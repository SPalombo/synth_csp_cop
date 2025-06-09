from ortools.sat.python import cp_model
from typing import Dict, List, Optional, Tuple

from csp_cop_src.problems.job_shop_scheduling import JobShopSchedulingProblem, Job, Task
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.job_shop_scheduling_solution import JobShopSchedulingSolution, ScheduledTask

def solve_job_shop_scheduling(problem: JobShopSchedulingProblem) -> JobShopSchedulingSolution:
    """
    Solves a Job-Shop Scheduling Problem using OR-Tools CP-SAT solver.
    """
    model = cp_model.CpModel()

    # Extract data from the problem instance
    all_jobs: List[Job] = problem.jobs
    num_jobs = problem.num_jobs
    num_machines = problem.num_machines

    # Calculate horizon (upper bound for makespan)
    horizon = 0
    for job in all_jobs:
        horizon += sum(task.duration for task in job.tasks)

    # Variables:
    intervals = {}
    start_vars = {}
    end_vars = {}
    machine_to_intervals: Dict[int, List[cp_model.IntervalVar]] = {m: [] for m in range(num_machines)}

    for job_idx, job in enumerate(all_jobs):
        for task_idx, task in enumerate(job.tasks):
            machine_id = task.machine_id
            duration = task.duration

            suffix = f'_{job_idx}_{task_idx}'
            start = model.NewIntVar(0, horizon, f'start{suffix}')
            end = model.NewIntVar(0, horizon, f'end{suffix}')
            interval = model.NewIntervalVar(start, duration, end, f'interval{suffix}')

            start_vars[(job_idx, task_idx)] = start
            end_vars[(job_idx, task_idx)] = end
            intervals[(job_idx, task_idx)] = interval
            machine_to_intervals[machine_id].append(interval)

    # Constraints:
    # 1. No overlap on machines
    for machine_id in range(num_machines):
        if machine_to_intervals[machine_id]:
            model.AddNoOverlap(machine_to_intervals[machine_id])

    # 2. Task precedence within each job
    for job_idx, job in enumerate(all_jobs):
        for task_idx in range(len(job.tasks) - 1):
            model.Add(start_vars[(job_idx, task_idx + 1)] >= end_vars[(job_idx, task_idx)])

    # Objective: Minimize makespan
    makespan = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(makespan, [end_vars[key] for key in end_vars])

    objective_is_minimized = False
    if problem.makespan_target is not None:
        model.Add(makespan <= problem.makespan_target)
    else:
        model.Minimize(makespan)
        objective_is_minimized = True

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    solution_status: str = SolutionStatus.NOT_SOLVED
    optimal_makespan: Optional[int] = None
    schedule: Dict[int, List[ScheduledTask]] = {}

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_status = SolutionStatus.OPTIMAL if status == cp_model.OPTIMAL else SolutionStatus.FEASIBLE
        optimal_makespan = int(solver.ObjectiveValue()) if objective_is_minimized else int(solver.Value(makespan))

        for job_idx, job in enumerate(all_jobs):
            schedule[job_idx] = []
            for task_idx, task in enumerate(job.tasks):
                scheduled_task = ScheduledTask(
                    task_idx=task_idx,
                    machine_id=task.machine_id,
                    start=int(solver.Value(start_vars[(job_idx, task_idx)])),
                    end=int(solver.Value(end_vars[(job_idx, task_idx)])),
                    duration=task.duration
                )
                schedule[job_idx].append(scheduled_task)
    elif status == cp_model.INFEASIBLE:
        solution_status = SolutionStatus.INFEASIBLE
    else:
        solution_status = SolutionStatus.UNKNOWN

    return JobShopSchedulingSolution(
        problem_id=problem.problem_id,
        status=solution_status,
        optimal_makespan=optimal_makespan,
        schedule=schedule
    )
