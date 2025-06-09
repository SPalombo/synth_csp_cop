from typing import List, Dict, Any
from csp_cop_src.problems.base_problem import BaseProblem

class TaskAssignmentProblem(BaseProblem):
    """
    Represents an instance of a Task Assignment Problem.
    Assigns N agents to M tasks with associated costs/profits.
    """
    def __init__(self, problem_id: str, num_agents: int, num_tasks: int, costs: List[List[int]], max_cost_target: int = None):
        """
        Args:
            problem_id (str): A unique identifier.
            num_agents (int): Number of agents available.
            num_tasks (int): Number of tasks to be assigned.
            costs (List[List[int]]): A matrix where costs[i][j] is the cost of agent i performing task j.
                                     Assume -1 or a very high number for impossible assignments.
            max_cost_target (int, optional): A target for the maximum total cost (for CSP variants).
                                             If not provided, it's a COP to minimize total cost.
        """
        super().__init__(problem_id, {})
        if not all(isinstance(arg, int) and arg > 0 for arg in [num_agents, num_tasks]):
            raise ValueError("num_agents and num_tasks must be positive integers.")
        if not (isinstance(costs, list) and len(costs) == num_agents and
                all(isinstance(row, list) and len(row) == num_tasks and
                    all(isinstance(c, int) for c in row) for row in costs)):
            raise ValueError("Costs must be a num_agents x num_tasks matrix of integers.")

        self.num_agents = num_agents
        self.num_tasks = num_tasks
        self.costs = costs
        self.max_cost_target = max_cost_target
        self.parameters = self._derive_parameters()

    def _derive_parameters(self) -> Dict[str, Any]:
        min_cost_per_task = [min(agent_costs) for agent_costs in zip(*self.costs)] if self.num_tasks > 0 else []
        max_cost_per_task = [max(agent_costs) for agent_costs in zip(*self.costs)] if self.num_tasks > 0 else []

        parameters = {
            "num_agents": self.num_agents,
            "num_tasks": self.num_tasks,
            "total_possible_assignments": self.num_agents * self.num_tasks,
            "min_total_possible_cost": sum(min_cost_per_task) if min_cost_per_task else 0,
            "max_total_possible_cost": sum(max_cost_per_task) if max_cost_per_task else 0,
            "cost_matrix": self.costs # For detailed context in NL generation
        }
        if self.max_cost_target is not None:
            parameters["max_cost_target"] = self.max_cost_target
            parameters["problem_type"] = "CSP"
        else:
            parameters["problem_type"] = "COP" # Minimize total cost
        return parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "problem": "TaskAssignment",
            "num_agents": self.num_agents,
            "num_tasks": self.num_tasks,
            "costs": self.costs,
            "max_cost_target": self.max_cost_target,
            "derived_parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        if data.get("problem") != "TaskAssignment":
            raise ValueError("Invalid problem type for TaskAssignmentProblem.")
        return cls(
            problem_id=data["problem_id"],
            num_agents=data["num_agents"],
            num_tasks=data["num_tasks"],
            costs=data["costs"],
            max_cost_target=data.get("max_cost_target")
        )

    def _normalized_data(self):
        # Canonicalize costs as tuple of tuples
        costs_norm = tuple(tuple(row) for row in self.costs)
        return {
            'num_agents': self.num_agents,
            'num_tasks': self.num_tasks,
            'costs': costs_norm,
            'max_cost_target': self.max_cost_target
        }