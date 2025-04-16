import os
from dotenv import load_dotenv
load_dotenv()

import base64
from typing import List, Dict, TypedDict
from e2b_code_interpreter import Sandbox

class RunResult(TypedDict):
    output: str
    error: str
    charts: List[str]


class E2BExecutor:
    """
    This is a utility class that allows us to setup our own sandbox environment with additional imports, code and files and run the code.
    """
    def __init__(
        self,
        additional_imports: List[str] = [],
        additional_files: List[str] = [],
        save_plots_at: str = None,
    ):
        self.sbx = Sandbox(timeout=3600)
        self.handle = self.sbx.files.watch_dir("/home/user")
        self.save_plots_at = save_plots_at
        if len(additional_imports) > 0:
            self.sbx.commands.run("pip install " + " ".join(additional_imports))

        for file_path in additional_files:
            with open(file_path, "rb") as file:
                self.sbx.files.write(file_path, file)

    def run(self, code: str) -> RunResult:
        execution = self.sbx.run_code(code)
        if execution.error:
            execution_logs = "\n".join([str(log) for log in execution.logs.stdout])
            logs = execution_logs
            logs += "Executing code yielded an error:"
            logs += execution.error.name
            logs += execution.error.value
            logs += execution.error.traceback
            return {
                'output': None,
                'error': logs,
                'charts': []
            }
        
        # Check for saved charts
        events = self.handle.get_new_events() 
        charts = []
        for event in events: 
            if event.name.endswith('.png') or event.name.endswith('.jpeg'):
                os.makedirs(self.save_plots_at, exist_ok=True)
                save_path = f"{self.save_plots_at}/{event.name}" if len(self.save_plots_at) > 0 else event.name
                with open(save_path, 'wb') as f:
                    f.write(self.sbx.files.read(event.name, format='bytes'))
                    charts.append(save_path)
                
        output =  "\n".join(output.strip() for output in execution.logs.stdout) or ''
        
        return {
            'output': output,
            'error': None,
            'charts': charts,
        }
