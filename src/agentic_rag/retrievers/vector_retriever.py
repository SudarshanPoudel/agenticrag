from agentic_rag.retrievers.base import BaseRetriever
from agentic_rag.stores import TextStore
from agentic_rag.utils.logging_config import setup_logger
from agentic_rag.types.core import DataFormat

logger = setup_logger(__name__)

class VectorRetriever(BaseRetriever):
    def __init__(self, store: TextStore, persistent_dir: str = ".", top_k: int = 5):
        self.store = store
        self.persistent_dir = persistent_dir
        self.top_k = top_k

    @property
    def name(self):
        return 'vector_search_retriever'
    
    @property
    def description(self):
        return (
            f"This retriever requires a user query in the input and retrieves relevant text chunks by "
            f"doing vector search from database. It then saves those chunks in "
            f"`{self.persistent_dir}/retrieved_data/text_data.txt`."
        )
    
    @property
    def working_data_format(self):
        return DataFormat.TEXT

    def retrieve(self, query: str, document_name: str) -> str:
        """
        Retrieve relevant text chunks based on user query.
        """
        chunks = self.store.knn_search(query_text=query, document_name=document_name, top_k=self.top_k)
        if chunks:
            logger.debug(f"{len(chunks)} text chunks relevant to query `{query}` retrieved by vector retriever")
            text = "\n\n---\n\n".join(c.text for c in chunks)
            output_path = f"{self.persistent_dir}/retrieved_data/text_data.txt"
            with open(output_path, 'w') as f:
                f.write(text)
            return f"Relevant text content saved at `{output_path}`"
        else:
            logger.debug(f"No chunks relevant to `{query}` found by vector retriever")
            return "Unable to retrieve any relevant text"
