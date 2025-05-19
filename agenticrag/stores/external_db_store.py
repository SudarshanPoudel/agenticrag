from sqlalchemy import Column, Integer, String
from agenticrag.stores.backends.sql_backend import Base

from agenticrag.types.core import ExternalDBData
from agenticrag.stores.backends.sql_backend import SQLBackend


class ExternalDBDataModel(Base):
    __tablename__ = "external_db_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    connection_url = Column(String, nullable=True)
    connection_url_env_var = Column(String, nullable=True)
    db_structure = Column(String, nullable=False)


class ExternalDBStore(SQLBackend[ExternalDBDataModel, ExternalDBData]):
    """
    A specialized store to store information of external databases connected to RAG Agent.
    """
    def __init__(self, connection_url = "sqlite:///.agenticrag_data/agenticrag.db"):
        super().__init__(ExternalDBDataModel, ExternalDBData, connection_url)
