from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain.tools import StructuredTool

from src.retrievers import VectorRetriever
from src.tasks import QATask
from src.utils.llm import DEFAULT_LLM
from src.utils.generate_args_schema import generate_args_schema_from_method
from src.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class ControllerAgent:
    def __init__(self):
        pass

    def invoke(self, query):
        
        task = self._select_task(query=query)
        logger.info(f"Task classified as: {task.name}")

        dataset_info = self._select_relevant_data(query=query)
        logger.info(f"Relevant datasets selected : {dataset_info}")

        retriever = self._select_retriever(query=query)
        logger.info(f"Retriever selected: {retriever.name}")

        retriever_tool = StructuredTool.from_function(
            func=retriever.retrieve,
            name=retriever.name,
            description=retriever.description,
            args_schema=generate_args_schema_from_method(retriever.retrieve)
        )
        task_tool = StructuredTool.from_function(
            func=task.execute,
            name=task.name,
            description=task.description,
            args_schema=generate_args_schema_from_method(task.execute)
        )
        tools = [task_tool, retriever_tool]
        checkpointer = MemorySaver()
        app = create_react_agent(
            DEFAULT_LLM, 
            tools, 
            checkpointer=checkpointer, 
        )
        
        final_state = app.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"thread_id": 42}}
        )
        response = final_state["messages"][-1].content
        logger.info(f"Response obtained as : {response}")
        return response

        
    def _select_task(self, query):
        return QATask()


    def _select_relevant_data(self, query):
        return "Text Data"

    def _select_retriever(self, query):
        return VectorRetriever()

