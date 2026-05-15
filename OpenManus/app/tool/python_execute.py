import multiprocessing
import sys
import base64
from io import StringIO
from typing import Dict

from app.tool.base import BaseTool


class PythonExecute(BaseTool):
    """A tool for executing Python code with timeout and safety restrictions."""

    name: str = "python_execute"
    description: str = "Executes Python code string. Supports matplotlib plotting with automatic image output. Note: Only print outputs are visible, function return values are not captured. Use print statements to see results."
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "The Python code to execute.",
            },
        },
        "required": ["code"],
    }

    def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
        original_stdout = sys.stdout
        try:
            output_buffer = StringIO()
            sys.stdout = output_buffer
            
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            def show_plot():
                buffer = StringIO()
                plt.savefig(buffer, format='png', bbox_inches='tight')
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close('all')
                return f'[PLOT_IMAGE]data:image/png;base64,{image_base64}[PLOT_IMAGE]'
            
            safe_globals['plt'] = plt
            safe_globals['matplotlib'] = matplotlib
            safe_globals['show_plot'] = show_plot
            
            exec(code, safe_globals, safe_globals)
            
            output = output_buffer.getvalue()
            if 'plt' in safe_globals:
                try:
                    plot_output = show_plot()
                    if plot_output:
                        output += '\n' + plot_output
                except:
                    pass
            
            result_dict["observation"] = output
            result_dict["success"] = True
        except Exception as e:
            result_dict["observation"] = str(e)
            result_dict["success"] = False
        finally:
            sys.stdout = original_stdout

    async def execute(
        self,
        code: str,
        timeout: int = 30,
    ) -> Dict:
        """
        Executes the provided Python code with a timeout.

        Args:
            code (str): The Python code to execute.
            timeout (int): Execution timeout in seconds.

        Returns:
            Dict: Contains 'output' with execution output or error message and 'success' status.
        """

        with multiprocessing.Manager() as manager:
            result = manager.dict({"observation": "", "success": False})
            if isinstance(__builtins__, dict):
                safe_globals = {"__builtins__": __builtins__}
            else:
                safe_globals = {"__builtins__": __builtins__.__dict__.copy()}
            
            safe_globals['__name__'] = '__main__'
            safe_globals['__file__'] = '<sandbox>'
            
            proc = multiprocessing.Process(
                target=self._run_code, args=(code, result, safe_globals)
            )
            proc.start()
            proc.join(timeout)

            if proc.is_alive():
                proc.terminate()
                proc.join(1)
                return {
                    "observation": f"Execution timeout after {timeout} seconds",
                    "success": False,
                }
            return dict(result)
