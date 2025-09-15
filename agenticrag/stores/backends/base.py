from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Union, Literal

from agenticrag.types.core import BaseData

T = TypeVar("T", bound=BaseData)

class BaseBackend(ABC, Generic[T]):
    @abstractmethod
    def add(self, data: T) -> T:
        """Add a data object of type T to the store."""
        pass

    @abstractmethod
    def get(self, id: Union[int, str]) -> Optional[T]:
        """Get a single data object by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieve all stored data objects."""
        pass

    @abstractmethod
    def update(self, id: str, **kwargs) -> None:
        """Update a data object by ID."""
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete a data object by ID."""
        pass

    @abstractmethod
    def index(self, **filters) -> List[T]:
        """Index or search entries filters keys"""
        pass

    @abstractmethod
    def aget(self, id: Union[int, str]) -> Optional[T]:
        """Get a single data object by ID."""
        pass

    @abstractmethod
    async def aadd(self, data: T) -> T:
        """Add a data object of type T to the store."""
        pass

    @abstractmethod
    async def aget_all(self) -> List[T]:
        """Retrieve all stored data objects."""
        pass

    @abstractmethod
    async def aupdate(self, id: str, **kwargs) -> None:
        """Update a data object by ID."""
        pass

    @abstractmethod
    async def adelete(self, id: str) -> None:
        """Delete a data object by ID."""
        pass

    @abstractmethod
    async def aindex(self, **filters) -> List[T]:
        """Index or search entries filters keys"""
        pass


class BaseVectorBackend(BaseBackend[T], ABC):
    @abstractmethod
    def search_similar(self, text_query: str, top_k: int, document_name: Optional[str] = None, similarity_strategy: Optional[str] = None, **kwargs) -> List[T]:
        """Return top-k similar entries based on a text query."""
        pass

    @abstractmethod
    async def asearch_similar(self, text_query: str, top_k: int, document_name: Optional[str] = None, similarity_strategy: Optional[str] = None, **kwargs) -> List[T]:
        """Return top-k similar entries based on a text query."""
        pass
