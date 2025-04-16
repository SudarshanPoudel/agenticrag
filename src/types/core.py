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
    type: Literal["text", "table"]
    name: str
    description: str