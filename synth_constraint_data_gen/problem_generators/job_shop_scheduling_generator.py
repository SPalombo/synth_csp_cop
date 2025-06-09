from __future__ import annotations

import logging
import math
import random
import uuid
from functools import lru_cache
from typing import Dict, List, Tuple, Optional

from csp_cop_src.problems.job_shop_scheduling import JobShopSchedulingProblem, Job, Task
from csp_cop_src.problem_generators.base_problem_generator import ProblemGenerator
from csp_cop_src.solvers.solve_job_shop_scheduling import solve_job_shop_scheduling

logger = logging.getLogger(__name__)
MAKESPAN_TARGET_FACTOR: int = 2

# ---------------------------------------------------------------------------
# 1) Uniform job‑length sampler
# ---------------------------------------------------------------------------

def _sample_job_lengths(*, n: int, k: int, l: int, total: int, rng: random.Random) -> List[int]:
    """Return an *ordered* length‑n list in [k,l]^n summing to *total*, uniformly."""
    if not (n * k <= total <= n * l):
        raise ValueError("total outside feasible range [n·k, n·l]")

    C = l - k
    residual = total - n * k

    @lru_cache(maxsize=None)
    def N(r: int, m: int) -> int:
        if r == 0:
            return 1
        if m == 0:
            return 0
        return sum(N(r - t, m - 1) for t in range(0, min(C, r) + 1))

    lengths: List[int] = []
    for i in range(n - 1):
        upper = min(C, residual)
        weights = [N(residual - t, n - i - 1) for t in range(upper + 1)]
        t = rng.choices(range(upper + 1), weights)[0]
        lengths.append(k + t)
        residual -= t
    lengths.append(k + residual)
    return lengths

# ---------------------------------------------------------------------------
# 2) Exact machine‑sequence sampler with ≥1 coverage
# ---------------------------------------------------------------------------

class _ExactMachineSampler:
    """Generates per‑job machine ID sequences uniformly under constraints."""

    def __init__(self, *, job_lengths: List[int], num_machines: int, rng: random.Random) -> None:
        if num_machines > 10:
            raise ValueError("Exact sampler supports ≤10 machines; use heuristic otherwise.")
        self.job_lengths = job_lengths
        self.m = num_machines
        self.rng = rng
        self._per_len_counts = {L: self._enumerate_len(L) for L in set(job_lengths)}
        self._count_remaining_jobs = lru_cache(maxsize=None)(self._count_remaining_jobs)  # type: ignore

    # ----- enumerate sequences of a given length, keyed by coverage mask -----
    def _enumerate_len(self, L: int) -> List[int]:
        m = self.m
        masks = 1 << m
        dp_prev = [[0] * m for _ in range(masks)]
        for machine in range(m):
            dp_prev[1 << machine][machine] = 1
        for _ in range(1, L):
            dp_next = [[0] * m for _ in range(masks)]
            for mask in range(masks):
                for last, cnt in enumerate(dp_prev[mask]):
                    if cnt == 0:
                        continue
                    for machine in range(m):
                        if machine == last:
                            continue
                        dp_next[mask | (1 << machine)][machine] += cnt
            dp_prev = dp_next
        return [sum(dp_prev[mask]) for mask in range(masks)]

    # ----- global DP: how many completions from state (idx, missing_mask) -----
    def _count_remaining_jobs(self, idx: int, missing: int) -> int:
        if missing == 0:
            # Remaining jobs unconstrained (all machines already seen)
            return 1
        if idx == len(self.job_lengths):
            return 0  # no jobs left but still missing machines
        seq_counts = self._per_len_counts[self.job_lengths[idx]]
        total = 0
        for mask, cnt in enumerate(seq_counts):
            if cnt == 0:
                continue
            new_missing = missing & ~mask  # clear any machines this job covers
            rest = self._count_remaining_jobs(idx + 1, new_missing)
            total += cnt * rest
        return total

    # ----- public sampler -----
    def sample(self) -> List[List[int]]:
        missing = (1 << self.m) - 1
        sequences: List[List[int]] = []
        for idx, L in enumerate(self.job_lengths):
            seq_counts = self._per_len_counts[L]
            options: List[Tuple[int, int]] = []
            for mask, cnt in enumerate(seq_counts):
                if cnt == 0:
                    continue
                rest = self._count_remaining_jobs(idx + 1, missing & ~mask)
                if rest:
                    options.append((mask, cnt * rest))
            if not options:
                raise RuntimeError("No feasible machine assignment — logic error")
            weights = [w for _, w in options]
            chosen_mask = self.rng.choices([m for m, _ in options], weights)[0]
            sequences.append(self._sample_seq(L, chosen_mask))
            missing &= ~chosen_mask
        assert missing == 0
        return sequences

    # ----- sample concrete sequence with given coverage mask -----
    def _sample_seq(self, L: int, cover_mask: int) -> List[int]:
        m = self.m
        @lru_cache(maxsize=None)
        def ways(pos: int, last: int | None, mask: int) -> int:
            if pos == L:
                return int(mask == 0)
            total = 0
            for machine in range(m):
                if machine == last:
                    continue
                total += ways(pos + 1, machine, mask & ~(1 << machine))
            return total
        seq, last, rem = [], None, cover_mask
        for pos in range(L):
            cand, wts = [], []
            for machine in range(m):
                if machine == last:
                    continue
                w = ways(pos + 1, machine, rem & ~(1 << machine))
                if w:
                    cand.append(machine)
                    wts.append(w)
            chosen = self.rng.choices(cand, wts)[0]
            seq.append(chosen)
            rem &= ~(1 << chosen)
            last = chosen
        assert rem == 0
        return seq

