import json
from typing import Dict, Any, List, Optional
from csp_cop_src.solutions.base_solution import BaseSolution, SolutionStatus

class LatinSquareSolution(BaseSolution):
    """
    Represents a solution to a Latin Square Problem.
    """
    def __init__(self,
                 problem_id: str,
                 status: str,
                 grid: List[List[int]] # The N x N grid itself
                 ):
        """
        Initializes a Latin Square Solution instance.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (str): The status of the solution.
            grid (List[List[int]]): The N x N grid representing the Latin Square.
                                     Values are the symbols (e.g., 0 to N-1).
        """
        super().__init__(problem_id, status, None) # Latin Square is a pure CSP, no optimal value
        if not (isinstance(grid, list) and all(isinstance(row, list) and all(isinstance(val, int) for val in row) for row in grid)):
            raise ValueError("grid must be a list of lists of integers.")
        self.grid = grid

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Latin Square solution instance to a dictionary."""
        return {
            "solution_type": "LatinSquare",
            "problem_id": self.problem_id,
            "status": self.status,
            "grid": self.grid,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Latin Square solution instance from a dictionary."""
        if data.get("solution_type") != "LatinSquare":
            raise ValueError("Invalid solution type for LatinSquareSolution.")
        return cls(
            problem_id=data["problem_id"],
            status=data["status"],
            grid=data["grid"]
        )