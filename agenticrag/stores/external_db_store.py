from sqlalchemy import Column, Integer, String
from agenticrag.stores.backends.sql_backend import Base

from agenticrag.types.core import ExternalDBData
from agenticrag.stores.backends.sql_backend import SQLBackend


def make_external_db_model(table_name: str):
    class ExternalDBDataModel(Base):
        __tablename__ = table_name
        id = Column(Integer, primary_key=True, index=True)
        name = Column(String, nullable=False)
        connection_url = Column(String, nullable=True)
        connection_url_env_var = Column(String, nullable=True)
        db_structure = Column(String, nullable=False)

    return ExternalDBDataModel


class ExternalDBStore(SQLBackend[ExternalDBData]):
    """
    A specialized store to store information of external databases connected to RAG Agent.
    """
    def __init__(self, connection_url = "sqlite:///.agenticrag_data/agenticrag.db", table_name = "external_db_data"):
        model = make_external_db_model(table_name)
        super().__init__(model, ExternalDBData, connection_url)
