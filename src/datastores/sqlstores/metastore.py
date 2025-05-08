from sqlmodel import SQLModel, Field
from typing import Optional

from ..base import BaseDataStore
from .base_sql_store import BaseSQLStore
from ...types.core import MetaData

class MetaDataModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    data_type: str
    name: str
    description: str

class MetaStore(BaseDataStore, BaseSQLStore):
    @property
    def source_data_type(self):
        return "meta_data"
    
    def get_model(self):
        return MetaDataModel

    def store(self, data:MetaData) -> None:
        model = MetaDataModel(data_type=data.type, name=data.name, description=data.description)
        self.add(model)
