from typing import Callable, Literal, List, Union
from agenticrag.core.storage_manager import StorageManager
from agenticrag.stores.backends.chroma_backend import ChromaBackend
from agenticrag.types.core import TextData, Vector


class ChromaTextStore(ChromaBackend[TextData]):
    """
    A specialized vector-based store for text data using ChromaDB.
    """

    def __init__(
        storage_manager: Union[StorageManager, str] = ".agenticrag_data",
        embedding_function: Union[Literal['default'], Callable[[str], Vector]] = 'default',
        collection_name: str = "vector_store_chroma",
        distance_metric: str = Literal["cosine", "dot_product", "euclidean"],
    ):
        super().__init__(
            schema=TextData,
            storage_manager=storage_manager,
            embedding_function=embedding_function,
            collection_name=collection_name,
            distance_metric=distance_metric
        )
