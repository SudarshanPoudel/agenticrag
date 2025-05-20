from agenticrag.types.exceptions import RAGAgentError
from agenticrag.loaders import TableLoader, TextLoader
from agenticrag.connectors import ExternalDBConnector

class RAGAgentLoaderMixin:
    """
    Mixin providing data loading and external data source connection methods for RAGAgent.
    """

    def load_text(self, text: str, name: str, description: str = None, source: str = None):
        """
        Load plain text data into the text store.
 
        Args:
            text (str): Text content to load.
            name (str): Name identifier for the text.
            description (str, optional): Optional description, if not provided use LLM to generate.
            source (str, optional): Source information, default to name.
        """
        if not self.text_store:
            raise RAGAgentError("Text store not initialized")
        loader = TextLoader(store=self.text_store, meta_store=self.meta_store, llm=self.llm)
        return loader.load_text(text, name, description, source)

    def load_web(self, url: str, name: str = None, description: str = None):
        """
        Load and parse web page content into the text store.

        Args:
            url (str): URL of the web page to load.
            name (str, optional): Optional name identifier, default to webpage title.
            description (str, optional): Optional description, if not provided use LLM to generate.
        """
        if not self.text_store:
            raise RAGAgentError("Text store not initialized")
        loader = TextLoader(store=self.text_store, meta_store=self.meta_store, llm=self.llm)
        return loader.load_web(url, name, description)

    def load_pdf(self, path: str, name: str = None, description: str = None):
        """
        Load and parse PDF content into the text store.

        Args:
            path (str): Path to the PDF file.
            name (str, optional): Optional name identifier, default to file name.
            description (str, optional): Optional description, if not provided use LLM to generate.
        """
        if not self.text_store:
            raise RAGAgentError("Text store not initialized")
        loader = TextLoader(store=self.text_store, meta_store=self.meta_store, llm=self.llm)
        return loader.load_pdf(path, name, description)

    def load_csv(self, file_path: str, name: str = None, description: str = None, source: str = None):
        """
        Load CSV file data into the table store.

        Args:
            file_path (str): Path to the CSV file.
            name (str, optional): Optional name identifier, default to file name.
            description (str, optional): Optional description, if not provided use LLM to generate.
            source (str, optional): Source information, default to file path.
        """
        if not self.table_store:
            raise RAGAgentError("Table store not initialized")
        loader = TableLoader(self.table_store, self.meta_store, f"{self.persistence_dir}/tables", self.llm)
        return loader.load_csv(file_path, name, description, source)

    def connect_db(self, name: str = "database", connection_url: str = None, connection_url_env_var: str = None, description: str = None):
        """
        Connect to an external database and register it in the external DB store.

        Args:
            name (str): Name identifier for the database connection.
            connection_url (str, optional): Direct database connection URL (Recommended not to use this, use connection_url_env_var instead).
            connection_url_env_var (str, optional): Environment variable name containing the connection URL.
            description (str, optional): Optional description, if not provided use LLM to generate.
        """
        if not self.external_db_store:
            raise RAGAgentError("External DB store not initialized")
        connector = ExternalDBConnector(self.external_db_store, self.meta_store, self.llm)
        return connector.connect_db(name=name, connection_url=connection_url, connection_url_env_var=connection_url_env_var, description=description)
