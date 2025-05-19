from typing import Callable, Literal, List, Union
from agenticrag.stores.backends.chroma_backend import ChromaBackend
from agenticrag.types.core import TextData


class TextStore(ChromaBackend[TextData]):
    """
    A specialized vector-based store for text data using ChromaDB.
    """

    def __init__(self, persistent_dir: str = ".agenticrag_data", embedding_function: Union[Literal['default'], Callable[[str], List[float]]] = 'default'):
        super().__init__(schema=TextData, persistent_dir=persistent_dir, embedding_function=embedding_function)
