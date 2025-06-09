from typing import List, Dict, Any
from csp_cop_src.problems.base_problem import BaseProblem

class SocialGolfersProblem(BaseProblem):
    """
    Represents an instance of the Social Golfers Problem.
    Parameters: G golfers, S groups, R rounds. Each group has P players.
    Total golfers G = S * P.
    """
    def __init__(self, problem_id: str, num_golfers: int, num_groups: int, group_size: int, num_rounds: int):
        super().__init__(problem_id, {})
        if not all(isinstance(arg, int) and arg > 0 for arg in [num_golfers, num_groups, group_size, num_rounds]):
            raise ValueError("All parameters must be positive integers.")
        if num_golfers != num_groups * group_size:
            raise ValueError("num_golfers must be equal to num_groups * group_size.")

        self.num_golfers = num_golfers
        self.num_groups = num_groups
        self.group_size = group_size
        self.num_rounds = num_rounds
        self.parameters = self._derive_parameters()

    def _derive_parameters(self) -> Dict[str, Any]:
        parameters = {
            "num_golfers": self.num_golfers,
            "num_groups": self.num_groups,
            "group_size": self.group_size,
            "num_rounds": self.num_rounds,
            "problem_type": "CSP" # Typically a CSP: find a valid schedule
        }
        return parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "problem": "SocialGolfers",
            "num_golfers": self.num_golfers,
            "num_groups": self.num_groups,
            "group_size": self.group_size,
            "num_rounds": self.num_rounds,
            "derived_parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        if data.get("problem") != "SocialGolfers":
            raise ValueError("Invalid problem type for SocialGolfersProblem.")
        return cls(
            problem_id=data["problem_id"],
            num_golfers=data["num_golfers"],
            num_groups=data["num_groups"],
            group_size=data["group_size"],
            num_rounds=data["num_rounds"]
        )

    def _normalized_data(self):
        return {
            'num_golfers': self.num_golfers,
            'num_groups': self.num_groups,
            'group_size': self.group_size,
            'num_rounds': self.num_rounds
        }