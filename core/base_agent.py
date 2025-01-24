from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def handle_task(self, task):
        """处理任务的抽象方法"""
        pass 


