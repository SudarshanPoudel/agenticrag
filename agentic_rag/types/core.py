from dataclasses import dataclass
from typing import Union, Optional
from numpy.typing import NDArray
import numpy as np
from enum import Enum

Vector = NDArray[Union[np.int32, np.float32]]  

class DataFormat(str, Enum):
    TEXT = "text"
    TABLE = "table"
    EXTERNAL_DB = "external_db"


@dataclass
class RAGAgentResponse:
    success: bool
    content: str
    tries: Optional[int] = None
    datasets: list[str] = []
    retrievers: list[str] = []
    tasks: list[str] = []