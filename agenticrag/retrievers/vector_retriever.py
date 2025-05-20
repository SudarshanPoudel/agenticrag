import os
from agenticrag.retrievers.base import BaseRetriever
from agenticrag.stores import TextStore
from agenticrag.utils.logging_config import setup_logger
from agenticrag.types.core import DataFormat

logger = setup_logger(__name__)

class VectorRetriever(BaseRetriever):
    def __init__(self, store: TextStore = None, persistent_dir: str = ".agenticrag_data/retrieved_data", top_k: int = 5):
        self.store = store or TextStore()
        self.persistent_dir = persistent_dir
        os.mkdir(self.persistent_dir) if not os.path.exists(self.persistent_dir) else None
        self.top_k = top_k

    @property
    def name(self):
        return 'vector_search_retriever'
    
    @property
    def description(self):
        return (
            f"This retriever requires a user query in the input and retrieves relevant text chunks by "
            f"doing vector search from database. It then saves those chunks in "
            f"`{self.persistent_dir}/text_data.txt`."
        )
    
    @property
    def working_data_format(self):
        return DataFormat.TEXT

    def retrieve(self, query: str, document_name: str = None) -> str:
        """
        Retrieve relevant text chunks based on user query.
        """
        chunks = self.store.search_similar(text_query=query, document_name=document_name, top_k=self.top_k)
        if chunks:
            logger.debug(f"{len(chunks)} text chunks relevant to query `{query}` retrieved by vector retriever")
            text = "\n\n---\n\n".join(c.text for c in chunks)
            output_path = f"{self.persistent_dir}/text_data.txt"
            with open(output_path, 'w') as f:
                f.write(text)
            return f"Relevant text content saved at `{output_path}`"
        else:
            logger.debug(f"No chunks relevant to `{query}` found by vector retriever")
            return "Unable to retrieve any relevant text"
