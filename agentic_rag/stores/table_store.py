from sqlalchemy import Column, Integer, String
from agentic_rag.stores.backends.sql_backend import Base

from agentic_rag.types.schemas import TableData
from agentic_rag.stores.backends.sql_backend import SQLBackend


class TableDataModel(Base):
    __tablename__ = "table_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    structure_summary = Column(String, nullable=False)


class TableStore(SQLBackend[TableDataModel, TableData]):
    """
    A specialized sql-based store for tabular data.
    """
    def __init__(self, connection_url = "sqlite:///sqlite.db"):
        super().__init__(TableDataModel, TableData, connection_url)

