import json
import os
import re
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


try:
    import pandas as pd
except ImportError:
    raise ImportError("Pandas is required to use SQLRetriever, install it via `pip install pandas`")

from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from agenticrag.types.core import DataFormat
from agenticrag.types.core import ExternalDBData
from agenticrag.stores import ExternalDBStore
from agenticrag.types.exceptions import RetrievalError
from agenticrag.retrievers.base import BaseRetriever
from agenticrag.utils.helpers import extract_json_blocks
from agenticrag.retrievers.utils.prompts import TABLE_DECIDER_TEMPLATE, SQL_WRITING_TEMPLATE
from agenticrag.utils.logging_config import setup_logger
from agenticrag.utils.llm import get_default_llm

logger = setup_logger(__name__)


class SQLRetriever(BaseRetriever):
    """
    Retriever that queries external SQL databases using LLM-generated SQL queries.
    Saves retrieved data as CSV to a persistent folder.
    """

    def __init__(self,  store: ExternalDBStore = None, llm: BaseChatModel = None, persistent_dir: str = ".agenticrag_data/retrieved_data"):
        self.store = store or ExternalDBStore()
        self.llm = llm or get_default_llm()
        self.persistent_dir = persistent_dir
        os.mkdir(self.persistent_dir) if not os.path.exists(self.persistent_dir) else None

    @property
    def name(self) -> str:
        return "sql_database_retriever"

    @property
    def description(self) -> str:
        return (
            f"This retriever takes a database name and a query describing the desired data extraction, "
            f"generates an SQL query via an LLM, executes it on the linked database, "
            f"and saves the result as '{self.persistent_dir}/table_data.csv'."
            f" It can extract particular row, column or even perform aggregation, grouping etc. on database data."
            f"It is recommended to ask for a specif part with all required aggregations, grouping etc."
        )

    @property
    def working_data_format(self) -> DataFormat:
        return DataFormat.EXTERNAL_DB

    def retrieve(self, query: str, db_name: str) -> str:
        """
        Retrieve data from the specified database based on the query description.
        """
        try:
            db_entries = self.store.index(name=db_name)
            if not db_entries:
                return f"No database found with name '{db_name}'"
            db = db_entries[0]

            db_structure = json.loads(db.db_structure)
            data_source_info = self._extract_data_source_info(query=query, metadata=db_structure)
            sql_response = self._generate_and_execute_sql(
                query=query, db=db, table_and_fields_data=data_source_info["table_and_fields_data"]
            )
            sql_query = sql_response["sql"]
            explanation = sql_response["explanation"]
            logger.debug(f"Generated SQL query: {sql_query}, explanation: {explanation}")
            data = sql_response["data"]

            if not data:
                logger.info("No data retrieved from SQL query.")
                return "No data retrieved."

            df = pd.DataFrame(data)
            output_path = os.path.join(self.persistent_dir, "table_data.csv")
            df.to_csv(output_path, index=False)
            logger.info(f"Data saved to {output_path}")
            return f"Retrieved data has been saved to `{output_path}`"

        except Exception as e:
            logger.error(f"Error during data retrieval: {e}", exc_info=True)
            raise RetrievalError(f"Failed to retrieve data: {e}") from e

    def _extract_data_source_info(self, query: str, metadata: dict) -> dict:
        """
        Use LLM to select relevant tables and fields from database metadata for the query.
        """
        all_tables = ", ".join(metadata.keys())
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(TABLE_DECIDER_TEMPLATE),
                HumanMessagePromptTemplate.from_template("query: {query}\nTables: [{tables}]"),
            ]
        ).format_messages(query=query, tables=all_tables)

        llm_response = self.llm.invoke(prompt).content
        tables = extract_json_blocks(llm_response).get("tables", [])
        table_and_fields = [{"table_name": table, "fields": metadata.get(table, [])} for table in tables]
        logger.debug(f"Selected tables and fields: {table_and_fields}")
        return {"tables": tables, "table_and_fields_data": json.dumps(table_and_fields, indent=2)}

    def _generate_and_execute_sql(self, query: str, db: ExternalDBData, table_and_fields_data: str) -> dict:
        """
        Generate an SQL query using the LLM, check safety, execute it and return the results.
        Retries once if execution or generation fails.
        """
        messages = ChatPromptTemplate.from_messages(
            [
                SystemMessage(SQL_WRITING_TEMPLATE),
                HumanMessagePromptTemplate.from_template("query: {query}\nTable and Fields Data: {table_and_fields_data}"),
            ]
        ).format_messages(query=query, table_and_fields_data=table_and_fields_data)

        max_retries = 5
        for attempt in range(max_retries + 1):
            llm_response = self.llm.invoke(messages)
            messages.append(llm_response)

            parsed = extract_json_blocks(llm_response.content)
            sql_query = parsed.get("sql")
            explanation = parsed.get("explanation")

            if not sql_query:
                logger.debug(f"LLM did not produce a valid SQL query, explanation: {explanation}")
                return {"sql": None, "explanation": explanation, "data": None}

            if not self._is_safe_sql(sql_query):
                logger.debug("Unsafe SQL query detected; retrying.")
                messages.append(HumanMessage(content="This is not a safe SQL. You only have permission to read data with SELECT."))
                continue

            try:
                logger.debug(f"Executing SQL query: {sql_query}")
                results = self._run_query(sql_query, db)
                if not results:
                    logger.info("SQL query returned no data.")
                    messages.append(HumanMessage(content="No data retrieved."))
                    continue
                return {"sql": sql_query, "explanation": explanation, "data": results}

            except Exception as e:
                logger.error(f"SQL execution error: {e}", exc_info=True)
                messages.append(HumanMessage(content=f"Error executing SQL: {e}"))

        return {
            "sql": None,
            "explanation": "Failed to extract required data after multiple attempts.",
            "data": None,
        }

    def _is_safe_sql(self, sql: str) -> bool:
        """
        Basic safety check: only allow SELECT queries, disallow DML and DDL commands.
        """
        allowed_pattern = re.compile(r"^\s*SELECT\s", re.IGNORECASE)
        forbidden_pattern = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b", re.IGNORECASE)

        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        for stmt in statements:
            if not allowed_pattern.match(stmt) or forbidden_pattern.search(stmt):
                logger.debug(f"Unsafe SQL detected: {stmt}")
                return False
        return True

    def _run_query(self, query: str, db: ExternalDBData) -> list[dict]:
        connection_url = db.connection_url or os.getenv(db.connection_url_env_var or "")
        if not connection_url:
            raise ValueError("No valid connection URL or environment variable found for DB.")

        engine = self._create_engine(connection_url)
        SessionLocal = sessionmaker(bind=engine)

        try:
            with SessionLocal() as session:
                result = session.execute(text(query))
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in result.fetchall()]
                logger.debug(f"Query returned {len(data)} rows.")
                return data
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error during query execution: {e}", exc_info=True)
            raise RuntimeError("Failed to execute query") from e


    def _create_engine(self, db_url: str):
        return create_engine(db_url, echo=False)

