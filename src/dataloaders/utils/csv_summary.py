import pandas as pd
import json
from langchain_core.messages import SystemMessage
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate

from ...utils.llm import DEFAULT_LLM
from .summary_prompt import SUMMARIZATION_PROMPT

def summarize_csv(file_path:str, metadata:str="", use_llm: bool = True)->str:
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported file format!")
    
    basic_info = {
        "total_rows": df.shape[0],
        "columns": []
    }

    for col in df.columns:
        example_values = df[col].dropna().head(5).tolist()
        # Check if the column is numerical
        if pd.api.types.is_numeric_dtype(df[col]):
            column_info = {
                "column_name": col,
                "data_type": str(df[col].dtype),
                "range": f"{df[col].min()} to {df[col].max()}", 
                "example_values": example_values or ['None'],
                "null_values": str(df[col].isna().sum())
            }
        else:
            column_info = {
                "column_name": col,
                "data_type": str(df[col].dtype),
                "unique_values": df[col].nunique(),
                "example_values": example_values or ['None'],
                "null_values": str(df[col].isna().sum())
            }
        basic_info["columns"].append(column_info)
        
    basic_json = json.dumps(basic_info, indent=4)
    
    if not use_llm:
        return basic_json
    
    message_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                SUMMARIZATION_PROMPT
            ),
            HumanMessagePromptTemplate.from_template(
                """Metadata: {metadata} \nBasic JSON: \n```json \n{basic_json}\n```"""
            )
        ]
    )
    messages = message_template.format_messages(
        metadata=metadata,
        basic_json=basic_json
    )
    summary = DEFAULT_LLM.invoke(messages)
    return summary.content
    