from core.base_agent import BaseAgent

class LLMAgent(BaseAgent):
    def __init__(self, llm_provider):
        self.llm = llm_provider 

    def handle_task(self, task):
        if task.task_type != "llm_query":
            return f"Unsupported task type: {task.task_type}"

        response = self.llm.generate_response(task.prompt)
        return response 
