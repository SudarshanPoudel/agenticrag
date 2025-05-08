from langchain.prompts import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage
import time
from src.dataloaders.utils.csv_summary import summarize_csv
from src.datastores.sqlstores import metastore
from src.datastores.sqlstores.metastore import MetaStore
from src.datastores.sqlstores.table_store import TableStore
from src.utils.local_sandbox_executor import LocalPythonExecutor

from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from google.api_core.exceptions import ResourceExhausted

from src.utils.llm import DEFAULT_LLM
from src.utils.prompts import CHART_GENERATION_PROMPT, DATA_RETRIEVER_SYSTEM_PROMPT
from src.utils.helpers import parse_code_blobs
from .base import BaseTask
from .utils.task_prompts import QA_PROMPT
from ..utils.llm import DEFAULT_LLM
from ..utils.logging_config import setup_logger


logger = setup_logger(__name__)

class ChartGenerationTask(BaseTask):
    def __init__(self):
        self.llm = DEFAULT_LLM

    @property
    def name(self):
        return "chart_generation"
    
    @property
    def description(self):
        return "This task requires csv file path as source data and a query to make chart, it then generates chart and return file path of the chart"
    
    def execute(self, file_path:str, query:str) -> str:
        executor = LocalPythonExecutor(
                additional_authorized_imports=["pandas", "seaborn", "matplotlib"]
            )   
        max_retries = 10
        structure = summarize_csv(file_path, use_llm=False)

        base_messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(CHART_GENERATION_PROMPT),
                HumanMessagePromptTemplate.from_template("Query: {query}\n File Path: {file_path}\n Output Folder: {output_path} \n File Structure: {structure}")
            ]
        ).format_messages(query=query, file_path=file_path, output_path="charts/", structure=structure)

        messages = base_messages.copy()
        for _ in range(max_retries):
            llm_resp = self.llm.invoke(messages).content
            try:
                code = parse_code_blobs(llm_resp)
            except ValueError as e:
                messages.append(HumanMessage(content=f"Error occurred while parsing code: {e}"))
                continue

            try:
                result = executor(code)
            except Exception as e:
                messages.append(HumanMessage(content=f"Error during code execution: {e}"))
                continue

            return f"Relevant chart saved at {result}"

        return "Failed to retrieve table after multiple attempts"