import json
from typing import Dict, Any, List, Optional
from csp_cop_src.solutions.base_solution import BaseSolution, SolutionStatus

class SocialGolfersSolution(BaseSolution):
    """
    Represents a solution to the Social Golfers Problem.
    """
    def __init__(self,
                 problem_id: str,
                 status: str,
                 schedule: Dict[int, List[List[int]]] # {round_id: [[golfer_id, ...], [golfer_id, ...], ...]}
                 ):
        """
        Initializes a Social Golfers Solution instance.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (str): The status of the solution.
            schedule (Dict[int, List[List[int]]]): A dictionary where keys are round_ids (0-indexed)
                                                   and values are lists of groups. Each group is a list of golfer_ids.
        """
        # For Social Golfers, there isn't typically an "optimal value" to minimize/maximize,
        # it's usually a pure CSP to find *any* valid schedule.
        super().__init__(problem_id, status, None)
        if not isinstance(schedule, dict) or not all(isinstance(k, int) and isinstance(v, list) for k, v in schedule.items()):
            raise ValueError("schedule must be a dictionary mapping int round_id to list of groups.")
        self.schedule = schedule

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Social Golfers solution instance to a dictionary."""
        return {
            "solution_type": "SocialGolfers",
            "problem_id": self.problem_id,
            "status": self.status,
            "schedule": self.schedule,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Social Golfers solution instance from a dictionary."""
        if data.get("solution_type") != "SocialGolfers":
            raise ValueError("Invalid solution type for SocialGolfersSolution.")
        return cls(
            problem_id=data["problem_id"],
            status=data["status"],
            schedule={int(k): v for k, v in data["schedule"].items()} # Ensure keys are ints
        )