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


def format_dataset_info(datasets):
    result = "Selected Datasets:-\n"
    for dataset_info in datasets:
        result += f"""
- Name: {dataset_info.name}
- Description: {dataset_info.description}

"""
    return result

def extract_blocks_from_llm_response(content: str, start_sep: str, end_sep: str, multiple: bool = False) -> Union[List[str], str]:
    """
    Extracts blocks of text enclosed between given start and end separators.
    """
    pattern = re.escape(start_sep) + r"(.*?)" + re.escape(end_sep)
    matches = re.findall(pattern, content, re.DOTALL)
    extracted = [match.strip() for match in matches]
    return extracted if multiple else (extracted[0] if extracted else "")

def extract_json_blocks(content: str, multiple: bool = False) -> Union[List[dict], dict]:
    """
    Extracts and parses JSON blocks from an LLM response.
    """
    json_blocks = extract_blocks_from_llm_response(content, "```json", "```", multiple=multiple)
    if not json_blocks:
        return [] if multiple else {}
    
    parsed_jsons = []
    for block in (json_blocks if isinstance(json_blocks, list) else [json_blocks]):
        try:
            parsed_jsons.append(json.loads(block))
        except json.JSONDecodeError:
            print("Error: Invalid JSON format")
            print(block)
    
    return parsed_jsons if multiple else parsed_jsons[0] if parsed_jsons else {}



def parse_code_blobs(code_blob: str) -> str:
    """Parses the LLM's output to get any code blob inside. Will return the code directly if it's code."""
    pattern = r"```(?:py|python)?\n(.*?)\n```"
    matches = re.findall(pattern, code_blob, re.DOTALL)
    if len(matches) == 0:
        try:  # Maybe the LLM outputted a code blob directly
            ast.parse(code_blob)
            return code_blob
        except SyntaxError:
            pass
          
        raise ValueError(
            f"""
The code blob is invalid, because the regex pattern {pattern} was not found in {code_blob=}. Make sure to include code with the correct pattern, for instance:
Thoughts: Your thoughts
Code:
```py
# Your python code here
```<end_code>""".strip()
        )
    return "\n\n".join(match.strip() for match in matches)
