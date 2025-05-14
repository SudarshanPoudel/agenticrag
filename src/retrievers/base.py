from abc import ABC, abstractmethod

from ..utils.logging_config import setup_logger
logger = setup_logger(__name__)

class BaseRetriever(ABC):
    """
    Abstract base class for any kind of data retrievers.
    """
    def __init__(self):
        pass


    @property
    @abstractmethod
    def name() -> str:
        "Return Name of the retriever"
        pass
    
    @property
    @abstractmethod
    def description() -> str:
        "Return detailed description of retriever, what it does and what it expects as input and it's output"
        pass

    @property
    @abstractmethod
    def data_store():
        "Return Store type that This retriever works on"
        pass

    @abstractmethod
    async def retrieve(self, *args, **kwargs) -> str:
        """Retrieves data according to given task string"""
        pass