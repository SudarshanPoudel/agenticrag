from sqlmodel import SQLModel, Field
from typing import Optional
from ...types.core import TableData
from .base import BaseSQLStore
from ...utils.logging_config import setup_logger

logger = setup_logger(__name__)

class TableDataModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str
    name: str
    source: str
    summary: Optional[str] = None

class TableStore(BaseSQLStore):
    def get_model(self):
        return TableDataModel

    def store(self, data: TableData) -> None:
        model = TableDataModel(path=data.path, name=data.name, source=data.source, summary=data.summary)
        self.add(model)
        logger.info("Table added to table_store")