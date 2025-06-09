"""
validate_job_shop_solution.py

Feasibility validator for Job-Shop-Scheduling answers.

Key rules
---------
1.  If `solution.status` is INFEASIBLE we accept an empty schedule and quit.
2.  Otherwise a schedule **must** be present and meet every constraint:
      • machine-range, precedence, no intra-machine overlaps, durations, etc.
3.  If the problem has a `makespan_target` (CSP mode) the schedule is valid
    iff its makespan ≤ that target.
      - We do **not** attempt to prove optimality; we only check feasibility.
4.  A mismatch between `solution.makespan` and the makespan computed from the
    schedule is a hard error.
5.  The function returns `(is_valid, violations_dict, error_messages)`.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional

from csp_cop_src.problems.job_shop_scheduling import JobShopSchedulingProblem
from csp_cop_src.solutions.base_solution import SolutionStatus
from csp_cop_src.solutions.job_shop_scheduling_solution import JobShopSchedulingSolution

# ---------------------------------------------------------------------------
#  Import your own domain classes / enums here
# ---------------------------------------------------------------------------
# from your_module import (
#     JobShopSchedulingProblem,
#     JobShopSchedulingSolution,
#     ScheduledTask,
#     SolutionStatus,
# )


# ────────────────────────────────────────────────────────────────────────────
#  Helper
# ────────────────────────────────────────────────────────────────────────────
def _as_dict(task: Any) -> Optional[Dict[str, Any]]:
    """Return a task as plain dict or None if malformed."""
    if isinstance(task, dict):
        return task
    if hasattr(task, "to_dict"):
        return task.to_dict()
    return None


# ────────────────────────────────────────────────────────────────────────────
#  Main validator
# ────────────────────────────────────────────────────────────────────────────
def validate_job_shop_solution(
    problem: JobShopSchedulingProblem,
    solution: JobShopSchedulingSolution,
) -> Tuple[bool, Dict[str, int], List[str]]:
    """
    Validate `solution` against `problem`.

    Returns
    -------
    is_valid : bool
        True if the schedule satisfies every constraint (and ≤ makespan_target
        when one is given).
    violations : dict[str, int]
        Count of each violation type.
    error_details : list[str]
        Human-readable messages (one per violation).
    """
    # ── containers ───────────────────────────────────────────────────────────
    violations: Dict[str, int] = defaultdict(int)
    error_details: List[str] = []
    is_valid = True

    def v(key: str, msg: str, fatal: bool = True):
        """Register a violation."""
        nonlocal is_valid
        violations[key] += 1
        error_details.append(msg)
        if fatal:
            is_valid = False

    # ── early exit: INFEASIBLE path ──────────────────────────────────────────
    if solution.status == SolutionStatus.INFEASIBLE:
        if solution.schedule:
            v("non_empty_infeasible", "INFEASIBLE solution contains a schedule.")
        return is_valid, dict(violations), error_details

    # ── basic presence checks ───────────────────────────────────────────────
    if not solution.schedule:
        v("empty_schedule", f"{solution.status.name} solution has no schedule.")
        return is_valid, dict(violations), error_details

    # ── per-machine container for overlap detection ─────────────────────────
    machine_ops: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    task_end_times: List[int] = []

    # ── iterate over jobs/tasks ──────────────────────────────────────────────
    for j_idx, job in enumerate(problem.jobs):
        sched_list = solution.schedule.get(j_idx)
        if sched_list is None:
            v("missing_job", f"Job {j_idx} absent from schedule.")
            continue

        # collect tasks by task_idx and detect duplicates
        sched_by_idx: Dict[int, Dict[str, Any]] = {}
        for raw in sched_list:
            sd = _as_dict(raw)
            if sd is None or "task_idx" not in sd:
                v("malformed_task", f"Job {j_idx}: malformed task entry.")
                continue
            t_idx = sd["task_idx"]
            if t_idx in sched_by_idx:
                v("duplicate_task_idx", f"Job {j_idx}: task_idx {t_idx} duplicated.")
            sched_by_idx[t_idx] = sd

        # task-count mismatch
        if len(sched_by_idx) != len(job.tasks):
            v("task_count_mismatch",
              f"Job {j_idx}: expected {len(job.tasks)} tasks, found {len(sched_by_idx)}.")

        # validate each task
        for t_idx, ptask in enumerate(job.tasks):
            sd = sched_by_idx.get(t_idx)
            if sd is None:
                v("missing_task",
                  f"Job {j_idx}, Task {t_idx} missing in schedule.")
                continue

            # required keys
            for key in ("machine_id", "start", "end"):
                if key not in sd:
                    v("malformed_task",
                      f"Job {j_idx}, Task {t_idx} missing '{key}'.")
                    continue

            m_id, start, end = sd["machine_id"], sd["start"], sd["end"]

            # machine id
            if not isinstance(m_id, int) or not (0 <= m_id < problem.num_machines):
                v("invalid_machine_id",
                  f"Job {j_idx}, Task {t_idx}: machine_id {m_id} out of range.")
            # machine mismatch
            if m_id != ptask.machine_id:
                v("machine_mismatch",
                  f"Job {j_idx}, Task {t_idx}: expected M{ptask.machine_id}, got M{m_id}.")

            # time sanity
            if not all(isinstance(x, int) for x in (start, end)):
                v("non_integer_time",
                  f"Job {j_idx}, Task {t_idx}: start/end not integers.")
                continue
            if start < 0:
                v("negative_start",
                  f"Job {j_idx}, Task {t_idx}: start {start} < 0.")
            if end <= start:
                v("non_positive_duration",
                  f"Job {j_idx}, Task {t_idx}: end {end} ≤ start {start}.")
            if end - start != ptask.duration:
                v("duration_mismatch",
                  f"Job {j_idx}, Task {t_idx}: "
                  f"duration should be {ptask.duration}, got {end-start}.")

            # collect for later checks
            machine_ops[m_id].append((start, end))
            task_end_times.append(end)

        # precedence (task i must finish before i+1 starts)
        for i in range(len(job.tasks) - 1):
            first = sched_by_idx.get(i)
            second = sched_by_idx.get(i + 1)
            if first and second and first["end"] > second["start"]:
                v("precedence_violation",
                  f"Job {j_idx}: Task {i} ends {first['end']} "
                  f"after Task {i+1} starts {second['start']}.")

    # ── machine overlap check ───────────────────────────────────────────────
    for m_id, ops in machine_ops.items():
        if len(ops) < 2:
            continue
        ops.sort()  # sort by start
        for (s1, e1), (s2, e2) in zip(ops, ops[1:]):
            if e1 > s2:
                v("machine_overlap",
                  f"Machine {m_id}: [{s1},{e1}) overlaps [{s2},{e2}).")
                break  # one is enough

    # ── makespan checks ──────────────────────────────────────────────────────
    calc_ms: Optional[int] = max(task_end_times) if task_end_times else None
    if calc_ms is None:
        v("no_valid_times", "No valid start/end times found in schedule.")
    else:
        # compare with reported solution.makespan
        if solution.makespan is not None and solution.makespan != calc_ms:
            v("makespan_mismatch",
              f"Solution.makespan {solution.makespan} ≠ calculated {calc_ms}.")
        # compare with problem.makespan_target if present
        if problem.makespan_target is not None and calc_ms > problem.makespan_target:
            v("target_makespan_exceeded",
              f"Makespan {calc_ms} exceeds target {problem.makespan_target}.")

    # ── final verdict ────────────────────────────────────────────────────────
    return is_valid, dict(violations), error_details