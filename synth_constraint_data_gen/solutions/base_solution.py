import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class SolutionStatus:
    """Enum-like class for solution status."""
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    NOT_SOLVED = "NOT_SOLVED"
    UNKNOWN = "UNKNOWN"

class BaseSolution(ABC):
    """
    Abstract base class for all problem solution types.
    Defines common interface for solution instances.
    """
    def __init__(self, problem_id: str, status: str = SolutionStatus.NOT_SOLVED, optimal_value: Optional[Any] = None):
        """
        Initializes the base solution.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (str): The status of the solution (e.g., OPTIMAL, FEASIBLE, INFEASIBLE).
            optimal_value (Any, optional): The optimal value if the problem was a COP and solved optimally.
        """
        self.problem_id = problem_id
        self.status = status
        self.optimal_value = optimal_value

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Converts the solution instance to a dictionary."""
        # Common fields will be included here by concrete implementations
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a solution instance from a dictionary."""
        # Common fields will be extracted here by concrete implementations
        pass

    def to_jsons(self) -> str:
        """Serializes the solution instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=4)

    @classmethod
    def from_jsons(cls, json_str: str):
        """Deserializes a solution instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def to_json(self, filepath: str):
        """Saves the solution instance to a JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_jsons())

    @classmethod
    def from_json(cls, filepath: str):
        """Loads a solution instance from a JSON file."""
        with open(filepath, 'r') as f:
            json_str = f.read()
        return cls.from_jsons(json_str)

    def __repr__(self):
        return f"{self.__class__.__name__}(problem_id='{self.problem_id}', status='{self.status}')"

    def __str__(self):
        base_str = f"Solution for Problem ID: {self.problem_id}\nStatus: {self.status}"
        if self.optimal_value is not None:
            base_str += f"\nOptimal Value: {self.optimal_value}"
        return base_str