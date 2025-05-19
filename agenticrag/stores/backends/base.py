from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from agenticrag.types.core import BaseData

T = TypeVar("T", bound=BaseData)


class BaseBackend(ABC, Generic[T]):
    @abstractmethod
    def add(self, data: T) -> None:
        """Add a data object of type T to the store."""
        pass

    @abstractmethod
    def get(self, id: str) -> Optional[T]:
        """Get a single data object by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Retrieve all stored data objects."""
        pass

    @abstractmethod
    def update(self, id: str, data: T) -> None:
        """Update a data object by ID."""
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete a data object by ID."""
        pass

    @abstractmethod
    def index(self, data: T) -> List[T]:
        """Index or search entries by non-null fields of the data object."""
        pass


class BaseVectorBackend(BaseBackend[T], ABC):
    @abstractmethod
    def search_similar(self, text_query: str, document_name: str, top_k: int) -> List[T]:
        """Return top-k similar entries based on a text query."""
        pass
