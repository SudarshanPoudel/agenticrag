from __future__ import annotations
import os
import streamlit as st
from typing import List
from agenticrag import RAGAgent
from agenticrag.core.llm_client import LLMClient
from agenticrag.loaders import TextLoader, TableLoader
from agenticrag.connectors import ExternalDBConnector
from agenticrag.retrievers import TableRetriever, VectorRetriever, SQLRetriever
from agenticrag.tasks import QuestionAnsweringTask, ChartGenerationTask
from agenticrag.stores import TextStore, MetaStore, TableStore, ExternalDBStore
from agenticrag.utils.llm import get_default_llm
from ui.project_config import ProjectConfig, load_project_config

class AgentBundle:
    def __init__(self, agent: RAGAgent, components: dict):
        self.agent = agent
        self.components = components

@st.cache_resource
def get_agent_bundle(project_name: str) -> AgentBundle:
    cfg = load_project_config(project_name=project_name)
    if not cfg:
        return None
    agent_bundle = build_agent_from_config(cfg)
    return agent_bundle


def build_agent_from_config(cfg: ProjectConfig) -> AgentBundle:
    os.makedirs(cfg.persist_dir, exist_ok=True)

    # meta store is required
    meta_store = MetaStore(connection_url=cfg.meta_conn_url)

    text_store = None
    table_store = None
    external_db_store = None

    if cfg.stores.enable_text_store:
        text_store = TextStore(cfg.persist_dir)

    if cfg.stores.enable_table_store:
        table_store = TableStore(cfg.meta_conn_url)  # reuse meta conn_url for simplicity

    if cfg.stores.enable_external_db_store:
        external_db_store = ExternalDBStore(cfg.meta_conn_url)

    llm_model = _get_llm_from_config(cfg.llm)

    # loaders/connectors conditional
    text_loader = None
    table_loader = None
    external_db_connector = None
    extras = cfg.extras

    if text_store:
        text_loader = TextLoader(store=text_store, meta_store=meta_store, chunk_size=extras.get("text_loader_chunk_size", 2000), chunk_overlap=extras.get("text_loader_chunk_overlap", 200), llm=llm_model)
        

    if table_store:
        tables_dir = os.path.join(cfg.persist_dir, "tables")
        os.makedirs(tables_dir, exist_ok=True)
        table_loader = TableLoader(store=table_store, meta_store=meta_store, persistence_dir=tables_dir, llm=llm_model)

    if external_db_store:
        external_db_connector = ExternalDBConnector(store=external_db_store, meta_store=meta_store, llm=llm_model)

    # retrievers conditional with top_k and persistent_dir
    retrieved_dir = os.path.join(cfg.persist_dir, "retrieved_data")
    os.makedirs(retrieved_dir, exist_ok=True)

    retrievers = []

    table_retriever = None
    vector_retriever = None
    sql_retriever = None

    if cfg.retrievers.enable_table_retriever and table_store:
        table_retriever = TableRetriever(store=table_store, persistent_dir=retrieved_dir, llm=llm_model)

    if cfg.retrievers.enable_vector_retriever and text_store:
        vector_retriever = VectorRetriever(store=text_store, persistent_dir=retrieved_dir, top_k=cfg.retrievers.vector_top_k)

    if cfg.retrievers.enable_sql_retriever and external_db_store:
        sql_retriever = SQLRetriever(store=external_db_store, persistent_dir=retrieved_dir, llm=llm_model)

    for r in [table_retriever, vector_retriever, sql_retriever]:
        if r:
            retrievers.append(r)

    # tasks
    tasks = []
    qa_task = None
    chart_task = None

    if cfg.tasks.enable_qa_task:
        qa_task = QuestionAnsweringTask(llm=llm_model)
        tasks.append(qa_task)

    if cfg.tasks.enable_chart_task:
        charts_dir = os.path.join(cfg.persist_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        chart_task = ChartGenerationTask(llm=llm_model, save_charts_at=charts_dir)
        tasks.append(chart_task)


    agent = RAGAgent(
        meta_store=meta_store,
        retrievers=retrievers,
        tasks=tasks,
        persistent_dir=cdf(cfg.persist_dir) if False else cfg.persist_dir,
        model=llm_model
    )

    components = dict(
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
        qa_task=qa_task,
        chart_task=chart_task,
        cfg=cfg,
    )
    return AgentBundle(agent=agent, components=components)


def _get_llm_from_config(conf):
    return LLMClient(model="gemini/gemini-2.0-flash", api_key=conf.api_key)