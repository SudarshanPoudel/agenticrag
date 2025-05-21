from abc import ABC
from typing import Type, TypeVar, Generic, Union, Callable, Literal, List, Optional
from agenticrag.types.core import Vector
from agenticrag.types.core import VectorData
from agenticrag.utils.logging_config import setup_logger
from agenticrag.stores.backends.base import BaseVectorBackend
from agenticrag.types.exceptions import StoreError

logger = setup_logger(__name__)

SchemaType = TypeVar("SchemaType", bound=VectorData)

class ChromaBackend(BaseVectorBackend[SchemaType], ABC, Generic[SchemaType]):
    def __init__(
        self,
        schema: Type[SchemaType],
        persistent_dir: str = ".chroma",
        embedding_function: Union[Literal['default'], Callable[[str], Vector]] = 'default',
    ):
                
        try:
            from chromadb import PersistentClient
        except ImportError:
            raise ImportError("ChromaDB is not installed. Please install it with `pip install chromadb`.")
        self.schema = schema
        try:
            logger.info(f"Initializing ChromaDB client at {persistent_dir}")
            self.chroma_client = PersistentClient(path=persistent_dir)
            self.collection = self.chroma_client.get_or_create_collection(name="vector_store_chroma")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma client: {e}")
            raise StoreError("ChromaDB initialization failed.") from e

        if embedding_function == 'default':
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError("SentenceTransformers is not installed, either use own embedding function or install it via `pip install sentence_transformers`.")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_function = lambda x: self.embedding_model.encode(x)
        else:
            self.embedding_function = embedding_function

    def add(self, data: SchemaType) -> None:
        try:
            embedding = self.embedding_function(data.text)
            metadata = {k: v for k, v in data.model_dump().items() if k not in {'id', 'text'}}
            self.collection.add(
                documents=[data.text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[str(data.id)],
            )
            logger.info(f"Added data with id: {data.id}")
        except Exception as e:
            logger.error(f"Failed to add data id={data.id}: {e}")
            raise StoreError("Add failed.") from e

    def get(self, id: str) -> Optional[SchemaType]:
        try:
            results = self.collection.get(ids=[id])
            if not results["documents"]:
                return None
            text = results["documents"][0]
            meta = results["metadatas"][0]
            return self.schema(**{"id": id, "text": text, **meta})
        except Exception as e:
            logger.error(f"Failed to get data id={id}: {e}")
            raise StoreError("Get failed.") from e

    def get_all(self) -> List[SchemaType]:
        try:
            results = self.collection.get()
            return [
                self.schema(**{"id": rid, "text": doc, **meta})
                for rid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"])
            ]
        except Exception as e:
            logger.error("Failed to get all data: {e}")
            raise StoreError("Get all failed.") from e

    def update(self, id: str, **kwargs) -> None:
        try:
            text = kwargs.get("text", None)
            embedding = self.embedding_function(text) if text else None
            metadata = {k: v for k, v in kwargs.items() if k not in {'id', 'text'}}
            self.collection.update(
                documents=[text] if text else None,
                embeddings=[embedding] if embedding else None,
                metadatas=[metadata],
                ids=[id],
            )
            logger.info(f"Updated data with id: {id}")
        except Exception as e:
            logger.error(f"Failed to update data id={id}: {e}")
            raise StoreError("Update failed.") from e

    def delete(self, id: str) -> None:
        try:
            self.collection.delete(ids=[id])
            logger.info(f"Deleted data with id: {id}")
        except Exception as e:
            logger.error(f"Failed to delete data id={id}: {e}")
            raise StoreError("Delete failed.") from e

    def index(self, **kwargs) -> List[SchemaType]:
        try:
            id = kwargs.pop("id", None)
            where_filter = {k: v for k, v in kwargs.items() if k not in {"id", "text"} and v is not None}
            if not where_filter:
                return []

            results = self.collection.get(ids=[id], where=where_filter)
            return [
                self.schema(**{"id": rid, "text": doc, **meta})
                for rid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"])
            ]
        except Exception as e:
            logger.error(f"Failed to index data: {e}")
            raise StoreError("Indexing failed.") from e

    def search_similar(self, text_query: str, document_name: str = None, top_k: int = 5) -> List[SchemaType]:
        try:
            embedding = self.embedding_function(text_query)
            where_filter = {"name": document_name} if document_name else None
            results = self.collection.query(query_embeddings=[embedding], where=where_filter, n_results=top_k)

            return [
                self.schema(**{"id": rid, "text": doc, **meta})
                for rid, doc, meta in zip(results["ids"][0], results["documents"][0], results["metadatas"][0])
            ]
        except Exception as e:
            logger.error(f"Search similar failed: {e}")
            raise StoreError("Search similar failed.") from e
