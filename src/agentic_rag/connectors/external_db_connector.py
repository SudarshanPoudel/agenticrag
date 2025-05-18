import os
from langchain_core.language_models.chat_models import BaseChatModel

from agentic_rag.connectors.base import BaseDataConnector
from agentic_rag.connectors.utils.extract_db_structure import extract_db_structure, summarize_db
from agentic_rag.stores import ExternalDBStore, MetaStore
from agentic_rag.types.core import DataFormat
from agentic_rag.types.schemas import ExternalDBData, MetaData
from agentic_rag.utils import llm
from agentic_rag.utils.logging_config import setup_logger
from agentic_rag.types.exceptions import ConnectorError

logger = setup_logger(__name__)


class ExternalDBConnector(BaseDataConnector):
    """
    Connects to an external database and stores its structure and metadata.
    """
    def __init__(self, store: ExternalDBStore = ExternalDBStore(), meta_store: MetaStore = MetaStore(), llm:BaseChatModel =None):
        self.store = store
        self.meta_store = meta_store
        self.llm = llm

    def connect_db(
        self,
        name: str = "database",
        connection_url: str = None,
        connection_url_env_var: str = None,
        description: str = None
    ) -> str:
        """
        Extracts schema from the external DB and stores both structure and metadata.

        Args:
            name (str): Identifier for the database.
            connection_url (str, optional): Direct connection string.
            connection_url_env_var (str, optional): Environment variable for connection string.
            description (str, optional): Optional DB summary description.
        """
        try:
            if connection_url and not connection_url_env_var:
                logger.warning(
                    f"Using plain connection string for '{name}'. Consider using environment variable."
                )

            if connection_url_env_var:
                connection_url = os.getenv(connection_url_env_var)
                if not connection_url:
                    raise ValueError(f"Environment variable '{connection_url_env_var}' not found.")
            elif not connection_url:
                raise ValueError("Either 'connection_url' or 'connection_url_env_var' must be provided.")

            logger.info(f"Connecting to database for '{name}'...")
            structure = extract_db_structure(connection_url=connection_url)
            logger.debug(f"Structure extraction successful for '{name}'.")

            if not description:
                if not self.llm:
                    raise ConnectorError("LLM not provided, so cannot auto-generate description.")
                description = summarize_db(db_structure=structure, llm = self.llm)
                logger.debug(f"Auto-generated description for '{name}'.")

            # Store structure without connection string if env var is used
            safe_url = None if connection_url_env_var else connection_url
            db_data = ExternalDBData(
                name=name,
                connection_url=safe_url,
                connection_url_env_var=connection_url_env_var,
                db_structure=structure
            )
            self.store.add(db_data)

            metadata = MetaData(
                name=name,
                description=description,
                source="External Database",
                format=DataFormat.EXTERNAL_DB
            )
            self.meta_store.add(metadata)
            logger.info(f"Connected and stored database '{name}'.")
            return name


        except Exception as e:
            logger.error(f"Failed to connect and store database '{name}': {e}")
            raise ConnectorError("Failed to connect external database.") from e
