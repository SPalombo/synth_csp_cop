import json
from typing import List, Dict, Any, Tuple
from csp_cop_src.problems.base_problem import BaseProblem

class GraphColoringProblem(BaseProblem):
    """
    Represents an instance of a Graph Coloring Problem.
    """
    def __init__(self, problem_id: str, num_nodes: int, edges: List[Tuple[int, int]], num_colors_target: int = None):
        """
        Initializes a Graph Coloring Problem instance.

        Args:
            problem_id (str): A unique identifier for this problem instance.
            num_nodes (int): The total number of nodes (vertices) in the graph.
            edges (List[Tuple[int, int]]): A list of tuples, where each tuple (u, v) represents an edge
                                           between node u and node v. Nodes are 0-indexed.
            num_colors_target (int, optional): An optional target for the number of colors (for CSP variants).
                                               If not provided, it's typically a COP problem aiming to minimize colors.
        """
        super().__init__(problem_id, {})
        if not isinstance(num_nodes, int) or num_nodes <= 0:
            raise ValueError("num_nodes must be a positive integer.")
        if not isinstance(edges, list) or not all(isinstance(e, tuple) and len(e) == 2 for e in edges):
            raise ValueError("edges must be a list of (u, v) tuples.")
        if any(not (0 <= n < num_nodes) for edge in edges for n in edge):
            raise ValueError(f"Edge nodes must be within [0, {num_nodes-1}].")

        self.num_nodes = num_nodes
        self.edges = sorted(list(set([tuple(sorted(edge)) for edge in edges]))) # Store unique, sorted edges
        self.num_colors_target = num_colors_target
        self.num_edges = len(self.edges)
        self.parameters = self._derive_parameters()

    def _derive_parameters(self) -> Dict[str, Any]:
        """Derives a comprehensive set of parameters from the graph data."""
        density = (2 * self.num_edges) / (self.num_nodes * (self.num_nodes - 1)) if self.num_nodes > 1 else 0

        parameters = {
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "graph_density": round(density, 4),
            "edges_list": self.edges, # Include for detailed logging/prompting
        }
        if self.num_colors_target is not None:
            parameters["num_colors_target"] = self.num_colors_target
            parameters["problem_type"] = "CSP"
        else:
            parameters["problem_type"] = "COP"
        return parameters

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Graph Coloring problem instance to a dictionary."""
        return {
            "problem_id": self.problem_id,
            "problem": "GraphColoring",
            "num_nodes": self.num_nodes,
            "edges": self.edges,
            "num_colors_target": self.num_colors_target,
            "derived_parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Graph Coloring problem instance from a dictionary."""
        if data.get("problem") != "GraphColoring":
            raise ValueError("Invalid problem type for GraphColoringProblem.")
        return cls(
            problem_id=data["problem_id"],
            num_nodes=data["num_nodes"],
            edges=data["edges"],
            num_colors_target=data.get("num_colors_target")
        )

    def _normalized_data(self):
        edges_norm = tuple(sorted(tuple(sorted(edge)) for edge in self.edges))
        return {
            'num_nodes': self.num_nodes,
            'edges': edges_norm,
            'num_colors_target': self.num_colors_target
        }