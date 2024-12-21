from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def handle_task(self, task):
        pass 


