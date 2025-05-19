import os
from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from agenticrag.tasks.base import BaseTask
from agenticrag.tasks.utils.prompts import CHART_GENERATION_PROMPT
from agenticrag.loaders.utils.extract_csv_structure import extract_csv_structure
from agenticrag.utils.local_sandbox_executor import LocalPythonExecutor
from agenticrag.utils.helpers import parse_code_blobs
from agenticrag.utils.llm import get_default_llm
from agenticrag.utils.logging_config import setup_logger
from agenticrag.types.exceptions import TaskExecutionError

logger = setup_logger(__name__)


class ChartGenerationTask(BaseTask):
    """
    Task that generates charts from CSV data based on a user query.
    It uses an LLM to generate Python code, then safely executes the code to create the chart.
    """

    def __init__(self, llm:BaseChatModel = None, save_charts_at=".agenticrag_data/charts"):
        self.llm = llm or get_default_llm()
        self.save_charts_at = save_charts_at

    @property
    def name(self):
        return "chart_generation"

    @property
    def description(self):
        return (
            "This task takes a CSV file path and a chart query, "
            "generates Python code via LLM to create the chart, "
            "executes it, and returns the chart's saved path."
        )

    def execute(self,  query: str, file_path: str) -> str:
        """
        Generate a chart from a CSV file based on a natural language query.

        Uses an LLM to generate Python code for the chart, executes it 
        and returns the path to the saved chart image.

        Args:
            file_path (str): Path to the input CSV file.
            query (str): Natural language query describing the desired chart.
        """
        try:
            logger.info(f"Starting chart generation for: {file_path}, query: '{query}'")

            structure = extract_csv_structure(file_path)
            output_path = f"{self.save_charts_at}/"
            os.makedirs(output_path, exist_ok=True)

            base_messages = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(CHART_GENERATION_PROMPT),
                    HumanMessagePromptTemplate.from_template(
                        "Query: {query}\nFile Path: {file_path}\nOutput Folder: {output_path}\nFile Structure: {structure}"
                    ),
                ]
            ).format_messages(
                query=query,
                file_path=file_path,
                output_path=output_path,
                structure=structure,
            )
            
            executor = LocalPythonExecutor(
                additional_authorized_imports=["pandas", "seaborn", "matplotlib"]
            )
            messages = base_messages.copy()
            max_retries = 10

            for attempt in range(max_retries):
                logger.debug(f"LLM attempt {attempt + 1}")
                try:
                    llm_response = self.llm.invoke(messages).content
                    code = parse_code_blobs(llm_response)
                    chart_path = executor(code)
                    logger.info(f"Chart successfully saved at: {chart_path}")
                    return f"Relevant chart saved at {chart_path}"
                except ValueError as e:
                    logger.info(f"Code parsing failed: {e}")
                    messages.append(HumanMessage(content=f"Code parsing error: {e}"))
                except Exception as e:
                    logger.info(f"Code execution failed: {e}")
                    messages.append(HumanMessage(content=f"Code execution error: {e}"))

            return "Failed to generate chart after multiple attempts"

        except Exception as e:
            logger.error(f"ChartGenerationTask error: {e}")
            raise TaskExecutionError(str(e)) from e
