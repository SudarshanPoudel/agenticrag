# Quickstart

Build powerful Retrieval-Augmented Generation (RAG) applications with minimal or advanced setup using `agenticrag`.

## Prerequisites
- Python 3.8+
- Install agenticrag:
```bash
pip install agenticrag
```

!!! tip "Tip"
    If you are planning on full customization you can install minimal version with `pip install agenticrag[minimal]`. 
    This excludes optional dependencies, giving you full control over which libraries to install based on your needs.


## Quick RAGAgent Setup

This is the simplest way to get started. Just create an agent, load some data (PDFs, webpages), and invoke queries.

```python
import os
from agenticrag import RAGAgent

# Set Gemini API Key (required for default LLM)
os.environ["GEMINI_API_KEY"] = "<YOUR GEMINI API KEY>"

# Create agent with default setup
agent = RAGAgent()

# Load a PDF file
agent.load_pdf(
    path="data/attention.pdf",
    name="attention_paper",
)

# Load from a website
agent.load_web(
    url="https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    name="rag_wiki"
)

# Ask a question
response = agent.invoke("What is Retrieval-Augmented Generation?")
print("Answer:", response.content)
print("Sources:", [s.name for s in response.datasets])
```

*Done. Just load and ask.*


## Advanced Multi-Source Project

Build a robust, multi-modal RAG pipeline with fully customizable components.

```python
from agenticrag import RAGAgent
from agenticrag.stores import MetaStore, TextStore, TableStore, ExternalDBStore
from agenticrag.retrievers import VectorRetriever, TableRetriever, SQLRetriever
from agenticrag.tasks import QuestionAnsweringTask, ChartGenerationTask
from agenticrag.loaders import TextLoader, TableLoader
from agenticrag.connectors import ExternalDBConnector
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-pro",
    api_key="<YOUR GEMINI API KEY>",
)

# Initialize persistent stores
meta_store = MetaStore(
    connection_url="sqlite:///project.db"
)
text_store = TextStore(
    persistent_dir="./vector_store", embedding_function="default"
)
table_store = TableStore(
    connection_url="sqlite:///project.db"
)
external_db_store = ExternalDBStore(
    connection_url="sqlite:///project.db"
)

# Initialize loaders
text_loader = TextLoader(
    text_store, meta_store, chunk_size=100, chunk_overlap=20, llm=llm)
table_loader = TableLoader(
    table_store, meta_store, persistence_dir="./tables", llm=llm)

# Connect external DB
db_connector = ExternalDBConnector(external_db_store, meta_store, llm=llm)

# Load data
text_loader.load_pdf("./docs.pdf")
table_loader.load_csv("./data/metrics.csv")
db_connector.connect_db(
    name="analytics", 
    connection_url_env_var="ANALYTICS_DB_URL"
)

# Initialize retrievers
vector_retriever = VectorRetriever(
    text_store, persistent_dir="./retrieved_data")
table_retriever = TableRetriever(
    table_store, persistent_dir="./retrieved_data")
sql_retriever = SQLRetriever(
    external_db_store, persistent_dir="./retrieved_data")

# Initialize tasks
qa_task = QuestionAnsweringTask()
chart_task = ChartGenerationTask()

# Create the custom agent
agent = RAGAgent(
    persistent_dir="./project_data",
    retrievers=[vector_retriever, table_retriever, sql_retriever],
    tasks=[qa_task, chart_task]
)

# Invoke with a complex prompt
response = agent.invoke(
    "What was the average user growth over the last 4 quarters? Also, show a chart comparing user growth and churn rate."
)

print("Answer:\n", response.content)
```

---

!!! tip "Tip"
    You can always start with the minimal setup and gradually plug in your own loaders, retrievers, and task modules as your use case grows.
