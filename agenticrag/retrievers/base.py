from abc import ABC, abstractmethod

from agenticrag.types.core import DataFormat
from agenticrag.utils.logging_config import setup_logger

logger = setup_logger(__name__)

class BaseRetriever(ABC):
    """
    Abstract base class for retrievers that operate on specific data formats.
    """
    def __init__(self):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        "Returns Name of the retriever"
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        "Returns detailed description of retriever, what it does and what it expects as input and it's output"
        pass

    @property
    @abstractmethod
    def working_data_format() -> DataFormat:
        "Returns data format that retriever works with"
        pass


    @abstractmethod
    async def retrieve(self, *args, **kwargs) -> str:
        """Retrieves data according to given task string"""
        pass