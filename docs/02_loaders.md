# Loaders

Loaders simplify the process of ingesting data into stores by handling parsing, preprocessing, and metadata generation. They abstract away the complexity of working directly with stores.

### TextLoader

Handles various text formats including plain text, PDFs, and web content.

```python
from agenticrag.loaders import TextLoader
from langchain_google_genai import ChatGoogleGenerativeAI

# Define LLM to utilize automatic description generation and more, you can use any ChatModel from langchain
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key="<your_api_key>",
)

# Initialize with appropriate stores
text_loader = TextLoader(
    text_store=text_store,  
    meta_store=meta_store,
    chunk_size = 2000,
    chunk_overlap = 200,
    llm = llm # or leave it empty to use DEFAULT_LLM (Gemini-2.0-flash), we can use llm 
)

# Load PDF with automatic chunking and metadata generation
text_loader.load_pdf(
    path="data/research_paper.pdf"
)

# Load from web URL
text_loader.load_web(
    url="https://example.com/article",
    name="web_article"
)
```

### TableLoader

Specializes in loading tabular data with automatic schema detection.

```python
from agenticrag.loaders import TableLoader

# Initialize
table_loader = TableLoader(
    table_store=table_store,
    meta_store=meta_store,
    persistence_dir="./table_data",
    llm=llm
)

# Load CSV with automatic schema inference
table_loader.load_csv(
    path="data/customer_data.csv",
    name="customers"
)

# Load from pandas DataFrame
import pandas as pd
df = pd.read_excel("data/financial_report.xlsx")
table_loader.load_dataframe(
    df=df,
    name="financial_data",
)
```

### Creating Custom Loaders

You can create custom loaders for specialized data sources:

```python
from agenticrag.loaders import BaseLoader
from agenticrag.types.exceptions import LoaderError

class JSONLoader(BaseLoader):
    def __init__(self, text_store, meta_store):
        self.text_store = text_store
        self.meta_store = meta_store
        
    def load_json(self, path, name, description=None):
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Convert to text representation
        text_content = json.dumps(data, indent=2)
        
        # Add metadata
        meta = self.meta_store.add(
            MetaData(
                name=name,
                format=DataFormat.TEXT,
                description=description or f"JSON data from {path}", # or use LLM to generate one
                source= path
            )
        )
        
        try:
            json_data = self.text_store.add(
                TextData(
                    id=f"json_{name}",
                    name=name,
                    text=text_content
                )
            )
            return meta
            
        except Exception as e:
            self.meta_store.delete(meta.id) # Always evert data from meta store if error occurred while adding in main store.
            raise LoaderError("Error") from e

```
