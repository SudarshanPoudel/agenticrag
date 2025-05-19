from langchain_core.language_models.chat_models import BaseChatModel
import os

from agenticrag.utils.llm import get_default_llm

from .base import BaseLoader
from agenticrag.loaders.utils.description_generators import text_to_desc
from agenticrag.loaders.utils.markdown_splitter import MarkdownSplitter
from agenticrag.loaders.utils.scrape_web import scrape_web
from agenticrag.loaders.utils.parse_pdf import parse_pdf
from agenticrag.stores import MetaStore
from agenticrag.stores.backends.base import BaseVectorBackend
from agenticrag.types.core import DataFormat
from agenticrag.types.exceptions import LoaderError
from agenticrag.types.core import MetaData, TextData
from agenticrag.utils.logging_config import setup_logger

logger = setup_logger(__name__)


class TextLoader(BaseLoader):
    """
    Loads and indexes text data from various sources into vector and metadata stores.
    """
    def __init__(
        self,
        store: BaseVectorBackend,
        meta_store: MetaStore,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        llm: BaseChatModel = None
    ):
        self.store = store
        self.meta_store = meta_store
        self.splitter = MarkdownSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.llm = llm 

    def load_text(self, text: str, name: str, description: str = None, source: str = None) -> MetaData:
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
                    self.llm = get_default_llm()
                description = text_to_desc(text, self.llm)
            if not source:
                source = name

            chunks = self.splitter.split(text)
            logger.debug(f"Splitting '{name}' into {len(chunks)} chunks.")

            
            metadata = MetaData(
                name=name,
                description=description,
                source=source,
                format=DataFormat.TEXT
            )
            meta = self.meta_store.add(metadata)
            try:
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{name}_{i}"
                    data = TextData(id=chunk_id, name=name, text=chunk)
                    self.store.add(data)
                    logger.debug(f"Stored chunk {chunk_id}")
                logger.info(f"Text  loaded successfully with Meta_id: {meta.id}")
                return metadata
            except Exception as e:
                self.meta_store.delete(meta.id)
                raise e

        except Exception as e:
            logger.error(f"Failed to load text for '{name}': {e}")
            raise LoaderError(f"Failed to load text for '{name}': {e}")

    def load_web(self, url: str, name: str = None, description: str = None) -> str:
        """
        Scrapes content from a URL and loads it into the store.

        Args:
            url (str): Web page URL to scrape.
            name (str, optional): Document name default to webpage title.
            description (str, optional):  Description of what webpage is about, if not provided use LLM.
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

    def load_pdf(self, path:str, name: str = None, description: str = None) -> str:
        """
        Loads a PDF file content into the store.

        Args:
            path (str): Path to the PDF file.
            name (str, optional): Document name, default to file name.
            description (str, optional): Description of what PDF is about, if not provided use LLM.
        """
        try:
            pdf_content = parse_pdf(path)
            if not name:
                name = os.path.basename(path).split(".")[0]
            logger.info(f"Loaded content from '{path}' with document name: {name}")
            return self.load_text(
                text=pdf_content,
                name=name,
                description=description,
                source=path
            )
        except Exception as e:
            logger.error(f"Failed to load from PDF '{path}': {e}")
            raise