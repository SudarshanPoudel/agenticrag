from dataclasses import dataclass, field
from typing import Optional, List, Literal

@dataclass
class TextData:
    name: str
    description: str
    text: str
    source: str


@dataclass
class TableData:
    name:str
    description:str
    summary: str
    path:str
    source:str

@dataclass
class MetaData:
    type: Literal["text", "table", "database"]
    name: str
    description: str

@dataclass
class DBInfoData:
    name: str
    db_structure: str
    summary: str
    connection_url: Optional[str] = None
    connection_url_env_var: Optional[str] = None