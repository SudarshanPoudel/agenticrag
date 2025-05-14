from ..types.core import DBInfoData, MetaData
import os
from ..datastores.sqlstores.db_info_store import DBInfoStore
from .base import BaseDataConnector
from .utils.extract_db_structure import extract_db_structure, summarize_db
from ..utils.logging_config import setup_logger

logger = setup_logger(__name__)

class DBConnector(BaseDataConnector):
    def __init__(self):
        pass

    @property
    def data_store(self):
        return DBInfoStore()
    
    def connect_db(self, name: str = "database", connection_url: str = None, connection_url_env_var: str = None, summary: str = None):
        if connection_url and not connection_url_env_var:
            logger.warning("Directly using connection_url is less secure, use connection_url_env_var instead")
        if connection_url_env_var:
            connection_url = os.getenv(connection_url_env_var)
        elif not connection_url:
            raise ValueError("connection_url or connection_url_env_var must be provided")
        
        db_structure = extract_db_structure(connection_url=connection_url)
        if not summary:
            summary = summarize_db(db_structure=db_structure)

        if connection_url_env_var:
            connection_url = None

        data = DBInfoData(connection_url=connection_url, connection_url_env_var=connection_url_env_var, name=name, db_structure=db_structure, summary=summary)
        self.data_store.store(data=data)


        metadata = MetaData(
            type="database_data",
            name=name,
            description=summary
        )
        self.meta_store.store(data=metadata)
