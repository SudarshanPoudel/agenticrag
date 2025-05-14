import csv
import io
import json
import os
import re
import pandas as pd

from ..datastores.sqlstores.db_info_store import DBInfoStore
from .base import BaseRetriever
from ..utils.helpers import extract_json_blocks
from ..datastores.vectorstores.textstore import TextStore
from ..utils.prompts import TABLE_DECIDER_TEMPLATE, SQL_WRITING_TEMPLATE
from ..utils.llm import DEFAULT_LLM
from ..utils.logging_config import setup_logger

from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

logger = setup_logger(__name__)

class SQLRetriever(BaseRetriever):
    def __init__(self):
        self.llm = DEFAULT_LLM
        self.db = None

    @property
    def name(self):
        return 'sql_database_retriever'
    
    @property
    def description(self):
        desc = """This retriever requires a name of the linked database source and a query asking to extract particular data, it then retrieves data in table format and save in `retrieved_data/table_data.csv`."""
        return desc
    
    @property
    def data_store(self):
        return DBInfoStore()

    def retrieve(self, task:str, db_name: str):
        db_metadata = self.data_store.fetch(name=db_name)[0]

        db_structure = db_metadata.db_structure
        db_structure = json.loads(db_structure)
        data_source_info = self._extract_data_source_info(task=task, metadata=db_structure)        
        sql_llm_response = self._generate_and_execute_sql(task=task, db_name=db_name, table_and_fields_data=data_source_info['table_and_fields_data'])
        sql = sql_llm_response['sql']
        sql_explanation =sql_llm_response['explanation']
        sql_execution_data = sql_llm_response['data']
        
        if not sql_execution_data:
            return "No data retrieved."
        
        df = pd.DataFrame(sql_execution_data)
        df.to_csv("retrieved_data/table_data.csv", index=False)
        return "Retrieved data has been saved to `retrieved_data/table_data.csv`"
        

    def _extract_data_source_info(self, task:str, metadata:str) -> dict:
        all_tables = ", ".join(metadata.keys()) 
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(TABLE_DECIDER_TEMPLATE),
                HumanMessagePromptTemplate.from_template("Task: {task}\n Tables: [{tables}]")
            ]
        ).format_messages(task=task, tables=all_tables)
        llm_response = self.llm.invoke(prompt).content
        tables = extract_json_blocks(llm_response)["tables"]
        table_and_fields = []
        for table in tables:
            table_and_fields.append({"table_name": table, "fields": metadata[table]})
        return {
            "tables": tables,
            "table_and_fields_data": json.dumps(table_and_fields, indent=2)
        }


    def _generate_and_execute_sql(self, task: str, db_name: str, table_and_fields_data: str) :
        messages = ChatPromptTemplate.from_messages([
            SystemMessage(SQL_WRITING_TEMPLATE),
            HumanMessagePromptTemplate.from_template("Task: {task}\n Table and Fields Data: {table_and_fields_data}")
        ]).format_messages(task=task, table_and_fields_data=table_and_fields_data)
        max_retries = 1
        for _ in range(max_retries):
            llm_response = self.llm.invoke(messages)
            # print(messages)
            messages.append(llm_response)
            
            parsed_response = extract_json_blocks(content=llm_response.content)
            sql_query = parsed_response.get("sql")
            explanation = parsed_response.get("explanation")
            
            if not sql_query:
                return {
                    "sql": None,
                    "explanation": explanation,
                    "data": None
                }
            
            if not self._is_safe_sql(sql=sql_query):
                messages.append(HumanMessage(content="This is not a safe sql, You only have permission to read data with SELECT."))
                continue
            
            try:
                print(sql_query)
                result = self.data_store.run_read_query(query=sql_query, db_name=db_name)
                
                
                if not result:
                    messages.append(HumanMessage(content="No data retrieved."))
                    continue
                
                return {
                    "sql": sql_query,
                    "explanation": explanation,
                    "data": result
                }
            except Exception as e:
                error_message = f"ERROR OCCURRED WHILE EXECUTING SQL: {e}"
                print(error_message)
                messages.append(HumanMessage(content=error_message))
        
        return {
            "sql": None,
            "explanation": "Failed to extract required data after multiple attempts.",
            "data": None
        }

    def _is_safe_sql(self, sql:str)->bool:
        ALLOWED_SQL_PATTERN = re.compile(r"^\s*SELECT\s", re.IGNORECASE)
        FORBIDDEN_PATTERNS = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b", re.IGNORECASE)
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        for stmt in statements:
            if not ALLOWED_SQL_PATTERN.match(stmt): 
                return False
            if FORBIDDEN_PATTERNS.search(stmt): 
                return False
        return True