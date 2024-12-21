import subprocess
from core.base_agent import BaseAgent 

class TerminalAgent(BaseAgent):
    def handle_task(self, task):
        if task.task_type != "run_command":
            return f"Unsupported task type: {task.task_type}"

        command = task.prompt
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return result.decode("utf-8")
        except subprocess.CalledProcessError as e:
            return f"Command failed with error: {e.output.decode('utf-8')}"

