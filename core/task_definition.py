class Task:
    def __init__(self, task_type, prompt, **kwargs):
        self.task_type = task_type 
        self.prompt = prompt 
        self.kwargs = kwargs 
