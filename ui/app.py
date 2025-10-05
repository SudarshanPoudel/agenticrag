import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
torch.classes.__path__ = []  # suppress torch dynamic class path

import streamlit as st
from ui.onboarding import onboarding_panel
from ui.agent_factory import get_agent_bundle
from ui.sections.chat import chat_section
from ui.sections.loader import loader_section
from ui.sections.stores import store_section

def main():
    st.set_page_config(page_title="AgenticRAG", layout="wide", initial_sidebar_state="expanded")
    with open("ui/style.css", "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    if "active_project" not in st.session_state:
        st.session_state["active_project"] = None
    if st.session_state["active_project"] is None:
        st.title("AgenticRAG Playground")
        st.markdown("*No project selected, please select one from the sidebar.*")
    else:
        st.title(f"AgenticRAG Playground: {st.session_state['active_project']}")
    
    with st.sidebar:
        st.markdown("### Project")
        if st.session_state["active_project"] is None:
            onboarding_panel()
            st.stop()
        else:
            st.success(f"Active: {st.session_state['active_project']}")
            if st.button("Switch project"):
                st.session_state["active_project"] = None
                st.session_state.pop("chat_messages", None)
                st.rerun()

    agent_bundle = get_agent_bundle(st.session_state["active_project"])
    if not agent_bundle:
        st.warning("Project config not found. Please re-create.")
        st.session_state["active_project"] = None
        st.rerun()


    tabs = []
    tabs.append("💬 Chat")
    # loaders shown only if any loader exists
    if any(agent_bundle.components.get(k) for k in ["text_loader", "table_loader", "external_db_connector"]):
        tabs.append("📥 Load")
    # stores shown if any store exists
    if any(agent_bundle.components.get(k) for k in ["meta_store", "text_store", "table_store", "external_db_store"]):
        tabs.append("📚 Stores")

    tab_objs = st.tabs(tabs)

    tab_index = 0
    with tab_objs[tab_index]:
        chat_section(agent_bundle)

    idx = 1
    if "📥 Load" in tabs:
        with tab_objs[idx]:
            loader_section(agent_bundle)
        idx += 1
    if "📚 Stores" in tabs:
        with tab_objs[idx]:
            store_section(agent_bundle)

    
if __name__ == "__main__":
    main()
