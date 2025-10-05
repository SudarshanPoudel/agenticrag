import streamlit as st
import tempfile

def loader_section(agent_bundle):

    comps = agent_bundle.components
    text_loader = comps.get("text_loader")
    table_loader = comps.get("table_loader")
    external_db_connector = comps.get("external_db_connector")

    available_loaders = []
    if text_loader:
        available_loaders.extend(["📄 Load PDF", "🌐 Load Website"])
    if table_loader:
        available_loaders.append("📊 Load CSV")
    if external_db_connector:
        available_loaders.append("🗄️ Connect External DB")

    if not available_loaders:
        st.warning("No loader components found in this agent.")
        return

    col1, col2 = st.columns([1, 4])

    with col1:
        st.markdown("### Sources")
        selected_loader = st.radio(
            "Select data source",
            available_loaders,
            label_visibility="collapsed",
            index=0,
            key="loader_select",
        )

    with col2:
        st.markdown(f"### {selected_loader[2:]}")

        # --- PDF Loader ---
        if selected_loader == "📄 Load PDF" and text_loader:
            pdf_name = st.text_input("PDF name (optional)", key="pdf_name")
            uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_upload")
            auto_desc = st.toggle("Auto-generate description", value=True, key="pdf_auto_desc")
            description = None if auto_desc else st.text_area("Description", key="pdf_desc")

            if st.button("Load PDF", type='primary'):
                if not uploaded_pdf:
                    st.error("Please upload a PDF file first!")
                else:
                    with st.spinner("Uploading PDF..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_pdf.read())
                            try:
                                text_loader.load_pdf(
                                    tmp.name,
                                    name=pdf_name or uploaded_pdf.name,
                                    source="UPLOADED: " + uploaded_pdf.name,
                                    description=description,
                                )
                                st.success(f"Loaded: {uploaded_pdf.name}")
                            except Exception as e:
                                st.error(f"Failed to load PDF: {e}")

        # --- Website Loader ---
        elif selected_loader == "🌐 Load Website" and text_loader:
            website_name = st.text_input("Website name (optional)", key="web_name")
            website_url = st.text_input("Website URL", key="web_input")
            auto_desc = st.toggle("Auto-generate description", value=True, key="web_auto_desc")
            description = None if auto_desc else st.text_area("Description", key="web_desc")

            if st.button("Load Website", type='primary'):
                if not website_url:
                    st.error("Please enter the website URL!")
                else:
                    with st.spinner("Loading website..."):
                        try:
                            text_loader.load_web(
                                website_url,
                                name=website_name,
                                description=description,
                            )
                            st.success(f"Loaded: {website_url}")
                        except Exception as e:
                            st.error(f"Failed to load website: {e}")

        # --- CSV Loader ---
        elif selected_loader == "📊 Load CSV" and table_loader:
            csv_name = st.text_input("CSV name (optional)", key="csv_name")
            uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], key="csv_upload")
            auto_desc = st.toggle("Auto-generate description", value=True, key="csv_auto_desc")
            description = None if auto_desc else st.text_area("Description", key="csv_desc")

            if st.button("Load CSV", type='primary'):
                if not uploaded_csv:
                    st.error("Please upload a CSV file first!")
                else:
                    with st.spinner("Uploading CSV..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                            tmp.write(uploaded_csv.read())
                            try:
                                table_loader.load_csv(
                                    tmp.name,
                                    name=csv_name or uploaded_csv.name,
                                    source="UPLOADED: " + uploaded_csv.name,
                                    description=description,
                                )
                                st.success(f"Loaded: {uploaded_csv.name}")
                            except Exception as e:
                                st.error(f"Failed to load CSV: {e}")

        # --- External DB Connector ---
        elif selected_loader == "🗄️ Connect External DB" and external_db_connector:
            db_name = st.text_input("Database name", key="db_name")
            db_url = st.text_input("Database connection URL", key="db_input")
            auto_desc = st.toggle("Auto-generate description", value=True, key="db_auto_desc")
            description = None if auto_desc else st.text_area("Description", key="db_desc")

            if st.button("Connect DB", type='primary'):
                if not db_name or not db_url:
                    st.error("Please provide both database name and connection URL!")
                else:
                    with st.spinner("Connecting to DB..."):
                        try:
                            external_db_connector.connect_db(
                                name=db_name,
                                connection_url=db_url,
                                description=description,
                            )
                            st.success(f"Connected to: {db_url}")
                        except Exception as e:
                            st.error(f"Failed to connect: {e}")
