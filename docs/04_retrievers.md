# Retrievers

Retrievers extract relevant information from stores based on user queries. They are specialized by data type and retrieval method. They are normally used directly by RAG Agent which orchestrates the workflow, so to avoid retrieved data getting lost
in llm communication, we generally provide a *persistent_dir* where these retrievers save the retrieved data and return a string message saying where retrieved data is instead of actual data.

#### VectorRetriever

Uses semantic search for text data retrieval.

```python
from agenticrag.retrievers import VectorRetriever

# Initialize
vector_retriever = VectorRetriever(
    text_store=text_store,
    persistent_dir="./retrieved_data",
    top_k=10
)

# Retrieve relevant text chunks
result = vector_retriever.retrieve(
    query="How does multi-head attention work?",
    document_name="attention_paper",  # Optional, can search across all documents
)

print(result)
```

#### TableRetriever

Specializes in retrieving and processing tabular data.

```python
from agenticrag.retrievers import TableRetriever

# Initialize
table_retriever = TableRetriever(
    table_store=table_store,
    persistent_dir="./retrieved_data"
)

# Retrieve with filtering and transformation
result = table_retriever.retrieve(
    query="Get average revenue by region for Q1 2023",
    data_name="name" # name of the data/file in meta store
)

print(result)
```

#### SQLRetriever

Executes SQL queries against external databases.

```python
from agenticrag.retrievers import SQLRetriever

# Initialize
sql_retriever = SQLRetriever(
    external_db_store=external_db_store,
    persistent_dir="./retrieved_data"
)

# Retrieve using natural language which gets converted to SQL
result = sql_retriever.retrieve(
    query="Find customers who made purchases over $1000 last month",
    db_name="production_db",
)

print(result)
```

#### Creating Custom Retrievers

You can create custom retrievers for specialized retrieval logic:

```python
from agenticrag.retrievers import BaseRetriever
import os

class HybridRetriever(BaseRetriever):
    def __init__(self, text_store, table_store, persistent_dir):
        self.text_store = text_store
        self.table_store = table_store
        self.persistent_dir = persistent_dir
        os.mkdir(self.persistent_dir) if not os.path.exists(self.persistent_dir) else None

    @property
    def name(self):
        return 'hybrid_retriever'
    
    @property
    def description(self):
        return (
            f"This retriever requires a user query in the input and retrieves relevant text chunks by "
            f"doing hybrid text search from database. It then saves those chunks in "
            f"`{self.persistent_dir}/text_data.txt`."
        )
    
    @property
    def working_data_format(self):
        return DataFormat.TEXT
        
    def retrieve(self, query, table_name):
        # Your retrieving logic
        # ...
        text_results = your_custom_logic()

        # Save combined results
        output_path = os.path.join(self.persistent_dir, "hybrid_results.txt")
        with open(output_path, "w") as f:
            f.write("TEXT RESULTS:\n")
            for text in text_results:
                f.write(f"{text.text}\n\n")
        
        
        return f"Retrieved hybrid data saved to: {output_path}"
```


!!! note "Note"
    While creating custom retrievers be extra careful, have clear name, description as well as clear arguments in .retrieve() method. Only take necessary arguments and avoid use of \*args and \*\*kwargs, if possible values like top_k which can be set by default should be set in constructor instead of .retrieve()