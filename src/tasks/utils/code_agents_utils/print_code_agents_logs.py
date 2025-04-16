from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from .helper import parse_code_blobs

def print_code_agents_logs(iteration, response, query):
    """
    Logs intermediate results with rich formatting using custom hex colors.
    """
    console = Console()
    # Define custom colors
    query_color = "#00BFFF"  # DeepSkyBlue
    iteration_color = "#FFD700"  # Gold
    thought_color = "#D3D3D3"  # LightGray
    output_color = "#32CD32"  # LimeGreen
    border_color = "#1E90FF"  # DodgerBlue
    code_border_color = "#FF4500"  # OrangeRed
    
    if iteration == 1:
        console.print(Panel(Text(query, style=f"bold {query_color}"), title=f"[bold {query_color}]Query[/bold {query_color}]", border_style=border_color, expand=False))
    
    console.print(f"\n[bold {iteration_color}]Iteration {iteration}[/bold {iteration_color}]\n")
    
    # Extract thought and code separately
    content = response['llm_response'].content.strip()
    
    if "**Thought:**" in content and "**Code:**" in content:
        thought, code = content.split("**Code:**", 1)
        thought = thought.replace("**Thought:**", "").strip()
        console.print(Panel(Text(thought, style=f"italic {thought_color}"), title=f"[bold {thought_color}]Thought[/bold {thought_color}]", border_style=thought_color, expand=False))
        
        code = parse_code_blobs(code)
    else:
        code = parse_code_blobs(content)
    
    # Format code block with line numbers and padding
    syntax = Syntax(code, "python", theme="monokai", line_numbers=True, padding=(1, 1))
    console.print(Panel(syntax, title=f"[bold {code_border_color}]Code[/bold {code_border_color}]", border_style=code_border_color, expand=False))
    
    # Print execution result
    output = response['output'].strip()
    
    console.print(Panel(Text(output, style=f"bold {output_color}"), title=f"[bold {output_color}]Output[/bold {output_color}]", border_style=output_color, expand=False))
    if len(response['charts']) > 0:
        charts = "Charts = " + ", ".join(response['charts']).strip()
        console.print(Panel(Text(charts, style=f"bold {output_color}"), title=f"[bold {output_color}]Charts[/bold {output_color}]", border_style=output_color, expand=False))
