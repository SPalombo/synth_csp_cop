from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from csp_cop_src.problems.bin_packing import BinPackingProblem
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.bin_packing_solution import BinPackingSolution

def solve_bin_packing(problem: BinPackingProblem) -> BinPackingSolution:
    """
    Solves a Bin Packing Problem using OR-Tools CP-SAT solver.
    """
    model = cp_model.CpModel()

    bin_capacity = problem.bin_capacity
    item_sizes = problem.item_sizes
    num_items = problem.num_items

    max_num_bins_upper_bound = num_items
    min_num_bins_lower_bound = (sum(item_sizes) + bin_capacity - 1) // bin_capacity

    # Variables:
    x: Dict[Tuple[int, int], cp_model.BoolVar] = {}
    y: Dict[int, cp_model.BoolVar] = {}

    if problem.num_bins_target is not None:
        max_num_bins_upper_bound = problem.num_bins_target

    for b in range(max_num_bins_upper_bound):
        y[b] = model.NewBoolVar(f'y_{b}')
        for i in range(num_items):
            x[(i, b)] = model.NewBoolVar(f'x_{i},{b}')

    # Constraints:
    # 1. Each item must be placed in exactly one bin.
    for i in range(num_items):
        model.Add(sum(x[(i, b)] for b in range(max_num_bins_upper_bound)) == 1)

    # 2. Bin capacity constraint
    for b in range(max_num_bins_upper_bound):
        model.Add(sum(x[(i, b)] * item_sizes[i] for i in range(num_items)) <= bin_capacity * y[b])

    # Objective: Minimize the number of used bins (for COP)
    objective_is_minimized = False
    num_bins_used_var: Optional[cp_model.IntVar] = None

    if problem.num_bins_target is None:
        num_bins_used_var = model.NewIntVar(min_num_bins_lower_bound, max_num_bins_upper_bound, 'num_bins_used')
        model.Add(num_bins_used_var == sum(y[b] for b in range(max_num_bins_upper_bound)))
        model.Minimize(num_bins_used_var)
        objective_is_minimized = True

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution_status: str = SolutionStatus.NOT_SOLVED
    num_bins_used: Optional[int] = None
    bins: Dict[int, List[int]] = {}
    bin_contents_weights: Dict[int, List[int]] = {}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_status = SolutionStatus.OPTIMAL if status == cp_model.OPTIMAL else SolutionStatus.FEASIBLE

        if objective_is_minimized:
            num_bins_used = int(solver.ObjectiveValue())
        else:
            used_bins_count = 0
            for b in range(max_num_bins_upper_bound):
                if solver.Value(y[b]) == 1:
                    used_bins_count += 1
            num_bins_used = used_bins_count

        for b in range(max_num_bins_upper_bound):
            if solver.Value(y[b]) == 1:
                bins[b] = []
                bin_contents_weights[b] = []
                for i in range(num_items):
                    if solver.Value(x[(i, b)]) == 1:
                        bins[b].append(i)
                        bin_contents_weights[b].append(item_sizes[i])

    elif status == cp_model.INFEASIBLE:
        solution_status = SolutionStatus.INFEASIBLE
    else:
        solution_status = SolutionStatus.UNKNOWN

    return BinPackingSolution(
        problem_id=problem.problem_id,
        status=solution_status,
        num_bins_used=num_bins_used,
        bins=bins,
        bin_contents_weights=bin_contents_weights
    )
