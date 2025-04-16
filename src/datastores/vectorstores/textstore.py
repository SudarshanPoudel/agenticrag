from chromadb import Client
from chromadb.config import Settings
from typing import Union, Callable, Literal, List, Any, Dict
from sentence_transformers import SentenceTransformer
from ...types.core import TextData
from ..utils.markdown_splitter import MarkdownSplitter
from ...utils.logging_config import setup_logger

logger = setup_logger(__name__)

class TextStore:
    def __init__(
        self,
        collection_name: str = "text_store",
        embedding_function: Union[Literal['default'], Callable[[str], List[float]]] = 'default',
    ):
        self.chroma_client = Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=".chroma"))
        self.collection = self.chroma_client.get_or_create_collection(collection_name)

        if embedding_function == 'default':
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_function = lambda x: self.embedding_model.encode([x])[0]
        else:
            self.embedding_function = embedding_function

    def store(self, data: TextData) -> None:
        splitter = MarkdownSplitter(max_length=2000)
        text_chunks = splitter.split(data=data.text)

        for i, chunk in enumerate(text_chunks):
            self.collection.add(
                documents=[chunk],
                embeddings=[self.embedding_function(chunk)],
                metadatas=[{
                    "source": data.source,
                    "name": data.name
                }],
                ids=[f"{data.name}_{i}"]
            )
        logger.info(f"{len(text_chunks)} text chunks of '{data.name}' stored in vector DB")

    def knn_search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        embedding = self.embedding_function(query_text)
        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        return results
