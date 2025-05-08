from .base import BaseRetriever
from ..datastores.vectorstores.textstore import TextStore
from ..utils.llm import DEFAULT_LLM
from ..utils.logging_config import setup_logger

logger = setup_logger(__name__)

class VectorRetriever(BaseRetriever):
    def __init__(self):
        pass

    @property
    def name(self):
        return 'vector_search_retriever'
    
    @property
    def description(self):
        desc = """This retriever requires a user query in the input and retrieves relevant text chunks by doing vector search from database. It then saves those chunks in `retrieved_data/text_data.txt`."""
        return desc
    
    @property
    def data_store(self):
        return TextStore()


    def retrieve(self, query:str)->str:
        """
        Args:
            query: Query to search relevant text.
        """
        chunks = self.data_store.knn_search(query_text=query)
        if len(chunks) > 0:
            logger.debug(f"{len(chunks)} Text chunks, relevant to query `{query}` retrieved by vector retriever")
            print(chunks['documents'])
            text = "\n\n---\n\n".join(chunks['documents'][0])
            with open('retrieved_data/text_data.txt', 'w') as f:
                f.write(text)

            return "Relevant text content saved at `retrieved_data/text_data.txt`"
        else:
            logger.debug(f"No chunks relevant to `{query}` found by vector retrieve")
            return "Unable to retrieve any relevant text"
            