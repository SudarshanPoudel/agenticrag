# AgenticRAG

[![PyPI version](https://badge.fury.io/py/agenticrag.svg)](https://badge.fury.io/py/agenticrag)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

AgenticRAG is a modular framework for building customizable Retrieval-Augmented Generation systems. It provides a complete stack for ingesting, storing, retrieving, and acting on diverse data types through a unified interface.

![agenticrag](agenticrag.png)

---

## Key Features

- **Modular Architecture**: Easily customize any component while maintaining system compatibility
- **Multi-format Data Support**: Handle text, tables, and databases through specialized stores
- **Flexible Data Ingestion**: Import data from PDFs, CSVs, web pages, and external databases
- **Intelligent Retrieval**: Use semantic search, SQL queries, or table operations as needed
- **Task-oriented Design**: Perform question answering, chart generation, or custom operations
- **Easy Extensibility**: Create custom components with minimal boilerplate

---

## Installation

### For Users

Install the stable release from PyPI:

```bash
pip install agenticrag
```

### For Contributors

Clone the repository and install development dependencies:

```bash
git clone https://github.com/yourusername/agenticrag.git
cd agenticrag
pip install -r requirements.txt
pip install -e .
```
---

## Quick Start

```python
from agenticrag import RAGAgent

# Initialize agent with default components
agent = RAGAgent(persistent_dir="./agenticrag_data")

# Load some data
agent.load_pdf("path/to/document.pdf", name="company_handbook")
agent.load_csv("path/to/data.csv", name="sales_data")

# Ask questions using the data
response = agent.invoke("What were our top selling products last quarter?")
print(response)
```

---

## Architecture Overview
![AgenticRAG Architecture](docs/architecture.png)


The AgenticRAG system follows a modular, layered architecture where each component has specific responsibilities:

1. **Data Storage Layer**: Stores maintain structured representations of various data types
2. **Data Ingestion Layer**: Loaders and Connectors handle importing data into stores
3. **Data Retrieval Layer**: Retrievers access relevant information based on queries
4. **Task Execution Layer**: Tasks perform operations using retrieved context
5. **Orchestration Layer**: RAGAgent coordinates all components to fulfill user requests

---

## Documentation

For detailed documentation, check out:

- [Full Documentation](https://sudarshanpoudel.github.io/agenticrag/): Complete guide to architecture and components
- [Examples](examples/): Jupyter notebooks showing various use cases

---

## Project Structure

```
├── agenticrag/                # Main package
│   ├── connectors/            # Database and API connectors
│   ├── loaders/               # Data ingestion components
│   ├── retrievers/            # Context retrieval components
│   ├── stores/                # Data storage components
│   ├── tasks/                 # Task execution components
│   ├── types/                 # Data models and type definitions
│   ├── utils/                 # Utility functions and helpers
│   └── rag_agent.py           # Main agent implementation
├── docs/                      # Documentation
├── examples/                  # Example notebooks
├── tests/                     # Unit and integration tests
├── ui/                        # Streamlit demo app
├── LICENSE                    # MIT License
├── pyproject.toml             # Package configuration
├── README.md                  # This file
└── requirements.txt           # Development dependencies
```

---

## Example Use Cases

### Question Answering from Documents

```python
from agenticrag import RAGAgent

agent = RAGAgent()
agent.load_pdf("research_paper.pdf", name="research")
agent.invoke("Summarize the key findings of the research paper")
```

### Data Analysis with Visualizations

```python
from agenticrag import RAGAgent
from agenticrag.retrievers import TableRetriever
from agenticrag.tasks import ChartGenerationTask

agent = RAGAgent(
    retrievers=[TableRetriever()],
    tasks=[ChartGenerationTask()]
)
agent.load_csv("Iris.csv")
agent.invoke("Create a scatter plot showing petel length and width of Iris")
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
