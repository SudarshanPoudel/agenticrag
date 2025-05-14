from os import name
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session
from sqlmodel import SQLModel, Field
from typing import Optional
from ...types.core import DBInfoData
from ..base import BaseDataStore
from .base_sql_store import BaseSQLStore
from ...utils.logging_config import setup_logger
import re

logger = setup_logger(__name__)

class DBInfoDataModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    db_structure: str
    connection_url: Optional[str] = None
    connection_url_env_var: Optional[str] = None
    summary: Optional[str] = None

class DBInfoStore(BaseDataStore,BaseSQLStore):
    @property
    def source_data_type(self):
        return "database_data"
    
    def get_model(self):
        return DBInfoDataModel

    def store(self, data: DBInfoData) -> None:
        model = DBInfoDataModel(
            db_structure=data.db_structure,
            connection_url=data.connection_url,
            connection_url_env_var=data.connection_url_env_var, 
            name=data.name, 
            summary=data.summary
        )
        self.add(model)
        logger.info("Database info added to db_info_store")

    def run_read_query(self, query: str, db_name: str) -> list[dict]:
        # Basic check to prevent non-SELECT queries
        query_clean = query.strip().lower()
        if not query_clean.startswith("select"):
            raise ValueError("Only SELECT queries are allowed")

        if re.search(r"\b(update|delete|insert|drop|alter|truncate)\b", query_clean):
            raise ValueError("Query contains forbidden operation")

        # Use the provided db_url or the store's default session
        db_metadata = self.fetch(name=db_name)[0]
        connection_url = db_metadata.connection_url

        if not connection_url:
            connection_url_env_var = db_metadata.connection_url_env_var
            if not connection_url_env_var:
                raise ValueError("No connection URL or environment variable provided.")
            connection_url = os.getenv(connection_url_env_var)

        engine = self._create_engine(connection_url)

        try:
            with Session(engine) as session:
                result = session.exec(text(query))
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
        except SQLAlchemyError as e:
            raise RuntimeError("Failed to execute query") from e

    def _create_engine(self, db_url: str):
        from sqlmodel import create_engine
        return create_engine(db_url, echo=False)
