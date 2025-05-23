import sys
import os
import re

from httpx import get
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
torch.classes.__path__ = []

from agenticrag import RAGAgent
from agenticrag.loaders import TextLoader, TableLoader
from agenticrag.connectors import ExternalDBConnector
from agenticrag.retrievers import TableRetriever, VectorRetriever, SQLRetriever
from agenticrag.tasks import QuestionAnsweringTask, ChartGenerationTask
from agenticrag.stores import TextStore, MetaStore, TableStore, ExternalDBStore, meta_store

import streamlit as st
import tempfile

from ui.cache_bundle import get_agent


def chat_section(agent):
    st.subheader("💬 Ask Your Agent")
    user_input = st.text_input("Ask your question:", key="chat_input")
    if user_input:
        st.markdown(f"**You :** {user_input}")
        agent = get_agent().agent
        response = agent.invoke(user_input)

        
        markdown_content = response.content
        match = re.search(r'!\[.*?\]\((.*?)\)', markdown_content)
        cleaned_markdown = re.sub(r'!\[.*?\]\((.*?)\)', '', markdown_content)
        st.markdown(cleaned_markdown.strip())

        if match:
            image_path = match.group(1)
            st.image(image_path)

        if response.datasets:
            st.markdown("#### 📂 Datasets used:")
            for ds in response.datasets:
                st.markdown(f"- **{ds.name}** — {ds.description}")

        # Show tasks
        if response.tasks:
            st.markdown("#### 🔧 Tasks performed:")
            for task in response.tasks:
                st.markdown(f"- `{task.__class__.__name__}`")


def loader_section(agent):
    st.subheader("📥 Load Data into Agent")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Load PDF")
        pdf_name = st.text_input("Enter PDF name (Optional)", key="pdf_name")
        uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_upload")
        if uploaded_pdf and st.button("Load PDF"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_pdf.read())
                temp_file_path = tmp_file.name
                try:
                    get_agent().text_loader.load_pdf(temp_file_path, name=pdf_name or uploaded_pdf.name, source="UPLOADED : " + uploaded_pdf.name) 
                    st.success(f"Loaded PDF: {uploaded_pdf.name}")
                except Exception as e:
                    st.error(f"Failed to load PDF: {e}")

        st.markdown("#### Website URL")
        website_name = st.text_input("Enter website name (Optional)", key="web_name")
        website_url = st.text_input("Enter website URL", key="web_input")
        if website_url and st.button("Load Website"):
            try:
                get_agent().text_loader.load_web(website_url, name = website_name)
                st.success(f"Loaded website: {website_url}")
            except Exception as e:
                st.error(f"Failed to load website: {e}")

    with col2:
        st.markdown("#### Load CSV")
        csv_name = st.text_input("Enter CSV name (Optional)", key="csv_name")
        uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], key="csv_upload")
        if uploaded_csv and st.button("Load CSV"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_csv.read())
                temp_file_path = tmp_file.name
                try:
                    get_agent().table_loader.load_csv(temp_file_path, name=csv_name or uploaded_csv.name, source="UPLOADED : " + uploaded_csv.name)
                    st.success(f"Loaded CSV: {uploaded_csv.name}")
                except Exception as e:
                    st.error(f"Failed to load CSV: {e}")

        st.markdown("#### Database URL")
        db_name = st.text_input("Enter DB name", key="db_name")
        db_url = st.text_input("Enter DB connection URL", key="db_input")
        if db_url and db_name and st.button("Connect to DB"):
            try:
                get_agent().external_db_connector.connect_db(name = db_name, connection_url=db_url)
                st.success(f"Connected to DB: {db_url}")
            except Exception as e:
                st.error(f"Failed to connect to DB: {e}")

def store_section(agent):
    st.subheader("📚 View Data Stores")
    meta_store = get_agent().meta_store
    text_store = get_agent().text_store
    table_store = get_agent().table_store
    external_db_store = get_agent().external_db_store

    data = [
        {"Store": "Meta Store", "Data": meta_store.get_all()},
        {"Store": "Text Store", "Data": text_store.get_all()},
        {"Store": "Table Store", "Data": table_store.get_all()},
        {"Store": "External DB Store", "Data": external_db_store.get_all()},
    ]


    for store_entry in data:
        store_name = store_entry["Store"]
        rows = store_entry["Data"]

        with st.expander(f"🔹 {store_name}", expanded=True):
            if rows:
                rows_dicts = [row.model_dump() if hasattr(row, "dict") else row for row in rows]
                st.dataframe(rows_dicts)
            else:
                st.write("No data yet.")

def main():
    st.set_page_config(page_title="AgenticRAG App", layout="wide")
    st.title("🤖 AgenticRAG Playground")

    agent = get_agent()

    tab1, tab2, tab3 = st.tabs(["💬 Ask", "📥 Load Data", "📚 Stores"])

    with tab1:
        chat_section(agent)

    with tab2:
        loader_section(agent)

    with tab3:
        store_section(agent)

    with open("ui/style.css", "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
