import json
from typing import Dict, Any, List, Optional
from csp_cop_src.solutions.base_solution import BaseSolution, SolutionStatus

class GraphColoringSolution(BaseSolution):
    """
    Represents a solution to a Graph Coloring Problem.
    """
    def __init__(self,
                 problem_id: str,
                 status: str,
                 num_colors_used: Optional[int],
                 node_colors: Dict[int, int] # {node_id: color_id, ...}
                 ):
        """
        Initializes a Graph Coloring Solution instance.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (str): The status of the solution.
            num_colors_used (Optional[int]): The number of colors used in this solution.
            node_colors (Dict[int, int]): A dictionary mapping node_id to its assigned color_id.
                                           Colors are typically 0-indexed.
        """
        super().__init__(problem_id, status, num_colors_used) # num_colors_used is the optimal_value for COP
        if not isinstance(node_colors, dict) or not all(isinstance(k, int) and isinstance(v, int) for k, v in node_colors.items()):
            raise ValueError("node_colors must be a dictionary mapping int node_id to int color_id.")
        self.node_colors = node_colors
        self.colors_used = num_colors_used # Alias for clarity

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Graph Coloring solution instance to a dictionary."""
        return {
            "solution_type": "GraphColoring",
            "problem_id": self.problem_id,
            "status": self.status,
            "num_colors_used": self.colors_used,
            "node_colors": self.node_colors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Graph Coloring solution instance from a dictionary."""
        if data.get("solution_type") != "GraphColoring":
            raise ValueError("Invalid solution type for GraphColoringSolution.")
        return cls(
            problem_id=data["problem_id"],
            status=data["status"],
            num_colors_used=data["num_colors_used"],
            node_colors={int(k): v for k, v in data["node_colors"].items()} # Ensure keys are ints if they come as strings
        )