# ---------------------------------------------------------------------------
# 3) COP generator (total_tasks chosen internally)
# ---------------------------------------------------------------------------

def generate_random_jssp_cop(
    *,
    num_jobs: int,
    num_machines: int,
    min_tasks_per_job: int,
    max_tasks_per_job: int,
    min_task_time: int,
    max_task_time: int,
    problem_id: str | None = None,
    rng: random.Random | None = None,
) -> JobShopSchedulingProblem:
    rng = rng or random.Random()
    lower = max(num_jobs * min_tasks_per_job, num_machines)
    upper = num_jobs * max_tasks_per_job
    if lower > upper:
        raise ValueError("num_machines too large for given job/task bounds")
    total_tasks = rng.randint(lower, upper)

    job_lengths = _sample_job_lengths(n=num_jobs, k=min_tasks_per_job, l=max_tasks_per_job, total=total_tasks, rng=rng)
    seq_sampler = _ExactMachineSampler(job_lengths=job_lengths, num_machines=num_machines, rng=rng)
    machine_seqs = seq_sampler.sample()

    jobs: List[Job] = []
    for jid, machines in enumerate(machine_seqs):
        tasks = [Task(machine_id=m, duration=rng.randint(min_task_time, max_task_time)) for m in machines]
        jobs.append(Job(job_id=jid, tasks=tasks))

    return JobShopSchedulingProblem(problem_id=problem_id or str(uuid.uuid4()), jobs=jobs)

# ---------------------------------------------------------------------------
# 4) CSP generator (adds makespan target)
# ---------------------------------------------------------------------------

