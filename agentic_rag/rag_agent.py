from typing import List
import json
from langchain.tools import StructuredTool
from langchain_core.language_models.chat_models import BaseChatModel
from matplotlib import table


from agentic_rag.loaders import TableLoader, TextLoader
from agentic_rag.connectors import ExternalDBConnector
from agentic_rag.tasks import QuestionAnsweringTask, ChartGenerationTask, BaseTask
from agentic_rag.retrievers import BaseRetriever, VectorRetriever, TableDataRetriever, SQLRetriever
from agentic_rag.stores import BaseBackend, BaseVectorBackend, TextStore, TableStore, MetaStore, ExternalDBStore, meta_store
from agentic_rag.utils.generate_args_schema import generate_args_schema_from_method
from agentic_rag.utils.logging_config import setup_logger
from agentic_rag.types.exceptions import RAGAgentError

from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

from agentic_rag.utils.prompts import DATA_SOURCE_SELECTION_PROMPT, CONTROLLER_PROMPT, TASK_SELECTION_PROMPT
from agentic_rag.utils.helpers import extract_json_blocks, format_datasets, format_tool_metadata

logger = setup_logger(__name__)

class RAGAgent:
    def __init__(
        self,
        llm: BaseChatModel,
        persistent_dir: str = ".agentic_rag_data/",
        meta_store: MetaStore = None,
        tasks: List[BaseTask] = None,
        retrievers: List[BaseRetriever] = None,
    ):
        self.llm = llm
        if not tasks:
            tasks = [
                QuestionAnsweringTask(llm=llm),
                ChartGenerationTask(llm=llm)
            ]
        else:
            seen_type = set()
            for agent in tasks:
                if not isinstance(agent, BaseTask):
                    raise RAGAgentError(f"Task {agent} is not an instance of BaseTask")
                
                agent_type = type(agent)
                if agent_type in seen_type:
                    raise RAGAgentError(f"Duplicate agent type {agent_type} found.")
                seen_type.add(agent_type)

        self.tasks = tasks

        if not meta_store:
            meta_store = MetaStore(persistent_dir=persistent_dir)
        self.meta_store = meta_store
        self.text_store = None
        self.external_db_store = None
        self.table_store = None

        if not retrievers:
            self.text_store = TextStore(persistent_dir=persistent_dir)
            self.table_store = TableStore(persistent_dir=persistent_dir)
            self.meta_store = MetaStore(persistent_dir=persistent_dir)
            self.external_db_store = ExternalDBStore(persistent_dir=persistent_dir)
            retrievers = [
                VectorRetriever(store=self.text_store, persistent_dir=persistent_dir),
                TableDataRetriever(store=self.table_store, persistent_dir=persistent_dir),
                SQLRetriever(store=self.external_db_store, llm=llm, persistent_dir=persistent_dir)
            ]

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
                elif isinstance(retriever, TableDataRetriever):
                    self.table_store = retriever.store
                elif isinstance(retriever, SQLRetriever):
                    self.external_db_store = retriever.store

        self.retrievers = retrievers


    def invoke(self, query, max_retry=10):
        tasks = self._select_tasks(query=query)
        if not tasks:
            return "Unable to select task"
        logger.info(f"Tasks to perform: {[task.name for task in tasks]}")

        datasets = self._select_relevant_data(query=query)
        if not datasets:
            return "Unable to select dataset"
        logger.info(f"Relevant datasets selected: {[dataset.name for dataset in datasets]}")

        selected_retrievers = self._select_retrievers(datasets=datasets)
        if not selected_retrievers:
            return "Unable to select retriever"
        logger.info(f"Retriever selected: {[retriever.name for retriever in selected_retrievers]}")

        # Create tools
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

        # Create messages using classes instead of raw dicts
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

        for _ in range(max_retry):
            try:
                tool_call_msg = self.llm.invoke(messages)
                tool_call = extract_json_blocks(tool_call_msg.content)
            except Exception as e:
                logger.exception("Failed to parse tool call")
                error = f"Error parsing tool call: {e}"
                messages.append(tool_call_msg)
                messages.append(HumanMessage(name=tool_name, content=f"Error: {error}\n Original User query was : {query}"))
                continue

            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})

            if tool_name == "final_answer":
                answer = args.get("answer", "")
                logger.info(f"Final answer generated by controller: {answer}")
                return answer

            if tool_name not in tools_dict:
                logger.error(f"Unknown tool called: {tool_name}")
                tool_output = "Unknown tool called: {tool_name}"
            else:
                try:
                    tool_output = call_tool(tool_name, args)
                    logger.info(f"{tool_name} output: {tool_output}")
                except Exception as e:
                    logger.exception(f"{tool_name} tool execution failed")
                    tool_output = f"Error executing {tool_name} tool: {e}"
            messages.append(tool_call_msg)
            messages.append(HumanMessage(name=tool_name, content=f"Tool Output: {tool_output}\n Original User query was : {query}"))

        
    def _select_tasks(self, query):
        task_list = [
            {"name": task.name, "description": task.description} for task in self.tasks
        ]
        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(TASK_SELECTION_PROMPT),
                HumanMessagePromptTemplate.from_template("Query: {query}\n Tasks and Description:\n ```json\n{TastExecutionError}\n```")
            ]
        ).format_messages(query=query, task_list=task_list)
        llm_resp = self.llm.invoke(messages).content
        result = extract_json_blocks(llm_resp)
        relevant_tasks = []
        for task in self.tasks:
            for selected_task in result['tasks']:
                if task.name == selected_task:
                    relevant_tasks.append(task)
            
        return relevant_tasks
    

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
                HumanMessagePromptTemplate.from_template("Query: {query}\n Datasets and Description:\n ```json\n{data_list}\n```")
            ]
        ).format_messages(query=query, data_list=data_list)
        llm_resp = self.llm.invoke(messages).content
        result = extract_json_blocks(llm_resp)
        relevant_data_sources = []

        for data in all_data:
            for selected_data in result['data_sources']:
                if data.name == selected_data and data not in relevant_data_sources:
                    relevant_data_sources.append(data)
        return relevant_data_sources


    def _select_retrievers(self, datasets):
        selected_retrievers = []
        for retriever in self.retrievers:
            for dataset in datasets:
                if retriever.working_data_format == dataset.format:
                    selected_retrievers.append(retriever)
        return selected_retrievers
       


    # Load data directly
    def load_csv(self, file_path: str, name: str = None, description: str = None, source: str = None):
        if not self.table_store:
            raise RAGAgentError("Table store not initialized")
        table_loader = TableLoader(store=self.table_store, meta_store=self.meta_store, persistence_dir=self.persistence_dir+"/tables", llm=self.llm)
        table_loader.load_csv(file_path, name, description, source)

    def load_text(self, text: str, name: str, description: str = None, source: str = None):
        if not self.text_store:
            raise RAGAgentError("Text store not initialized")
        text_loader = TextLoader(store=self.text_store, meta_store=self.meta_store, llm=self.llm)
        text_loader.load_text(text, name, description, source)

    def load_web(self, url: str, name: str = None, description: str = None):
        if not self.text_store:
            raise RAGAgentError("Text store not initialized")
        text_loader = TextLoader(store=self.text_store, meta_store=self.meta_store, llm=self.llm)
        text_loader.load_web(url, name, description)

    def connect_db(self, name: str = "database", connection_url: str = None, connection_url_env_var: str = None, description: str = None):
        if not self.db_store:
            raise RAGAgentError("DB store not initialized")
        db_connector = ExternalDBConnector(store=self.db_store, meta_store=self.meta_store, llm=self.llm)
        db_connector.connect_db(name, connection_url, connection_url_env_var, description)