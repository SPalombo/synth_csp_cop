import json
from typing import Dict, Any, List, Optional
from csp_cop_src.solutions.base_solution import BaseSolution, SolutionStatus

class TaskAssignmentSolution(BaseSolution):
    """
    Represents a solution to a Task Assignment Problem.
    """
    def __init__(self,
                 problem_id: str,
                 status: str,
                 total_cost: Optional[int],
                 assignments: Dict[int, int] # {task_id: agent_id}
                 ):
        """
        Initializes a Task Assignment Solution instance.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (str): The status of the solution.
            total_cost (Optional[int]): The total cost incurred by this assignment.
            assignments (Dict[int, int]): A dictionary mapping task_id to the agent_id assigned to it.
        """
        super().__init__(problem_id, status, total_cost) # total_cost is the optimal_value for COP
        if not isinstance(assignments, dict) or not all(isinstance(k, int) and isinstance(v, int) for k, v in assignments.items()):
            raise ValueError("assignments must be a dictionary mapping int task_id to int agent_id.")
        self.assignments = assignments
        self.cost = total_cost # Alias for clarity

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Task Assignment solution instance to a dictionary."""
        return {
            "solution_type": "TaskAssignment",
            "problem_id": self.problem_id,
            "status": self.status,
            "total_cost": self.cost,
            "assignments": self.assignments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Task Assignment solution instance from a dictionary."""
        if data.get("solution_type") != "TaskAssignment":
            raise ValueError("Invalid solution type for TaskAssignmentSolution.")
        return cls(
            problem_id=data["problem_id"],
            status=data["status"],
            total_cost=data["total_cost"],
            assignments={int(k): v for k, v in data["assignments"].items()} # Ensure keys are ints
        )
