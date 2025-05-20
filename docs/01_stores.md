# 1. Stores

Stores form the foundation of the AgenticRAG system, providing a consistent way to manage various data types. Each store is specialized for a particular data format and typically connects to a storage backend.

### Available Storage Backends

The library provides two built-in storage backends:
- **SQLBackend**: Uses relational databases for structured data storage
- **ChromaBackend**: Uses vector databases for embedding-based retrieval

You can implement custom backends by inheriting from the `BaseBackend` abstract class and implementing methods for CRUD.

```python
from agenticrag.stores import BaseBackend
from agenticrag.types import BaseData

class MyCustomBackend(BaseBackend[SchemaType]):
    def __init__(self, schema: Type[SchemaType]...):
        # Implement Your logic
    
    def add(self, data):
        # Implement adding data
        pass
    
    def get(self, id):
        # Implement data retrieval
        pass
    
    # Implement other required methods
```

To make store for specific type of data, you can inherit any of the backend as required and implement with specific schema, model or other parameters as required.

### Core Store Types

The library includes four primary store types:

### MetaStore
Maintains metadata about all datasets, essential for decision-making by the RAGAgent.

```python
from agenticrag.stores import MetaStore
from agenticrag.types import MetaData, DataFormat

# Initialize metastore
meta_store = MetaStore(connection_url="sqlite:///agenticrag.db")

# Add dataset metadata
meta_store.add(
    MetaData(
        name="company_docs",
        format=DataFormat.TEXT,
        description="Internal company documentation",
        tags=["internal", "documentation"]
    )
)

# Query metadata
text_datasets = meta_store.filter(format=DataFormat.TEXT)
```

### TextStore
Manages text data with support for embeddings and semantic search.

```python
from agenticrag.stores import TextStore
from agenticrag.types import TextData

# Initialize with persistent vector DB
text_store = TextStore(persistent_dir="./vector_db")

# Add text data
text_store.add(
    TextData(
        id="doc_123",
        name="architecture_overview",
        text="The system follows a microservice architecture...",
        source="internal_wiki"
    )
)

# Search similar content
similar_texts = text_store.search_similar(
    "system design patterns", 
    document_name="architecture_overview", 
    top_k=10
)
```

### TableStore
Specialized for tabular data like CSVs and dataframes.

```python
from agenticrag.stores import TableStore
from agenticrag.types import TableData

# Initialize 
table_store = TableStore(connection_url="sqlite:///agenticrag.db")

# Add table reference
table_store.add(
    TableData(
        id=1,
        name="sales_data",
        path="data/sales_2023.csv",
        structure_summary="""
        Sales data with columns:
        - date (datetime): Transaction date
        - product_id (int): Product identifier
        - quantity (int): Units sold
        - revenue (float): Total revenue
        - region (str): Sales region
        """,
    )
)
```

### ExternalDBStore
Interfaces with external databases via connection strings.

```python
from agenticrag.stores import ExternalDBStore

# Initialize
external_db_store = ExternalDBStore(connection_url="sqlite:///agenticrag.db")

# Add database connection
external_db_store.add_connection(
    name="production_db",
    connection_url="postgresql://user:pass@localhost:5432/production",
    description="Production database with customer and order tables",
    tables=["customers", "orders", "products"]
)
```