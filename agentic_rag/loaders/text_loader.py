from .base import BaseLoader
from langchain_core.language_models.chat_models import BaseChatModel

from agentic_rag.loaders.utils.description_generators import text_to_desc
from agentic_rag.loaders.utils.markdown_splitter import MarkdownSplitter
from agentic_rag.loaders.utils.scrape_web import scrape_web
from agentic_rag.stores import MetaStore
from agentic_rag.stores.backends.base import BaseVectorBackend
from agentic_rag.types.core import DataFormat
from agentic_rag.types.exceptions import LoaderError
from agentic_rag.types.schemas import MetaData, TextData
from agentic_rag.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class TextLoader(BaseLoader):
    """
    Loads and indexes text data from various sources into vector and metadata stores.
    """
    def __init__(
        self,
        text_store: BaseVectorBackend,
        meta_store: MetaStore,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        llm: BaseChatModel = None
    ):
        self.text_store = text_store
        self.meta_store = meta_store
        self.splitter = MarkdownSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.llm = llm

    def load_text(self, text: str, name: str, description: str = None, source: str = None) -> str:
        """
        Splits text into chunks and stores it in the vector store along with metadata.

        Args:
            text (str): Full document content.
            name (str): Name/identifier of the document.
            description (str, optional): Summary or auto-generated if not provided.
            source (str, optional): Source path/URL, defaults to name.
        """
        try:
            if not description:
                if not self.llm:
                    raise LoaderError("LLM not provided, cannot auto generate description.")
                description = text_to_desc(text, self.llm)
            if not source:
                source = name

            chunks = self.splitter.split(text)
            logger.debug(f"Splitting '{name}' into {len(chunks)} chunks.")

            for i, chunk in enumerate(chunks):
                chunk_id = f"{name}_{i}"
                data = TextData(id=chunk_id, name=name, text=chunk)
                self.text_store.add(data)
                logger.debug(f"Stored chunk {chunk_id}")

            metadata = MetaData(
                name=name,
                description=description,
                source=source,
                format=DataFormat.TEXT
            )
            self.meta_store.add(metadata)
            logger.debug(f"Metadata stored for '{name}'")
            logger.info(f"Loaded text for '{name}'")
            return name

        except Exception as e:
            logger.error(f"Failed to load text for '{name}': {e}")
            raise

    def load_web(self, url: str, name: str = None, description: str = None) -> str:
        """
        Scrapes content from a URL and loads it into the store.

        Args:
            url (str): Web page URL to scrape.
            name (str, optional): Document name override.
            description (str, optional): Optional metadata description.
        """
        try:
            web_data = scrape_web(url)
            if not name:
                name = web_data.get("site_name", "web_doc")
            logger.info(f"Scraped content from '{url}' with document name: {name}")
            return self.load_text(
                text=web_data.get("markdown", ""),
                name=name,
                description=description,
                source=url
            )
        except Exception as e:
            logger.error(f"Failed to load from web '{url}': {e}")
            raise
