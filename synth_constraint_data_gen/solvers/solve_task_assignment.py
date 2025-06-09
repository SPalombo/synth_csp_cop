from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from csp_cop_src.problems.task_assignment import TaskAssignmentProblem
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.task_assignment_solution import TaskAssignmentSolution

def solve_task_assignment(problem: TaskAssignmentProblem) -> TaskAssignmentSolution:
    """
    Solves a Task Assignment Problem using OR-Tools CP-SAT solver.
    """
    model = cp_model.CpModel()

    num_agents = problem.num_agents
    num_tasks = problem.num_tasks
    costs = problem.costs

    # Variables: x[i][j] = 1 if agent i is assigned to task j, 0 otherwise
    assignments: Dict[Tuple[int, int], cp_model.BoolVar] = {}
    for i in range(num_agents):
        for j in range(num_tasks):
            assignments[(i, j)] = model.NewBoolVar(f'x_{i}_{j}')

    # Constraints:
    # 1. Each task must be assigned to exactly one agent.
    for j in range(num_tasks):
        model.Add(sum(assignments[(i, j)] for i in range(num_agents)) == 1)

    # Objective: Minimize total cost
    # A safe upper bound for total_cost_var.
    # Assumes costs are non-negative.
    max_possible_cost = sum(max(row) for row in costs) if costs else 0
    total_cost_var = model.NewIntVar(0, max_possible_cost, 'total_cost')
    model.Add(total_cost_var == sum(assignments[(i, j)] * costs[i][j]
                                   for i in range(num_agents) for j in range(num_tasks)))

    objective_is_minimized = False
    if problem.max_cost_target is not None:
        model.Add(total_cost_var <= problem.max_cost_target)
    else:
        model.Minimize(total_cost_var)
        objective_is_minimized = True

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution_status: str = SolutionStatus.NOT_SOLVED
    total_cost: Optional[int] = None
    task_assignments: Dict[int, int] = {}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_status = SolutionStatus.OPTIMAL if status == cp_model.OPTIMAL else SolutionStatus.FEASIBLE
        total_cost = int(solver.ObjectiveValue()) if objective_is_minimized else int(solver.Value(total_cost_var))

        for j in range(num_tasks):
            for i in range(num_agents):
                if solver.Value(assignments[(i, j)]) == 1:
                    task_assignments[j] = i
                    break

    elif status == cp_model.INFEASIBLE:
        solution_status = SolutionStatus.INFEASIBLE
    else:
        solution_status = SolutionStatus.UNKNOWN

    return TaskAssignmentSolution(
        problem_id=problem.problem_id,
        status=solution_status,
        total_cost=total_cost,
        assignments=task_assignments
    )
