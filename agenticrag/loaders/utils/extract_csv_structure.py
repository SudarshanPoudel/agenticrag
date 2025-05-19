import json

def extract_csv_structure(file_path:str)->str:
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("Pandas is required to extract CSV structure, install it via `pip install pandas`")
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
    
    return basic_json
    