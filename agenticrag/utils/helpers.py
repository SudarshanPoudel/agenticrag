from typing import Dict, List, Union
import re
import json
import ast

from pydantic import BaseModel


def format_tool_metadata(tools_dict):
    tool_descriptions = []
    for name, tool in tools_dict.items():
        params = tool.args.schema().get("properties", {})
        param_str = "\n".join([f"    - `{p}`: {details.get('description', 'No description')}" for p, details in params.items()])
        tool_descriptions.append(f"**{name}**: {tool.description}\n  Parameters:\n{param_str}")
    return "\n\n".join(tool_descriptions)


def format_datasets(datasets):
    result = ""
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

def _extract_blocks_from_response(
    content: str,
    start_sep: str,
    end_sep: str,
    multiple: bool = False
) -> Union[List[str], str]:
    pattern = re.escape(start_sep) + r"(.*?)" + re.escape(end_sep)
    matches = re.findall(pattern, content, re.DOTALL)
    extracted = [match.strip() for match in matches]
    return extracted if multiple else (extracted[0] if extracted else "")

def _extract_json_like_blocks(text: str) -> list[str]:
    blocks, stack, start = [], [], None
    for i, ch in enumerate(text):
        if ch in "{[":
            if not stack:
                start = i
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    blocks.append(text[start:i+1])
                    start = None
    return blocks


def extract_json_blocks(
    content: str,
    multiple: bool = False
) -> Union[List[dict], dict]:
    import ast

    def try_parse_all_blocks(candidates):
        parsed = []
        for block in candidates:
            try:
                if isinstance(block, str) and block.startswith('"') and block.endswith('"'):
                    block = ast.literal_eval(block)  # unescape stringified JSON
                parsed.append(json.loads(block))
            except Exception:
                continue
        return parsed

    # 0. First try direct parsing — content *is* a full JSON string
    try:
        direct = json.loads(content)
        return direct if not multiple else [direct]
    except Exception:
        pass

    # 1. Try ```json fenced blocks
    blocks = _extract_blocks_from_response(content, "```json", "```", multiple=True)

    # 2. Try to extract all {...} or [...] using greedy matching
    if not blocks:
        blocks = _extract_json_like_blocks(content)


    # 3. Try finding escaped stringified JSON
    if not blocks:
        escaped_match = re.search(r'"({\\n.*?})"', content)
        if escaped_match:
            try:
                unescaped = bytes(escaped_match.group(1), "utf-8").decode("unicode_escape")
                blocks = [unescaped]
            except Exception:
                pass

    if not blocks:
        return [] if multiple else {}

    parsed = try_parse_all_blocks(blocks)
    return parsed if multiple else (parsed[0] if parsed else {})



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


class FinalAnswerArgsSchema(BaseModel):
    answer: str 