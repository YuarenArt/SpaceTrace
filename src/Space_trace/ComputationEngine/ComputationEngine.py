from abc import ABC, abstractmethod

class ComputationEngine(ABC):
    @abstractmethod
    def compute_points(self, data, config):

        pass