from typing import List, Union
import re
import json
import ast


def format_tool_metadata(tools_dict):
    tool_descriptions = []
    for name, tool in tools_dict.items():
        params = tool.args_schema.schema().get("properties", {})
        param_str = "\n".join([f"    - `{p}`: {details.get('description', 'No description')}" for p, details in params.items()])
        tool_descriptions.append(f"**{name}**: {tool.description}\n  Parameters:\n{param_str}")
    return "\n\n".join(tool_descriptions)


def format_datasets(datasets):
    result = "Selected Datasets:-\n"
    for dataset in datasets:
        result += f"""
- Name: {dataset.name}
- Description: {dataset.description}

"""
    return result

def extract_blocks_from_llm_response(content: str, start_sep: str, end_sep: str, multiple: bool = False) -> Union[List[str], str]:
    """
    Extract text blocks between two separators.
    """
    pattern = re.escape(start_sep) + r"(.*?)" + re.escape(end_sep)
    matches = re.findall(pattern, content, re.DOTALL)
    blocks = [m.strip() for m in matches]
    return blocks if multiple else (blocks[0] if blocks else "")

def extract_json_blocks(content: str, multiple: bool = False) -> Union[List[dict], dict]:
    """
    Extract and parse JSON blocks from a string.
    """
    blocks = extract_blocks_from_llm_response(content, "```json", "```", multiple)
    if not blocks:
        return [] if multiple else {}

    parsed = []
    for block in (blocks if isinstance(blocks, list) else [blocks]):
        try:
            parsed.append(json.loads(block))
        except json.JSONDecodeError:
            print("Error: Invalid JSON format")
            print(block)

    return parsed if multiple else parsed[0] if parsed else {}

def parse_code_blobs(blob: str) -> str:
    """
    Extract code blocks from a string. If no block is found, attempts to validate the string as code.
    """
    pattern = r"```(?:py|python)?\n(.*?)\n```"
    matches = re.findall(pattern, blob, re.DOTALL)
    
    if matches:
        return "\n\n".join(m.strip() for m in matches)

    try:
        ast.parse(blob)
        return blob
    except SyntaxError:
        raise ValueError(f"""
The code blob is invalid, because the regex pattern {pattern} was not found in {blob=}. Make sure to include code with the correct pattern, for instance:
Thoughts: Your thoughts
Code:
```py
# Your python code here
```<end_code>""".strip())
