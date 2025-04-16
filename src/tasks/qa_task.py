from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage

from .base import BaseTask
from ..utils.llm import DEFAULT_LLM
from ..utils.logging_config import setup_logger
from .utils.task_prompts import QA_PROMPT

logger = setup_logger(__name__)

class QATask(BaseTask):
    def __init__(self):
        pass

    @property
    def name(self):
        return "question_answering"
    
    @property
    def description(self):
        return "This task requires Query as input, it then looks into retrieved_data/text_data.txt and answers user's query"
    
    def execute(self, query:str, **kwargs) -> str:
        with open('retrieved_data/text_data.txt', 'r') as f:
            context = f.read()
        system_message = SystemMessage(QA_PROMPT)
        
        # Construct messages using 'stuff' method
        messages = [
            system_message,
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {query}")
        ]
        
        # Get the response from the model
        response = DEFAULT_LLM.invoke(messages)
        
        return response.content

