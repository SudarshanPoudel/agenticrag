import inspect
from typing import Any, Dict
from pydantic import create_model

def generate_args_schema_from_method(method):
    """
    Generate a Pydantic model from a method's signature.
    """
    sig = inspect.signature(method)
    params = sig.parameters
    fields = {}

    for name, param in params.items():
        if name == 'self':
            continue
        param_type = param.annotation if param.annotation is not param.empty else str
        fields[name] = (param_type, ...)

    return create_model(f'{method.__name__}ArgsSchema', **fields)
