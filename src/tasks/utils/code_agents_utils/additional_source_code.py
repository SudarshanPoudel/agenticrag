# This script contains a additional source code to be appended at e2b executor (like our own tool codes)
# Tools/Functions like final_answer() or explain_chart() That I want my agent to use without needing to generate code on it's own are here.

from .helper import get_source
from .extract_chart_data import format_chart_info, extract_chart_data

def get_additional_code(agent_name:str)->str:
    """
    This utility function returns the additional source code for any code agents to be appended before 
    any e2b execution, like code for our own tools or default tools we maintained in the prompt. 
    """
    additional_code = get_source(final_answer) + "\n" # final_answer() is appended to all agents

    if agent_name == 'ChartQueryAgent': 
        additional_code += get_source(explain_chart) + '\n' + get_source(format_chart_info) + '\n' + get_source(extract_chart_data)
    
    return additional_code
    
def final_answer(answer:str):
    "This method prints the final answer"
    print(answer)


def explain_chart(input_obj):
    try:
        ax = input_obj.gca()  # If it's a plt object
    except AttributeError:
        ax = input_obj
    chart_info = extract_chart_data(ax)
    print(format_chart_info(chart_info))
