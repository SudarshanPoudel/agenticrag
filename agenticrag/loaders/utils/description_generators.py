import re
from agenticrag.core.llm_client import LLMClient
from agenticrag.types.core import BaseMessage
from agenticrag.utils.logging_config import setup_logger

logger = setup_logger(__name__)

def preprocess_text(text):
    """Normalize text and split into sentences."""
    text = re.sub(r'\s+', ' ', text.strip())  # Remove extra spaces/newlines
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)  # Split on sentence boundaries
    return sentences

def select_representative_sentences(sentences, num_parts=10, sentences_per_part=3):
    """Select representative sentences uniformly across the document."""
    total_sentences = len(sentences)
    step = max(1, total_sentences // num_parts)  # Step size to ensure uniform distribution

    selected_sentences = []
    for i in range(num_parts):
        start_idx = i * step
        selected_sentences.extend(sentences[start_idx:start_idx + sentences_per_part])

    return selected_sentences

def text_to_desc(text, llm: LLMClient):
    """Generate a short description using selected sentences."""
    sentences = preprocess_text(text)
    selected_sentences = select_representative_sentences(sentences)
    summary_text = " ".join(selected_sentences)

    prompt = BaseMessage(
        content=f"""
        Given the following representative sentences from a document:
        {summary_text}
        Generate a short description (3-4 lines) explaining what this document is about.
        The description should provide an overall idea without summarizing individual details.
        """,
    )

    desc = llm.invoke(prompt).content
    logger.debug(f"Description generated for text as : {desc}")
    return desc


def csv_to_desc(filepath, llm: LLMClient):
    """Generate a short description of a CSV file based on its header and sample data."""
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("Pandas is required to use generate tabular files description, install it via `pip install pandas`")
    
    df = pd.read_csv(filepath, nrows=5)  # Read first 5 rows for context
    column_names = df.columns.tolist()
    sample_data = df.head(3).to_dict(orient="records") 

    # Create prompt
    prompt = BaseMessage(
        content=f"""
        The following CSV file contains data with the columns:
        {", ".join(column_names)}
        Here are some sample rows:
        {sample_data}
        
        Based on this, generate a short description (3-4 lines) explaining what this dataset is about.
        The description should provide an overall idea without summarizing individual rows.
        """,
    )

    # Generate description
    desc = llm.invoke(prompt).content

    logger.debug(f"Description generated for CSV: {desc}")
    return desc