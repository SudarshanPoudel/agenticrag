import inspect
from pydantic import BaseModel, create_model

def generate_args_schema_from_method(method):
    # Get the method signature
    sig = inspect.signature(method)
    
    # Extract the parameters
    params = sig.parameters
    
    # Dynamically create the schema class
    fields = {}
    
    for param_name, param in params.items():
        if param_name == 'self':
            continue  # Skip 'self' in method signatures
        # Use the parameter's type annotation if available
        param_type = param.annotation if param.annotation is not param.empty else str
        fields[param_name] = (param_type, ...)  # Required fields, so use '...'
    
    # Add the 'name' field if you want to include it in the dynamically created model
    fields['name'] = (str, ...)  # For example, include name field as required

    # Create and return a dynamic Pydantic model
    return create_model(f'{method.__name__}ArgsSchema', **fields)
