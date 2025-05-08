from abc import ABC, abstractmethod
from typing import Any, Union

class BaseDataStore(ABC):
    @property
    @abstractmethod
    def source_data_type(self) -> str:
        ...