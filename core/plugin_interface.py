from abc import ABC, abstractmethod

class PluginInterface(ABC):
    @abstractmethod
    def activate(self):
        pass 

    @abstractmethod
    def deactivate(self):
        pass 
