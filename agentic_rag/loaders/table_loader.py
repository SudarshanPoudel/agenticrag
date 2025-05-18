import os
import shutil
from langchain_core.language_models.chat_models import BaseChatModel

from agentic_rag.loaders.base import BaseLoader
from agentic_rag.loaders.utils.description_generators import csv_to_desc
from agentic_rag.loaders.utils.extract_csv_structure import extract_csv_structure
from agentic_rag.stores import MetaStore, TableStore
from agentic_rag.types.core import DataFormat
from agentic_rag.types.exceptions import LoaderError
from agentic_rag.types.schemas import MetaData, TableData
from agentic_rag.utils.logging_config import setup_logger


logger = setup_logger(__name__)


class TableLoader(BaseLoader):
    """
    Loader class for ingesting tabular data (CSV, Excel, JSON, DataFrame, etc.)
    into structured TableStore and MetaStore.
    """

    def __init__(self, store: TableStore, meta_store: MetaStore, persistence_dir: str, llm: BaseChatModel = None):
        """
        Args:
            store (TableStore): Storage handler for table structures.
            meta_store (MetaStore): Storage handler for metadata.
            persistence_dir (str): Directory to persist uploaded files into csv format.
        """
        self.persistence_dir = persistence_dir
        self.store = store
        self.meta_store = meta_store
        self.llm = llm

    def load_csv(self, file_path: str, name: str = None, description: str = None, source: str = None) -> str:
        """
        Loads a CSV file, persists it, extracts structure, and stores its data and metadata.

        Args:
            file_path (str): Path to the CSV file.
            name (str, optional): Display name of the table. Defaults to file name.
            description (str, optional): Optional description. Auto-generated if not provided.
            source (str, optional): Original source info. Defaults to file path.
        """
        try:
            os.makedirs(self.persistence_dir, exist_ok=True)
            destination = os.path.join(self.persistence_dir, os.path.basename(file_path))
            shutil.copy(file_path, destination)

            table_name = name or os.path.basename(file_path)
            if not description:
                if not self.llm:
                    raise LoaderError("LLM not provided, cannot generate description")
                description = csv_to_desc(destination, llm=self.llm)
            table_description = description
            table_source = source or file_path

            structure = extract_csv_structure(file_path=destination)
            logger.debug(f"Extracted structure summary for {table_name}: {structure}")

            table_data = TableData(
                name=table_name,
                path=destination,
                structure_summary=structure
            )
            self.store.add(data=table_data)

            metadata = MetaData(
                name=table_name,
                description=table_description,
                source=table_source,
                format=DataFormat.TABLE
            )
            self.meta_store.add(metadata)
            logger.info(f"Loaded CSV '{file_path}' into TableStore and MetaStore")
            return name
        
        except Exception as e:
            logger.error(f"Failed to load CSV '{file_path}': {e}", exc_info=True)
            raise LoaderError(f"Failed to load CSV: {file_path}") from e
