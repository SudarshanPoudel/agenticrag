from sqlalchemy import Column, Integer, String
from agenticrag.stores.backends.sql_backend import Base

from agenticrag.types.core import TableData
from agenticrag.stores.backends.sql_backend import SQLBackend


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
    def __init__(self, connection_url = "sqlite:///.agenticrag_data/agenticrag.db"):
        super().__init__(TableDataModel, TableData, connection_url)

