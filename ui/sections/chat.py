import re
import time
import streamlit as st

def chat_section(agent_bundle):
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "pending_request" not in st.session_state:
        st.session_state["pending_request"] = None

    # Make the chat history a fixed-height, scrollable container
    chat_scroller = st.container(height=460, border=False, gap=None)  # scrolls internally when overflowing
    input_footer = st.container()  # keep input outside to avoid page growth

    with chat_scroller:
        for msg in st.session_state["chat_messages"]:
            role = msg.get("role", "assistant")
            content = msg.get("content", "")
            meta = msg.get("meta", "")

            if role in ("user", "human"):
                with st.chat_message("user", avatar=":material/account_circle:"):
                    st.markdown(content)
            else:
                match = re.search(r'!\[.*?\]\((.*?)\)', content)
                cleaned = re.sub(r'!\[.*?\]\((.*?)\)', '', content).strip()

                with st.chat_message("assistant", avatar=":material/smart_toy:"):
                    st.markdown(cleaned)
                    if match:
                        st.image(match.group(1))
                    if meta:
                        st.caption(meta)

    # Input remains outside the scrollable history
    with input_footer:
        prompt = st.chat_input("Ask your question...")  # native chat input
        if prompt:
            st.session_state["chat_messages"].append({
                "role": "user",
                "content": prompt,
                "meta": ""
            })
            st.session_state["pending_request"] = prompt
            st.rerun()

    if st.session_state["pending_request"]:
        # Render loading and response inside the messages container so it appears in history
        with chat_scroller:
            loading_container = st.chat_message("assistant", avatar=":material/smart_toy:").empty()
            with loading_container.container():
                with st.spinner("Thinking...", show_time=True):
                    prompt_text = st.session_state["pending_request"]
                    response = agent_bundle.agent.invoke(prompt_text)

        md = response.content if hasattr(response, "content") else str(response)
        extra_bits = []
        if getattr(response, "datasets", None):
            ds_part = "Datasets: " + "; ".join([f"{ds.name}" for ds in response.datasets])
            extra_bits.append(ds_part)
        if getattr(response, "tasks", None):
            tk_part = "Tasks: " + "; ".join([f"{task.__class__.__name__}" for task in response.tasks])
            extra_bits.append(tk_part)
        meta_line = (" | ".join(extra_bits)) if extra_bits else ""

        st.session_state["chat_messages"].append({
            "role": "assistant",
            "content": md,
            "meta": meta_line,
        })
        st.session_state["pending_request"] = None
        st.rerun()
