from sqlalchemy import Column, Integer, String
from agenticrag.stores.backends.sql_backend import Base

from agenticrag.types.core import MetaData
from agenticrag.stores.backends.sql_backend import SQLBackend
from agenticrag.types.exceptions import StoreError

def make_meta_model(table_name: str):
    class MetaDataModel(Base):
        __tablename__ = table_name

        id = Column(Integer, primary_key=True, index=True)
        format = Column(String, nullable=False)
        name = Column(String, unique=True, nullable=False)
        description = Column(String, nullable=False)
        source = Column(String, nullable=False)

    return MetaDataModel

class MetaStore(SQLBackend[MetaData]):
    """
    A specialized store to store metadata of various data.
    """
    def __init__(self, connection_url = "sqlite:///.agenticrag_data/agenticrag.db", table_name = "meta_data"):
        model = make_meta_model(table_name)
        super().__init__(model, MetaData, connection_url)
        
    def add(self, data: MetaData) -> MetaData:
        if_already_existing = self.index(name=data.name)
        if if_already_existing:
            raise StoreError("Data with same name already exists, can't have 2 entries with same name")
        else:
            return super().add(data)