from click import prompt
from sqlalchemy import create_engine, inspect
import json
from agenticrag.core.llm_client import LLMClient
from agenticrag.types.core import BaseMessage
from agenticrag.utils.logging_config import setup_logger
from agenticrag.utils.llm import get_default_llm
logger = setup_logger(__name__)


def extract_db_structure(connection_url):
    engine = create_engine(connection_url)
    inspector = inspect(engine)

    db_structure = {}

    for table_name in inspector.get_table_names():
        table_info = {
            "columns": [],
            "primary_keys": inspector.get_pk_constraint(table_name)["constrained_columns"],
            "foreign_keys": [],
            "indexes": []
        }

        for column in inspector.get_columns(table_name):
            table_info["columns"].append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"]
            })

        for fk in inspector.get_foreign_keys(table_name):
            table_info["foreign_keys"].append({
                "column": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"]
            })

        for idx in inspector.get_indexes(table_name):
            table_info["indexes"].append({
                "name": idx["name"],
                "columns": idx["column_names"],
                "unique": idx.get("unique", False)
            })

        db_structure[table_name] = table_info

    return json.dumps(db_structure, indent=2)

def summarize_db(db_structure: str, llm: LLMClient):
    # Generate description
    prompt = BaseMessage(
        content=f"""Based on the structure of the database, generate a short description (3-4 lines) explaining what this database is about.
        The description should provide an overall idea about what type of data is available in the database.
        
        {db_structure}"""
    )
    desc = llm.invoke(prompt).content

    logger.debug(f"Description generated for Database: {desc}")
    return desc