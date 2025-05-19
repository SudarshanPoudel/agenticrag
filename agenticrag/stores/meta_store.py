from sqlalchemy import Column, Integer, String
from agenticrag.stores.backends.sql_backend import Base

from agenticrag.types.core import MetaData
from agenticrag.stores.backends.sql_backend import SQLBackend
from agenticrag.types.exceptions import StoreError

class MetaDataModel(Base):
    __tablename__ = "meta_data"

    id = Column(Integer, primary_key=True, index=True)
    format = Column(String, nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    source = Column(String, nullable=False)


class MetaStore(SQLBackend[MetaDataModel, MetaData]):
    """
    A specialized store to store metadata of various data.
    """
    def __init__(self, connection_url = "sqlite:///.agenticrag_data/agenticrag.db"):
        super().__init__(MetaDataModel, MetaData, connection_url)
        
    def add(self, data: MetaData) -> MetaData:
        if_already_existing = self.index(name=data.name)
        if if_already_existing:
            raise StoreError("Data with same name already exists, can't have 2 entries with same name")
        else:
            return super().add(data)