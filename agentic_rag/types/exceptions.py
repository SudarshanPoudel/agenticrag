class AgenticRAGException(Exception):
    """Base exception class for AgenticRAG."""
    pass

class RAGAgentError(AgenticRAGException):
    """Raised when an RAG agent fails."""
    pass

class LoaderError(AgenticRAGException):
    """Raised when a data loader fails."""
    pass

class ConnectorError(AgenticRAGException):
    """Raised when a data connector fails."""
    pass


class StoreError(AgenticRAGException):
    """Raised when a storage operation fails."""
    pass


class RetrievalError(AgenticRAGException):
    """Raised when data retrieval fails."""
    pass


class TaskExecutionError(AgenticRAGException):
    """Raised when a task agent fails during execution."""
    pass


class ConfigurationError(AgenticRAGException):
    """Raised for invalid or missing configuration."""
    pass