def generate_random_jssp_csp(
    *,
    num_jobs: int,
    num_machines: int,
    min_tasks_per_job: int,
    max_tasks_per_job: int,
    min_task_time: int,
    max_task_time: int,
    satisfiable_makespan: bool = True,
    problem_id: str | None = None,
    rng: random.Random | None = None,
) -> JobShopSchedulingProblem:
    cop = generate_random_jssp_cop(
        num_jobs=num_jobs,
        num_machines=num_machines,
        min_tasks_per_job=min_tasks_per_job,
        max_tasks_per_job=max_tasks_per_job,
        min_task_time=min_task_time,
        max_task_time=max_task_time,
        problem_id=problem_id,
        rng=rng,
    )
    sol = solve_job_shop_scheduling(cop)
    if sol is None:
        raise RuntimeError("Solver failed; cannot build CSP instance")
    opt = sol.makespan
    rng = rng or random.Random()
    if satisfiable_makespan:
        target = rng.randint(opt, opt * MAKESPAN_TARGET_FACTOR)
    else:
        target = rng.randint(max(1, opt // MAKESPAN_TARGET_FACTOR), opt - 1)
    return JobShopSchedulingProblem(problem_id=problem_id or str(uuid.uuid4()), jobs=cop.jobs, makespan_target=target)


# ---------------------------------------------------------------------------
# 4) JobShopProblemGenerator class ------------------------------------------
# ---------------------------------------------------------------------------

def _validate_ranges(
    jobs_range: Tuple[int, int],
    machines_range: Tuple[int, int],
    tasks_range: Tuple[int, int],
) -> None:
    """
    Ensure there exists at least one (jobs, machines, tasks) triple
    that satisfies both feasibility constraints *for the worst case*:

      1) max_machines ≤ min_jobs × max_tasks
      2) min_jobs × min_tasks ≥ min_machines

    Raises ValueError with an actionable message if impossible.
    """
    j_lo, _ = jobs_range
    m_lo, m_hi = machines_range
    t_min, t_max = tasks_range

    # Constraint 1 — guarantee *every* machines draw is legal
    if m_hi > j_lo * t_max:
        raise ValueError(
            f"num_machines upper-bound {m_hi} is too large for "
            f"min_num_jobs={j_lo} with max_tasks_per_job={t_max}. "
            "Lower max_num_machines or raise min_num_jobs / max_tasks_per_job."
        )

    # Constraint 2 — guarantee *every* jobs draw can cover min machines
    if j_lo * t_min < m_lo:
        needed = math.ceil(m_lo / j_lo)
        raise ValueError(
            f"min_tasks_per_job must be ≥ {needed} to ensure {j_lo} jobs "
            f"can cover min_num_machines={m_lo}. "
            "Increase min_tasks_per_job or lower min_num_machines."
        )
    
def _sample_j_m_t(
    *,
    jobs_range: Tuple[int, int],
    machines_range: Tuple[int, int],
    tasks_range: Tuple[int, int],
    rng: random.Random,
) -> Tuple[int, int, int, int]:
    """
    Assumes ranges have already been validated by _validate_ranges.
    Returns (num_jobs, num_machines, min_tasks_per_job_eff, max_tasks_per_job_eff).
    """
    j_lo, j_hi = jobs_range
    m_lo, m_hi = machines_range
    t_min, t_max = tasks_range

    num_jobs = rng.randint(j_lo, j_hi)

    m_hi_eff = min(m_hi, num_jobs * t_max)
    num_machines = rng.randint(m_lo, m_hi_eff)

    t_min_eff = max(t_min, math.ceil(num_machines / num_jobs))
    return num_jobs, num_machines, t_min_eff, t_max
    
class JobShopProblemCOPGenerator(ProblemGenerator[JobShopSchedulingProblem]):
    def __init__(
        self,
        min_num_jobs: int,
        max_num_jobs: int,
        min_num_machines: int,
        max_num_machines: int,
        min_tasks_per_job: int,
        max_tasks_per_job: int,
        min_task_time: int,
        max_task_time: int,
        seed: int = 42,
    ):
        _validate_ranges(
            (min_num_jobs, max_num_jobs),
            (min_num_machines, max_num_machines),
            (min_tasks_per_job, max_tasks_per_job)
        )

        self.min_num_jobs = min_num_jobs
        self.max_num_jobs = max_num_jobs
        self.min_num_machines = min_num_machines
        self.max_num_machines = max_num_machines
        self.min_tasks_per_job = min_tasks_per_job
        self.max_tasks_per_job = max_tasks_per_job
        self.min_task_time = min_task_time
        self.max_task_time = max_task_time
        self.rng = random.Random(seed)

    def generate_problem(self, problem_id: Optional[str] = None) -> JobShopSchedulingProblem:
        # The problem_id passed here is the one constructed in generate_problems (e.g., "MyBase_sample_1")
        # This ID is then passed to the JobShopSchedulingProblem constructor.
        num_jobs, num_machines, cur_min_tasks_per_job, cur_max_tasks_per_job = _sample_j_m_t(
            jobs_range=(self.min_num_jobs, self.max_num_jobs),
            machines_range=(self.min_num_machines, self.max_num_machines),
            tasks_range=(self.min_tasks_per_job, self.max_tasks_per_job),
            rng=self.rng
        )
        return generate_random_jssp_cop(
            num_jobs=num_jobs,
            num_machines=num_machines,
            min_tasks_per_job=cur_min_tasks_per_job,
            max_tasks_per_job=cur_max_tasks_per_job,
            min_task_time=self.min_task_time,
            max_task_time=self.max_task_time,
            problem_id=problem_id,
            rng=self.rng,
        )

class JobShopProblemCSPGenerator(ProblemGenerator[JobShopSchedulingProblem]):
    def __init__(
        self,
        min_num_jobs: int,
        max_num_jobs: int,
        min_num_machines: int,
        max_num_machines: int,
        min_tasks_per_job: int,
        max_tasks_per_job: int,
        min_task_time: int,
        max_task_time: int,
        satisfiable_makespan: bool = True,
        seed: int = 42,
    ):
        _validate_ranges(
            (min_num_jobs, max_num_jobs),
            (min_num_machines, max_num_machines),
            (min_tasks_per_job, max_tasks_per_job)
        )

        self.min_num_jobs = min_num_jobs
        self.max_num_jobs = max_num_jobs
        self.min_num_machines = min_num_machines
        self.max_num_machines = max_num_machines
        self.min_tasks_per_job = min_tasks_per_job
        self.max_tasks_per_job = max_tasks_per_job
        self.min_task_time = min_task_time
        self.max_task_time = max_task_time
        self.satisfiable_makespan = satisfiable_makespan
        self.rng = random.Random(seed)


    def generate_problem(self, problem_id: Optional[str] = None) -> JobShopSchedulingProblem:
        num_jobs, num_machines, cur_min_tasks_per_job, cur_max_tasks_per_job = _sample_j_m_t(
            jobs_range=(self.min_num_jobs, self.max_num_jobs),
            machines_range=(self.min_num_machines, self.max_num_machines),
            tasks_range=(self.min_tasks_per_job, self.max_tasks_per_job),
            rng=self.rng
        )
        return generate_random_jssp_csp(
            num_jobs=num_jobs,
            num_machines=num_machines,
            min_tasks_per_job=cur_min_tasks_per_job,
            max_tasks_per_job=cur_max_tasks_per_job,
            min_task_time=self.min_task_time,
            max_task_time=self.max_task_time,
            satisfiable_makespan=self.satisfiable_makespan,
            problem_id=problem_id,
            rng=self.rng,
        )

