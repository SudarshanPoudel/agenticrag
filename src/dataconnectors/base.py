from abc import ABC, abstractmethod
from typing import Any, Union

from ..datastores.sqlstores.base_sql_store import BaseSQLStore
from ..datastores.sqlstores.metastore import MetaStore

class BaseDataConnector(ABC):
    """
    Abstract base class for any kind of data loaders.
    Data loaders takes certain input and store the data in data stores. 
    """
    @property
    def meta_store(self):
        return MetaStore()

    @property
    @abstractmethod
    def data_store(self) -> BaseSQLStore:
        ...