from sqlalchemy import Column, Integer, String
from agenticrag.stores.backends.sql_backend import Base

from agenticrag.types.core import TableData
from agenticrag.stores.backends.sql_backend import SQLBackend


def make_table_model(table_name: str):
    class TableDataModel(Base):
        __tablename__ = table_name

        id = Column(Integer, primary_key=True, index=True)
        name = Column(String, nullable=False)
        path = Column(String, nullable=False)
        structure_summary = Column(String, nullable=False)

    return TableDataModel


class TableStore(SQLBackend[TableData]):
    """
    A specialized sql-based store for tabular data.
    """
    def __init__(self, connection_url = "sqlite:///.agenticrag_data/agenticrag.db", table_name = "table_data"):
        model = make_table_model(table_name)
        super().__init__(model, TableData, connection_url)

