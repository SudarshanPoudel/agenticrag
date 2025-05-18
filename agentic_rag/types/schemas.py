from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator
from agentic_rag.types.core import DataFormat

class BaseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class VectorData(BaseData):
    id: Optional[str] = None
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