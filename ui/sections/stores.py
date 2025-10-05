from narwhals import exclude
import streamlit as st
from agenticrag.types import MetaData, TextData, TableData, ExternalDBData, DataFormat

def store_section(agent_bundle):
    comps = agent_bundle.components
    meta_store = comps.get("meta_store")
    text_store = comps.get("text_store")
    table_store = comps.get("table_store")
    external_db_store = comps.get("external_db_store")

    # map format to store for convenience
    store_map = {
        DataFormat.TEXT: text_store,
        DataFormat.TABLE: table_store,
        DataFormat.EXTERNAL_DB: external_db_store
    }

    def handle_meta_update(old_row, new_row):
        """Propagate name changes to the relevant store"""
        if old_row.name != new_row.name:
            target_store = store_map.get(new_row.format)
            if target_store:
                for item in target_store.get_all():
                    if hasattr(item, "name") and item.name == old_row.name:
                        target_store.update(item.id, name=new_row.name)
        meta_store.update(old_row.id, description=new_row.description, source=new_row.source, name=new_row.name)

    def handle_meta_delete(row):
        """Delete corresponding entries in relevant store"""
        target_store = store_map.get(row.format)
        if target_store:
            for item in target_store.get_all():
                if hasattr(item, "name") and item.name == row.name:
                    target_store.delete(item.id)
        meta_store.delete(row.id)

    def render_meta_store():
        """Render editable Meta Store"""
        rows = meta_store.get_all()
        if not rows:
            st.write("No meta data yet.")
            return

        rows_dicts = [row.model_dump() for row in rows]
        st.markdown("### Meta Store")

        edited = st.data_editor(
            rows_dicts,
            width="stretch",
            disabled=["id", "format"],  # id/format not editable
            num_rows="fixed",           # no adding new rows
        )

        # Detect and apply edits
        for old, new in zip(rows, edited):
            if old != new:
                handle_meta_update(old, MetaData(**new))

        

    def render_store(name, store_obj):
        """Render non-meta store as read-only"""
        rows = store_obj.get_all() if store_obj else []
        with st.expander(name, expanded=False):
            if rows:
                rows_dicts = [row.model_dump() if hasattr(row, "model_dump") else row for row in rows]
                st.dataframe(rows_dicts, width="stretch")
            else:
                st.write("No data yet.")

    # --- Render Meta Store (editable & deletable) ---
    if meta_store:
        render_meta_store()

    # --- Render other stores (read-only) ---
    if text_store:
        render_store("Text Store", text_store)
    if table_store:
        render_store("Table Store", table_store)
    if external_db_store:
        render_store("External DB Store", external_db_store)

    if meta_store:
        rows = meta_store.get_all()
        st.markdown("<h4 style='margin-top: 2rem; color: rgb(255, 75, 75);'>Delete Store Entries</h3>", unsafe_allow_html=True)
        delete_ids = [f"{row.id} : {row.name}" for row in rows]
        if delete_ids:
            selected = st.selectbox("Select entry to delete", delete_ids, index=None, placeholder="Choose entry...")
            if selected:
                selected_id = selected.split(" : ")[0]
                selected_row = next((r for r in rows if str(r.id) == selected_id), None)
                if selected_row:
                    st.warning(f"Are you sure you want to delete '{selected_row.name}'?")
                    if st.button("Confirm Delete", type="primary"):
                        handle_meta_delete(selected_row)
                        st.success("Deleted successfully.")
                        st.rerun()
                
        else:
            st.info("No entries to delete.")