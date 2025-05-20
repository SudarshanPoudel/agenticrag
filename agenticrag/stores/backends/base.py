from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar, Union

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


class BaseVectorBackend(BaseBackend[T], ABC):
    @abstractmethod
    def search_similar(self, text_query: str, document_name: str, top_k: int) -> List[T]:
        """Return top-k similar entries based on a text query."""
        pass
