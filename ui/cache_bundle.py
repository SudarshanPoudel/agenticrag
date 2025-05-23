from collections import namedtuple

import streamlit as st
import os

from agenticrag import RAGAgent
from agenticrag.loaders import TextLoader, TableLoader
from agenticrag.connectors import ExternalDBConnector
from agenticrag.retrievers import TableRetriever, VectorRetriever, SQLRetriever
from agenticrag.tasks import QuestionAnsweringTask, ChartGenerationTask
from agenticrag.stores import TextStore, MetaStore, TableStore, ExternalDBStore

@st.cache_resource
def get_agent():
    BASE_DIR = os.path.dirname(__file__)  # This will be 'ui/'
    # persist_dir = BASE_DIR +".agenticrag_data"
    persist_dir =  "ui/.agenticrag_data"

    os.makedirs(persist_dir, exist_ok=True)

    conn_url = f"sqlite:///{persist_dir}/agenticrag.db"
    meta_store = MetaStore(connection_url=conn_url) 
    text_store  = TextStore(persist_dir)
    table_store = TableStore(conn_url)
    external_db_store = ExternalDBStore(conn_url)

    text_loader = TextLoader(store=text_store, meta_store=meta_store)
    table_loader = TableLoader(store=table_store, meta_store=meta_store, persistence_dir=persist_dir + "/tables")
    external_db_connector = ExternalDBConnector(store=external_db_store, meta_store=meta_store)

    table_retriever = TableRetriever(store=table_store, persistent_dir=persist_dir + "/retrieved_data")
    vector_retriever = VectorRetriever(store=text_store, persistent_dir=persist_dir + "/retrieved_data")
    sql_retriever = SQLRetriever(store=external_db_store, persistent_dir=persist_dir + "/retrieved_data")

    question_answering_task = QuestionAnsweringTask()
    chart_generation_task = ChartGenerationTask(save_charts_at= persist_dir + "/charts")

    AgentBundle = namedtuple('AgentBundle', [
        'agent',
        'meta_store',
        'text_store',
        'table_store',
        'external_db_store',
        'text_loader',
        'table_loader',
        'external_db_connector',
        'table_retriever',
        'vector_retriever',
        'sql_retriever',
        'question_answering_task',
        'chart_generation_task',
    ])

    agent = RAGAgent(
        meta_store=meta_store,
        retrievers=[table_retriever, vector_retriever, sql_retriever],
        tasks=[question_answering_task, chart_generation_task],
        persistent_dir=persist_dir
    )

    return AgentBundle(
        agent=agent,
        meta_store=meta_store,
        text_store=text_store,
        table_store=table_store,
        external_db_store=external_db_store,
        text_loader=text_loader,
        table_loader=table_loader,
        external_db_connector=external_db_connector,
        table_retriever=table_retriever,
        vector_retriever=vector_retriever,
        sql_retriever=sql_retriever,
        question_answering_task=question_answering_task,
        chart_generation_task=chart_generation_task,
    )
