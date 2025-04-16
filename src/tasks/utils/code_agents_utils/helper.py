import ast
import re
import inspect
import textwrap
import json

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


def get_source(obj) -> str:
    """
    This utility class is taken from smolagents.
    Get the source code of a class or callable object (e.g.: function, method).
    First attempts to get the source code using `inspect.getsource`.
    In a dynamic environment (e.g.: Jupyter, IPython), if this fails,
    falls back to retrieving the source code from the current interactive shell session.
    """
    if not (isinstance(obj, type) or callable(obj)):
        raise TypeError(f"Expected class or callable, got {type(obj)}")

    inspect_error = None
    try:
        return textwrap.dedent(inspect.getsource(obj)).strip()
    except OSError as e:
        # let's keep track of the exception to raise it if all further methods fail
        inspect_error = e
    try:
        import IPython

        shell = IPython.get_ipython()
        if not shell:
            raise ImportError("No active IPython shell found")
        all_cells = "\n".join(shell.user_ns.get("In", [])).strip()
        if not all_cells:
            raise ValueError("No code cells found in IPython session")

        tree = ast.parse(all_cells)
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == obj.__name__:
                return textwrap.dedent("\n".join(all_cells.split("\n")[node.lineno - 1 : node.end_lineno])).strip()
        raise ValueError(f"Could not find source code for {obj.__name__} in IPython history")
        # IPython is not available, let's just raise the original inspect error
        raise inspect_error
    except ValueError as e:
        # IPython is available but we couldn't find the source code, let's raise the error
        raise e from inspect_error


def parse_json_string(input_string):
    cleaned_input = re.sub(r"```json[\n\r]*|```[\n\r]*", "", input_string).strip()
    if not cleaned_input:
        return {}
    try:
        parsed_json = json.loads(cleaned_input)
        return parsed_json
    except json.JSONDecodeError:
        return {}


def parse_markdown_string(input_string):
    cleaned_input = re.sub(r"```markdown[\n\r]*|```[\n\r]*", "", input_string).strip()
    if cleaned_input:
        return cleaned_input
    return input_string


def encode_markdown_image_urls(markdown: str) -> str:
    # Regex pattern to match Markdown image syntax
    pattern = r"(!\[[^\]]*\]\(([^)]+)\))"
    def replace_spaces(match):
        full_match = match.group(1)  # Full Markdown image syntax
        url = match.group(2)  # Extract URL
        updated_url = url.replace(" ", "%20")  # Replace spaces
        return full_match.replace(url, updated_url)  # Replace in original match
    return re.sub(pattern, replace_spaces, markdown)
