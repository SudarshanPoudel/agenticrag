import streamlit as st
import os
from ui.agent_factory import get_agent_bundle
from ui.project_config import (
    ProjectConfig, LLMConfig, StoreFlags, RetrieverConfig, TaskConfig,
    save_project_config, load_project_config, list_projects, delete_project
)


def onboarding_panel():
    st.header("Project Setup")
    projects = list_projects()

    if projects:
        sel = st.selectbox("Select project", projects, index=0)
        if st.button("Load Selected", width='stretch'):
            cfg = load_project_config(sel)
            if cfg:
                st.session_state["active_project"] = sel
                get_agent_bundle.clear()
                st.success(f"Loaded project '{sel}'.")
                st.rerun()

        if st.button("Delete Selected", width='stretch'):
            ok = delete_project(sel)
            if ok:
                st.success(f"Project '{sel}' deleted.")
                st.rerun()
            else:
                st.error("Failed to delete project.")

        if st.button("Create New Project", width='stretch'):
            st.session_state["creating_new"] = True
            st.rerun()
    else:
        st.info("No saved projects found.")
        if st.button("Create New Project"):
            st.session_state["creating_new"] = True
            st.rerun()

    
    if st.session_state.get("creating_new"):
        st.divider()
        st.subheader("Create new project")

        # Initialize session defaults
        defaults = {
            "text_store": True,
            "table_store": True,
            "external_db_store": False,
            "qa_task": True,
            "chart_task": False,
        }
        for k, v in defaults.items():
            st.session_state.setdefault(k, v)

        project_name = st.text_input("Project name", value="my_rag_project")
        persist_dir = f"ui/data/.{project_name}_data" if project_name else "ui/data/.project_name_data"
        chat_history_queue_size = st.slider("chat_history_queue_size", 1, 10, 1, 1)
        st.markdown("---")
        st.subheader("LLM")
        provider = st.selectbox("Provider", ["gemini"], index=0)
        model = st.text_input("Model name", value="gemini-2.0-pro")
        api_key = st.text_input("API key", type="password", placeholder=os.getenv("LLM_API_KEY"))

        st.markdown("---")
        st.subheader("Stores")
        
        for store in ["text_store", "table_store", "external_db_store"]:
            enabled = st.session_state[store]
            flex = st.container(horizontal=True, horizontal_alignment="left", vertical_alignment="center")
            if enabled:
                if flex.button("Disable", key=f"disable_{store}", width=80):
                    st.session_state[store] = False
                    st.rerun()
            else:
                if flex.button("Enable", key=f"enable_{store}", width=80):
                    st.session_state[store] = True
                    st.rerun()
        
            flex.markdown(f"**{store.replace('_', ' ').title()}** {'✅' if enabled else '❌'}")

        st.markdown("---")
        st.subheader("Retrievers")

        retrievers = []
        if st.session_state["text_store"]:
            retrievers.append("Vector Retriever")
        if st.session_state["table_store"]:
            retrievers.append("Table Retriever")
        if st.session_state["external_db_store"]:
            retrievers.append("SQL Retriever")

        if retrievers:
            st.markdown("**Enabled Retrievers:** " + ", ".join(retrievers))
        else:
            st.info("No retrievers active. Enable at least one store above.")

        if st.session_state["text_store"]:
            st.markdown("##### ✅ Vector Retriever")
            vector_top_k = st.number_input("Vector Retriever top_k", 1, 50, 5, 1)
        if st.session_state["table_store"]:
            st.markdown("##### ✅ Table Retriever")
        if st.session_state["external_db_store"]:
            st.markdown("##### ✅ SQL Retriever")

     
        st.markdown("---")
        st.subheader("Tasks")

        # QA task — always possible
        st.session_state["qa_task"] = st.checkbox(
            "Enable QA task",
            value=st.session_state.get("qa_task", True),
            key="qa_task_checkbox"
        )

        # Chart generation — allowed only if table/external DB store enabled
        chart_possible = st.session_state.get("table_store", False) or st.session_state.get("external_db_store", False)

        if not chart_possible and st.session_state.get("chart_task", False):
            st.session_state["chart_task"] = False  # auto-disable if dependency removed

        st.session_state["chart_task"] = st.checkbox(
            "Enable Chart Generation",
            value=st.session_state.get("chart_task", False),
            disabled=not chart_possible,
            key="chart_task_checkbox",
            help=None if chart_possible else "Requires Table or External DB store"
        )



        submitted = st.button("Create project", type="primary")
        if submitted:
            if not project_name:
                st.error("Project name is required.")
            else:
                cfg = ProjectConfig(
                    project_name=project_name,
                    persist_dir=persist_dir,
                    meta_conn_url=f"sqlite:///{persist_dir}/agenticrag.db",
                    chat_history_queue_size=chat_history_queue_size,
                    llm=LLMConfig(
                        provider=provider,
                        model=model,
                        api_key=api_key,
                    ),
                    stores=StoreFlags(
                        enable_text_store=st.session_state["text_store"],
                        enable_table_store=st.session_state["table_store"],
                        enable_external_db_store=st.session_state["external_db_store"],
                    ),
                    retrievers=RetrieverConfig(
                        enable_vector_retriever=st.session_state["text_store"],
                        vector_top_k=int(vector_top_k),
                        enable_table_retriever=st.session_state["table_store"],
                        enable_sql_retriever=st.session_state["external_db_store"],
                    ),
                    tasks=TaskConfig(
                        enable_qa_task=st.session_state["qa_task"],
                        enable_chart_task=st.session_state["chart_task"],
                    ),
                )

                os.makedirs(cfg.persist_dir, exist_ok=True)
                save_project_config(cfg)
                st.success(f"Project '{project_name}' created and loaded.")
                st.session_state["creating_new"] = False
                st.session_state["active_project"] = project_name
                st.rerun()
