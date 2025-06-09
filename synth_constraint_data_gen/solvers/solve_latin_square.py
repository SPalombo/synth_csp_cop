from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from csp_cop_src.problems.latin_square import LatinSquareProblem
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.latin_square_solution import LatinSquareSolution

def solve_latin_square(problem: LatinSquareProblem) -> LatinSquareSolution:
    """
    Solves a Latin Square Problem using OR-Tools CP-SAT solver.
    This is a pure CSP.
    """
    model = cp_model.CpModel()

    n = problem.n

    # Variables: grid[r][c] = value in cell (r, c)
    grid_vars: Dict[Tuple[int, int], cp_model.IntVar] = {}
    for r in range(n):
        for c in range(n):
            grid_vars[(r, c)] = model.NewIntVar(0, n - 1, f'cell_{r}_{c}')

    # Constraints:
    # 1. All values in a row must be distinct.
    for r in range(n):
        model.AddAllDifferent([grid_vars[(r, c)] for c in range(n)])

    # 2. All values in a column must be distinct.
    for c in range(n):
        model.AddAllDifferent([grid_vars[(r, c)] for r in range(n)])

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution_status: str = SolutionStatus.NOT_SOLVED
    grid_solution: List[List[int]] = []

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_status = SolutionStatus.OPTIMAL if status == cp_model.OPTIMAL else SolutionStatus.FEASIBLE
        grid_solution = [[0 for _ in range(n)] for _ in range(n)]
        for r in range(n):
            for c in range(n):
                grid_solution[r][c] = int(solver.Value(grid_vars[(r, c)]))

    elif status == cp_model.INFEASIBLE:
        solution_status = SolutionStatus.INFEASIBLE
    else:
        solution_status = SolutionStatus.UNKNOWN

    return LatinSquareSolution(
        problem_id=problem.problem_id,
        status=solution_status,
        grid=grid_solution
    )
