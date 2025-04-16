from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage

from .base import BaseTask
from .utils.task_prompts import QA_PROMPT
from ..utils.llm import DEFAULT_LLM
from ..utils.logging_config import setup_logger

from .utils.code_agent import DataQueryAgent
from ..datastores import TableStore

logger = setup_logger(__name__)

class TableQueryTask(BaseTask):
    def __init__(self):
        pass

    @property
    def name(self):
        return "table_data_question_answering"
    
    @property
    def description(self):
        return "This task requires Query as input, it then answers users query if it can be answered by using provided files"
    
    def execute(self, file_name:str, query:str, **kwargs) -> str:
       store = TableStore()
       values = store.fetch(name=file_name)
       agent = DataQueryAgent(
           file_path=values[0].path, 
           structure=values[0].summary,
           verbose=True
       )
       response = agent.ask(query=query)
       return response['answer']