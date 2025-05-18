from sqlalchemy import Column, Integer, String
from agentic_rag.stores.backends.sql_backend import Base

from agentic_rag.types.schemas import MetaData
from agentic_rag.stores.backends.sql_backend import SQLBackend

class MetaDataModel(Base):
    __tablename__ = "meta_data"

    id = Column(Integer, primary_key=True, index=True)
    format = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    source = Column(String, nullable=False)



class MetaStore(SQLBackend[MetaDataModel, MetaData]):
    """
    A specialized store to store metadata of various data.
    """
    def __init__(self, connection_url = "sqlite:///sqlite.db"):
        super().__init__(MetaDataModel, MetaData, connection_url)
        
