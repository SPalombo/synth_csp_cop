from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from csp_cop_src.problems.graph_coloring import GraphColoringProblem
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.graph_coloring_solution import GraphColoringSolution

def solve_graph_coloring(problem: GraphColoringProblem) -> GraphColoringSolution:
    """
    Solves a Graph Coloring Problem using OR-Tools CP-SAT solver.
    """
    model = cp_model.CpModel()

    num_nodes = problem.num_nodes
    edges = problem.edges

    max_colors_upper_bound = num_nodes
    if problem.num_colors_target is not None:
        max_colors_upper_bound = problem.num_colors_target

    # Variables: colors for each node
    node_vars: Dict[int, cp_model.IntVar] = {}
    for i in range(num_nodes):
        node_vars[i] = model.NewIntVar(0, max_colors_upper_bound - 1, f'node_color_{i}')

    # Constraints: adjacent nodes must have different colors
    for u, v in edges:
        model.Add(node_vars[u] != node_vars[v])

    # Objective: Minimize the number of colors used (for COP)
    objective_is_minimized = False
    num_colors_used_var: Optional[cp_model.IntVar] = None

    if problem.num_colors_target is None:
        num_colors_used_var = model.NewIntVar(0, max_colors_upper_bound - 1, 'num_colors_used')
        model.AddMaxEquality(num_colors_used_var, [node_vars[i] for i in range(num_nodes)])
        model.Minimize(num_colors_used_var)
        objective_is_minimized = True

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution_status: str = SolutionStatus.NOT_SOLVED
    num_colors_used: Optional[int] = None
    node_colors: Dict[int, int] = {}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_status = SolutionStatus.OPTIMAL if status == cp_model.OPTIMAL else SolutionStatus.FEASIBLE

        if objective_is_minimized:
            num_colors_used = int(solver.ObjectiveValue()) + 1
        else:
            if problem.num_colors_target is not None:
                actual_colors = set()
                for i in range(num_nodes):
                    color = int(solver.Value(node_vars[i]))
                    node_colors[i] = color
                    actual_colors.add(color)
                num_colors_used = len(actual_colors)
            else:
                num_colors_used = 0

        for i in range(num_nodes):
            node_colors[i] = int(solver.Value(node_vars[i]))

    elif status == cp_model.INFEASIBLE:
        solution_status = SolutionStatus.INFEASIBLE
    else:
        solution_status = SolutionStatus.UNKNOWN

    return GraphColoringSolution(
        problem_id=problem.problem_id,
        status=solution_status,
        num_colors_used=num_colors_used,
        node_colors=node_colors
    )
