from dataclasses import dataclass, field
from pydantic import BaseModel, ConfigDict, model_validator
from typing import Union, Optional
from numpy.typing import NDArray
import numpy as np
from enum import Enum


Vector = NDArray[Union[np.int32, np.float32]]  

class DataFormat(str, Enum):
    TEXT = "text"
    TABLE = "table"
    EXTERNAL_DB = "external_db"

class BaseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class VectorData(BaseData):
    id: str
    name: str
    text: str

class TextData(VectorData):
    pass

class TableData(BaseData):
    id: Optional[int] = None
    name: str
    path: str
    structure_summary: str

class MetaData(BaseData):
    id: Optional[int] = None
    format: DataFormat
    name: str
    description: str
    source: str = "unknown"

class ExternalDBData(BaseData):
    id: Optional[int] = None
    name: str
    db_structure: str
    connection_url: Optional[str] = None
    connection_url_env_var: Optional[str] = None

    @model_validator(mode="after")
    def validate_connection_info(self) -> "ExternalDBData":
        if not self.connection_url and not self.connection_url_env_var:
            raise ValueError("Either 'connection_url' or 'connection_url_env_var' must be provided.")
        return self

@dataclass
class RAGAgentResponse:
    success: bool
    content: str
    iterations: Optional[int] = None
    datasets: list = field(default_factory=list)
    retrievers: list = field(default_factory=list)
    tasks: list = field(default_factory=list)