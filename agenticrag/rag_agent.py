import os
from typing import List
from langchain.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from agenticrag.tasks import QuestionAnsweringTask, BaseTask
from agenticrag.retrievers import BaseRetriever, VectorRetriever, TableRetriever, SQLRetriever
from agenticrag.stores import TextStore, MetaStore
from agenticrag.types.core import RAGAgentResponse
from agenticrag.utils.generate_args_schema import generate_args_schema_from_method
from agenticrag.utils.logging_config import setup_logger
from agenticrag.types.exceptions import RAGAgentError
from agenticrag.utils.prompts import DATA_SOURCE_SELECTION_PROMPT, CONTROLLER_PROMPT, TASK_SELECTION_PROMPT
from agenticrag.utils.helpers import extract_json_blocks, format_datasets, format_tool_metadata
from agenticrag.utils.rag_agent_loader_mixin import RAGAgentLoaderMixin
from agenticrag.utils.llm import get_default_llm

logger = setup_logger(__name__)

class RAGAgent(RAGAgentLoaderMixin):
    """
    A controller agent for managing data loading, retrieval, and task execution.
    Uses LLM to select tasks, datasets, and tools based on user queries.
    """
    def __init__(
        self,
        llm: BaseChatModel = None,
        persistent_dir: str = ".agenticrag_data",
        meta_store: MetaStore = None,
        tasks: List[BaseTask] = None,
        retrievers: List[BaseRetriever] = None,
    ):
        """
        Initializes the RAGAgent with LLM, storage directory, metadata store, tasks, and retrievers.
        Args:
            llm (BaseChatModel): The language model used for decision-making and tool selection, defaults to Gemini-2.0-flash.
            persistent_dir (str): Directory path to persist metadata and related data. Defaults to ".agentic_rag_data/".
            meta_store (MetaStore, optional): Store for managing dataset and retriever metadata, if not provided a new one will be created.
            tasks (List[BaseTask], optional): List of task tools the agent can use, if not provided default to Question Answering Task only.
            retrievers (List[BaseRetriever], optional): List of retrievers available to fetch context, if not provided default to VectorRetriever.
        """
        self.llm = llm or get_default_llm()
        self.persistence_dir = persistent_dir.rstrip("/")
        os.mkdir(self.persistence_dir) if not os.path.exists(self.persistence_dir) else None
        if not tasks:
            tasks = [QuestionAnsweringTask(llm=llm)]
        else:
            seen_type = set()
            for agent in tasks:
                if not isinstance(agent, BaseTask):
                    raise RAGAgentError(f"Task {agent} is not an instance of BaseTask")
                agent_type = type(agent)
                if agent_type in seen_type:
                    raise RAGAgentError(f"Duplicate agent type {agent_type} (name:{agent.name}) found.")
                seen_type.add(agent_type)
        self.tasks = tasks

        if not meta_store:
            meta_store = MetaStore(connection_url=f"sqlite:///{self.persistence_dir}/agenticrag.db")
        self.meta_store = meta_store
        self.text_store = None
        self.external_db_store = None
        self.table_store = None

        if not retrievers:
            self.text_store = TextStore(persistent_dir=persistent_dir)
            retrievers = [VectorRetriever(store=self.text_store, persistent_dir=persistent_dir + "/retrieved_data")]
        else:
            seen_types = set()
            for retriever in retrievers:
                if not isinstance(retriever, BaseRetriever):
                    raise RAGAgentError(f"Retriever {retriever} is not an instance of BaseRetriever")
                retriever_type = type(retriever)
                if retriever_type in seen_types:
                    raise RAGAgentError(f"Duplicate retriever type detected: {retriever_type.__name__} (name: {retriever.name})")
                seen_types.add(retriever_type)
                if isinstance(retriever, VectorRetriever):
                    self.text_store = retriever.store
                elif isinstance(retriever, TableRetriever):
                    self.table_store = retriever.store
                elif isinstance(retriever, SQLRetriever):
                    self.external_db_store = retriever.store
        self.retrievers = retrievers

    def invoke(self, query: str, max_iterations: int=10) -> RAGAgentResponse:
        """
        Main method to invoke rag agent, for given query it will:
        - select tasks to perform
        - select relevant datasets
        - select retrievers based on provided datasets
        - execute tasks and retrievers till task is completed ot max retry is exceeded.
        Note: max_iterations can't control how many times internal agents/tools (retrievers or tasks) use llm, to control behavior of those you must pass them in
        constructor with default behavior set.

        Args:
            query (str): The query to be processed by the agent.
            max_iterations (int, optional): The maximum number of iterations (retriever or task call) for the agent. Defaults to 10.
        """
        tasks = self._select_tasks(query=query)
        if not tasks:
            return RAGAgentResponse(
                success=False,
                content="I'm not capable of performing desired task asked in query."
            )
        logger.info(f"Tasks to perform: {[task.name for task in tasks]}")

        datasets = self._select_relevant_data(query=query)
        if not datasets:
            return RAGAgentResponse(
                success=False,
                content="Sorry! No dataset relevant to query found.",
                tasks=tasks
            )
        logger.info(f"Relevant datasets selected: {[dataset.name for dataset in datasets]}")

        selected_retrievers = self._select_retrievers(datasets=datasets)
        if not selected_retrievers:
            return RAGAgentResponse(
                success=False,
                content="Unable to select retriever for provided datasets.",
                tasks=tasks,
                datasets=datasets
            )
        logger.info(f"Retriever selected: {[retriever.name for retriever in selected_retrievers]}")

        tools_dict = {}
        for retriever in selected_retrievers:
            retriever_tool = StructuredTool.from_function(
                func=retriever.retrieve,
                name=retriever.name,
                description=f"Type: `retriever tool`\n{retriever.description}",
                args_schema=generate_args_schema_from_method(retriever.retrieve)
            )
            tools_dict[retriever.name] = retriever_tool

        for task in tasks:
            task_tool = StructuredTool.from_function(
                func=task.execute,
                name=task.name,
                description=f"Type: `agent tool`\n{task.description}",
                args_schema=generate_args_schema_from_method(task.execute)
            )
            tools_dict[task.name] = task_tool

        def call_tool(tool_name, args):
            logger.debug(f"Tool `{tool_name}` Called with args: {args}")
            return tools_dict[tool_name].invoke(args)

        def final_answer(answer: str):
            return answer

        tool_metadata = format_tool_metadata(tools_dict)
        dataset_metadata = format_datasets(datasets)

        messages = [
            SystemMessage(
                content=CONTROLLER_PROMPT + f"""
Available tools:
{tool_metadata}

Relevant datasets:
{dataset_metadata}
"""
            ),
            HumanMessage(content=query)
        ]

        for i in range(max_iterations):
            try:
                tool_call_msg = self.llm.invoke(messages)
                tool_call = extract_json_blocks(tool_call_msg.content)
            except Exception as e:
                logger.exception("Failed to parse tool call")
                error = f"Error parsing tool call: {e}"
                messages.append(tool_call_msg)
                messages.append(HumanMessage(name="error", content=f"Error: {error}\nOriginal User query: {query}"))
                continue

            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})

            if tool_name == "final_answer":
                answer = args.get("answer", "")
                logger.info(f"Final answer generated by controller: {answer}")
                return RAGAgentResponse(
                    success=True,
                    content=answer,
                    datasets=datasets,
                    tasks=tasks,
                    retrievers=selected_retrievers,
                    iterations=i
                )

            if tool_name not in tools_dict:
                logger.error(f"Unknown tool called: {tool_name}")
                tool_output = f"Unknown tool called: {tool_name}"
            else:
                try:
                    tool_output = call_tool(tool_name, args)
                    logger.info(f"{tool_name} output: {tool_output}")
                except Exception as e:
                    logger.exception(f"{tool_name} tool execution failed")
                    tool_output = f"Error executing {tool_name} tool: {e}"

            messages.append(tool_call_msg)
            messages.append(HumanMessage(name=tool_name, content=f"Tool Output: {tool_output}\nOriginal User query: {query}"))

    def _select_tasks(self, query):
        task_list = [{"name": task.name, "description": task.description} for task in self.tasks]
        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(TASK_SELECTION_PROMPT),
                HumanMessagePromptTemplate.from_template(
                    "Query: {query}\nTasks and Descriptions:\n```json\n{task_list}\n```"
                )
            ]
        ).format_messages(query=query, task_list=task_list)
        llm_resp = self.llm.invoke(messages).content
        result = extract_json_blocks(llm_resp)
        return [task for task in self.tasks if task.name in result.get('tasks', [])]

    def _select_relevant_data(self, query):
        all_data = self.meta_store.get_all()
        data_list = []
        seen = set()
        for data in all_data:
            item = (data.name, data.description)
            if item not in seen:
                seen.add(item)
                data_list.append({"name": data.name, "description": data.description})

        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(DATA_SOURCE_SELECTION_PROMPT),
                HumanMessagePromptTemplate.from_template(
                    "Query: {query}\nDatasets and Descriptions:\n```json\n{data_list}\n```"
                )
            ]
        ).format_messages(query=query, data_list=data_list)
        llm_resp = self.llm.invoke(messages).content
        result = extract_json_blocks(llm_resp)
        return [data for data in all_data if data.name in result.get('data_sources', [])]

    def _select_retrievers(self, datasets):
        selected = []
        for retriever in self.retrievers:
            for dataset in datasets:
                if retriever.working_data_format == dataset.format:
                    selected.append(retriever)
        return selected

