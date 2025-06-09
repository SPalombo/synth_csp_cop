from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from csp_cop_src.problems.social_golfers import SocialGolfersProblem
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.social_golfers_solution import SocialGolfersSolution

def solve_social_golfers(problem: SocialGolfersProblem) -> SocialGolfersSolution:
    """
    Solves the Social Golfers Problem using OR-Tools CP-SAT solver.
    This is a pure CSP.
    """
    model = cp_model.CpModel()

    num_golfers = problem.num_golfers
    num_groups = problem.num_groups
    group_size = problem.group_size
    num_rounds = problem.num_rounds

    # Variables: assignment[r][g] = group_id for golfer g in round r
    assignments: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for r in range(num_rounds):
        for g in range(num_golfers):
            assignments[(r, g)] = model.NewIntVar(0, num_groups - 1, f'assignment_r{r}_g{g}')

    # Variables: group_membership[r][group_idx][golfer_idx]
    group_membership: Dict[Tuple[int, int, int], cp_model.BoolVar] = {}
    for r in range(num_rounds):
        for group_idx in range(num_groups):
            for g in range(num_golfers):
                group_membership[(r, group_idx, g)] = model.NewBoolVar(f'group_membership_r{r}_g{g}_gr{group_idx}')
                model.Add(assignments[(r, g)] == group_idx).OnlyEnforceIf(group_membership[(r, group_idx, g)])
                model.Add(assignments[(r, g)] != group_idx).OnlyEnforceIf(group_membership[(r, group_idx, g)].Not())

    # Constraints:
    # 1. Each group has exactly `group_size` golfers in each round.
    for r in range(num_rounds):
        for group_idx in range(num_groups):
            model.Add(sum(group_membership[(r, group_idx, g)] for g in range(num_golfers)) == group_size)

    # 2. No two golfers play in the same group more than once.
    for g1 in range(num_golfers):
        for g2 in range(g1 + 1, num_golfers):
            same_group_in_round_vars: List[cp_model.BoolVar] = []
            for r in range(num_rounds):
                are_in_same_group_in_round = model.NewBoolVar(f'same_group_r{r}_g{g1}_g{g2}')
                model.Add(assignments[(r, g1)] == assignments[(r, g2)]).OnlyEnforceIf(are_in_same_group_in_round)
                model.Add(assignments[(r, g1)] != assignments[(r, g2)]).OnlyEnforceIf(are_in_same_group_in_round.Not())
                same_group_in_round_vars.append(are_in_same_group_in_round)

            model.Add(sum(same_group_in_round_vars) <= 1)

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution_status: str = SolutionStatus.NOT_SOLVED
    schedule: Dict[int, List[List[int]]] = {}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_status = SolutionStatus.OPTIMAL if status == cp_model.OPTIMAL else SolutionStatus.FEASIBLE

        for r in range(num_rounds):
            round_groups: Dict[int, List[int]] = {group_idx: [] for group_idx in range(num_groups)}
            for g in range(num_golfers):
                assigned_group = int(solver.Value(assignments[(r, g)]))
                round_groups[assigned_group].append(g)
            schedule[r] = [round_groups[group_idx] for group_idx in sorted(round_groups.keys())]

    elif status == cp_model.INFEASIBLE:
        solution_status = SolutionStatus.INFEASIBLE
    else:
        solution_status = SolutionStatus.UNKNOWN

    return SocialGolfersSolution(
        problem_id=problem.problem_id,
        status=solution_status,
        schedule=schedule
    )
