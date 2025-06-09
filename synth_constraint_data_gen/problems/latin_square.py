from typing import Dict, Any
from csp_cop_src.problems.base_problem import BaseProblem

class LatinSquareProblem(BaseProblem):
    """
    Represents an instance of a Latin Square Problem.
    An N x N Latin Square.
    """
    def __init__(self, problem_id: str, n: int):
        super().__init__(problem_id, {})
        if not isinstance(n, int) or n <= 0:
            raise ValueError("n (size of the square) must be a positive integer.")
        self.n = n
        self.parameters = self._derive_parameters()

    def _derive_parameters(self) -> Dict[str, Any]:
        parameters = {
            "n": self.n,
            "grid_size": f"{self.n}x{self.n}",
            "num_cells": self.n * self.n,
            "problem_type": "CSP" # Find a valid Latin Square
        }
        return parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "problem": "LatinSquare",
            "n": self.n,
            "derived_parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        if data.get("problem") != "LatinSquare":
            raise ValueError("Invalid problem type for LatinSquareProblem.")
        return cls(
            problem_id=data["problem_id"],
            n=data["n"]
        )

    def _normalized_data(self):
        return {'n': self.n}