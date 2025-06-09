import json
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProblem(ABC):
    """
    Abstract base class for all problem types.
    Defines common interface for problem instances.
    """
    def __init__(self, problem_id: str, parameters: Dict[str, Any]):
        self.problem_id = problem_id
        self.parameters = parameters

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Converts the problem instance to a dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a problem instance from a dictionary."""
        pass

    def to_jsons(self) -> str:
        """Serializes the problem instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=4)

    @classmethod
    def from_jsons(cls, json_str: str):
        """Deserializes a problem instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_json(self, filepath: str):
        """Saves the problem instance to a JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_jsons())

    @classmethod
    def from_json(cls, filepath: str):
        """Loads a problem instance from a JSON file."""
        with open(filepath, 'r') as f:
            json_str = f.read()
        return cls.from_jsons(json_str)

    def __repr__(self):
        return f"{self.__class__.__name__}(id='{self.problem_id}')"

    def __str__(self):
        return f"Problem ID: {self.problem_id}\nParameters: {self.parameters}"

    @abstractmethod
    def _normalized_data(self):
        """Return a canonical, hashable representation of the problem-defining data. Subclasses must implement."""
        pass

    def __hash__(self):
        # Hash the normalized, canonical data
        norm = self._normalized_data()
        norm_json = json.dumps(norm, sort_keys=True)
        return hash(norm_json)