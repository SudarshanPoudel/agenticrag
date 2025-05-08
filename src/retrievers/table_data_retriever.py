import logging
import time
from src.datastores.sqlstores import metastore
from src.datastores.sqlstores.metastore import MetaStore
from src.datastores.sqlstores.table_store import TableStore
from src.utils.local_sandbox_executor import LocalPythonExecutor
from .base import BaseRetriever

from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from google.api_core.exceptions import ResourceExhausted

from src.utils.llm import DEFAULT_LLM
from src.utils.prompts import DATA_RETRIEVER_SYSTEM_PROMPT
from src.utils.helpers import parse_code_blobs

class TableDataRetriever(BaseRetriever):
    def __init__(self, llm=DEFAULT_LLM):
        self.llm = llm

    @property
    def name(self):
        return 'table_data_retriever'
    
    @property
    def description(self):
        return "This retriever requires a user query and csv file path. It then extracts relevant data from the csv file to solve user query and saves as `retrieved_data/table_data.csv` using pandas. It can extract particular row, column or even perform aggregation, grouping etc. on tabular data."

    @property
    def data_store(self):
        return TableStore()

    def retrieve(self, query: str, data_name: str):
        executor = LocalPythonExecutor(
            additional_authorized_imports=["pandas", "matplotlib"]
        )
        max_retries = 10
        table = self.data_store.fetch(name=data_name)[0]
        # print(table)
        structure = table.summary

        base_messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(DATA_RETRIEVER_SYSTEM_PROMPT),
                HumanMessagePromptTemplate.from_template("Query: {query}\n File Path: {file_path}\n Output Path: {output_path}\n Structure: {structure}")
            ]
        ).format_messages(query=query, file_path=table.path, output_path="retrieved_data/table_data.csv", structure=structure)

        messages = base_messages.copy()

        for _ in range(max_retries):
            llm_resp = self.llm.invoke(messages).content

            try:
                code = parse_code_blobs(llm_resp)
            except ValueError as e:
                messages.append(HumanMessage(content=f"Error occurred while parsing code: {e}"))
                continue

            try:
                executor(code)
            except Exception as e:
                messages.append(HumanMessage(content=f"Error during code execution: {e}"))
                continue

            return "Relevant table saved at `retrieved_data/table_data.csv`"

        return "Failed to retrieve table after multiple attempts."