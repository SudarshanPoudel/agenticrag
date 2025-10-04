from typing import List, Literal, Optional, Union
from pydantic import BaseModel


class LLMNode(BaseModel):
    provider: Literal["google"]
    model: str
    api_key: str


#  Stores
class SQLTableNode(BaseModel):
    conn_url : str
    table_name : str

class MetaDbStoreNode(SQLTableNode):
    store_name: Literal["meta"]

class ExternalDbStoreNode(SQLTableNode):
    store_name: Literal["external_db"]

class TableStoreNode(SQLTableNode):
    store_name: Literal["table"]


class ChromaStoreNode(BaseModel):
    store_name: Literal["chroma"]
    collection_name: str
    distance_metric: Literal["cosine", "dot_product", "euclidean"]


# Retrievers
class SQLRetrieverNode(BaseModel):
    retriever_name: Literal["sql_retriever"]
    store: ExternalDbStoreNode
    llm: LLMNode

class TableRetrieverNode(BaseModel):
    retriever_name: Literal["table_retriever"]
    store: TableStoreNode
    llm: LLMNode

class VectorRetrieverNode(BaseModel):
    retriever_name: Literal["vector_retriever"]
    store: Union[ChromaStoreNode]

# Tasks
class QuestionAnsweringTaskNode(BaseModel):
    task_name: Literal["qa_task"]
    llm: LLMNode

class ChartGenerationTaskNode(BaseModel):
    task_name: Literal["chart_task"]
    llm: LLMNode

class RagAgent(BaseModel):
    name: Optional[str] = "AgenticRAG"
    tasks: List[Union[QuestionAnsweringTaskNode, ChartGenerationTaskNode]]
    retrievers: List[Union[SQLRetrieverNode, TableRetrieverNode, VectorRetrieverNode]]
    llm: LLMNode
    meta_store: MetaDbStoreNode
    
    storage_manager: Optional[str] = ".agenticrag_data"

