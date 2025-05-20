import os
from langchain_core.language_models.chat_models import BaseChatModel

from agenticrag.connectors.base import BaseDataConnector
from agenticrag.connectors.utils.extract_db_structure import extract_db_structure, summarize_db
from agenticrag.stores import ExternalDBStore, MetaStore
from agenticrag.types.core import DataFormat
from agenticrag.types.core import ExternalDBData, MetaData
from agenticrag.utils.llm import get_default_llm
from agenticrag.utils.logging_config import setup_logger
from agenticrag.types.exceptions import ConnectorError

logger = setup_logger(__name__)


class ExternalDBConnector(BaseDataConnector):
    """
    Connects to an external database and stores its structure and metadata.
    """
    def __init__(self, store: ExternalDBStore, meta_store: MetaStore, llm:BaseChatModel =None):
        self.store = store
        self.meta_store = meta_store
        self.llm = llm or get_default_llm()

    def connect_db(
        self,
        name: str = "database",
        connection_url: str = None,
        connection_url_env_var: str = None,
        description: str = None
    ) -> MetaData:
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
                    raise ConnectorError(f"Environment variable '{connection_url_env_var}' not found.")
            elif not connection_url:
                raise ConnectorError("Either 'connection_url' or 'connection_url_env_var' must be provided.")

            logger.info(f"Connecting to database for '{name}'...")
            structure = extract_db_structure(connection_url=connection_url)
            logger.debug(f"Structure extraction successful for '{name}'.")

            if not description:
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

            metadata = MetaData(
                name=name,
                description=description,
                source="External Database",
                format=DataFormat.EXTERNAL_DB
            )
            meta = self.meta_store.add(metadata)
            try:
                db = self.store.add(db_data)
                logger.info(f"Connected and stored database with Database_id = {db.id} and Meta_id = {meta.id}")
                return metadata
            except Exception as e:
                self.meta_store.delete(meta.id)
                raise

        except Exception as e:
            logger.error(f"Failed to connect and store database '{name}': {e}")
            raise ConnectorError("Failed to connect external database.") from e
