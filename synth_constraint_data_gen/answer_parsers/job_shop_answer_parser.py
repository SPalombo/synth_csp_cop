"""
Permissive parser for Job-Shop Scheduling answers returned by an LLM.

• Detects “Not feasible” early and returns an INFEASIBLE solution.
• Extracts an (optional) makespan via several heuristics.
• Recovers schedules written in the canonical format, a loose “triples
  after job-id” format, a JSON/dict block, or a simple table.
• Builds a JobShopSchedulingSolution with ScheduledTask objects.

Assumes the following classes are already available:

    from your_module import ScheduledTask, JobShopSchedulingSolution
"""

from __future__ import annotations
import re
import json
from typing import Dict, List, Optional

from csp_cop_src.solutions.job_shop_scheduling_solution import JobShopSchedulingSolution, ScheduledTask


# ───────────────────────────────────────────────────────────────────────────────
#  Regex helpers
# ───────────────────────────────────────────────────────────────────────────────

RE_NOT_FEASIBLE = re.compile(r'\bnot\s+feasible\b', re.I)

RE_MAKESPAN_LINE = re.compile(r'makespan[^0-9]*?(\d+)', re.I)          # Tier A
RE_STANDALONE_INT = re.compile(r'^\D*(\d+)\D*$', re.M)                 # Tier B
RE_MAKESPAN_JSON = re.compile(r'"optimal_makespan"\s*:\s*(\d+)', re.I) # Tier C

RE_JOB_CANON = re.compile(r'^job\s+(\d+)\s*[:\-]\s*(.*)$', re.I)
RE_TASK_CANON = re.compile(
    r'm(?:achine)?[_\s-]?(\d+)\s*,?\s*(\d+)\s*,?\s*(\d+)', re.I
)

# Loose: <job_id> <m> <s> <e> [<m> <s> <e>]…
RE_JOB_LOOSE = re.compile(r'\b(\d+)(?:\D+(\d+)\D+(\d+)\D+(\d+))+')

# Table row: 4+ integers, first changes only at row breaks
RE_TABLE_ROW = re.compile(r'(?:\d+\D+){3,}\d+')


# ───────────────────────────────────────────────────────────────────────────────
#  Low-level utilities
# ───────────────────────────────────────────────────────────────────────────────

def _build_tasks(triples: List[tuple[int, int, int]]):
    return [
        ScheduledTask(
            task_idx=i,
            machine_id=int(m),
            start=int(s),
            end=int(e)
        )
        for i, (m, s, e) in enumerate(triples)
    ]


def _safe_int(x: str) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


# ───────────────────────────────────────────────────────────────────────────────
#  Makespan detection
# ───────────────────────────────────────────────────────────────────────────────

def _find_makespan(txt: str) -> Optional[int]:
    # Tier A: explicit “Makespan …”
    if m := RE_MAKESPAN_LINE.search(txt):
        return int(m.group(1))

    # Tier B: stand-alone number lines near the tail (≤5 lines)
    tail = '\n'.join(txt.strip().splitlines()[-5:])
    if m := RE_STANDALONE_INT.search(tail):
        return int(m.group(1))

    # Tier C: JSON/dict representation
    if m := RE_MAKESPAN_JSON.search(txt):
        return int(m.group(1))

    return None


# ───────────────────────────────────────────────────────────────────────────────
#  Schedule extraction strategies
# ───────────────────────────────────────────────────────────────────────────────

def _parse_canonical(lines: List[str]) -> Optional[Dict[int, List[ScheduledTask]]]:
    schedule: Dict[int, List[ScheduledTask]] = {}
    for ln in lines:
        jmatch = RE_JOB_CANON.match(ln.strip())
        if not jmatch:
            continue
        jid = int(jmatch.group(1))
        task_part = jmatch.group(2)
        triples = [
            tuple(map(int, t))
            for t in RE_TASK_CANON.findall(task_part)
        ]
        if triples:
            schedule[jid] = _build_tasks(triples)

    return schedule or None


def _parse_loose(lines: List[str]) -> Optional[Dict[int, List[ScheduledTask]]]:
    # Consider only last 10 lines
    schedule: Dict[int, List[ScheduledTask]] = {}
    for ln in lines[-10:]:
        nums = list(map(int, re.findall(r'\d+', ln)))
        if len(nums) < 4:
            continue
        jid, rest = nums[0], nums[1:]
        if (len(rest) % 3) != 0:
            continue
        triples = [tuple(rest[i:i+3]) for i in range(0, len(rest), 3)]
        schedule[jid] = _build_tasks(triples)

    return schedule or None


def _parse_json(txt: str) -> Optional[Dict[int, List[ScheduledTask]]]:
    try:
        blob = json.loads(txt[txt.index('{'): txt.rindex('}') + 1])
    except Exception:
        return None

    schedule_raw = blob.get('schedule')
    if not isinstance(schedule_raw, dict):
        return None

    schedule = {
        int(jid): [
            ScheduledTask.from_dict(td)  # type: ignore[arg-type]
            for td in tlist
        ]
        for jid, tlist in schedule_raw.items()
    }
    return schedule


def _parse_table(lines: List[str]) -> Optional[Dict[int, List[ScheduledTask]]]:
    rows = [ln for ln in lines if RE_TABLE_ROW.search(ln)]
    if not rows:
        return None

    schedule: Dict[int, List[ScheduledTask]] = {}
    for ln in rows:
        nums = list(map(int, re.findall(r'\d+', ln)))
        if len(nums) < 4:
            continue
        # Assume format: job, machine, start, end
        jid, m, s, e = nums[:4]
        schedule.setdefault(jid, []).append((int(m), int(s), int(e)))

    # Convert triples → ScheduledTask
    if schedule:
        for jid, triples in schedule.items():
            schedule[jid] = _build_tasks(triples)
        return schedule
    return None


# ───────────────────────────────────────────────────────────────────────────────
#  Decide status
# ───────────────────────────────────────────────────────────────────────────────

def _decide_status(txt: str, makespan: Optional[int]) -> str:
    if makespan is not None and re.search(r'\boptimal\b', txt, re.I):
        return 'OPTIMAL'
    if makespan is not None:
        return 'FEASIBLE'
    return 'FEASIBLE'  # default when schedule exists


# ───────────────────────────────────────────────────────────────────────────────
#  Public API
# ───────────────────────────────────────────────────────────────────────────────

def parse_job_shop(
    txt: str,
    problem_id: str,
) -> JobShopSchedulingSolution:
    """
    Parse raw LLM text and return a JobShopSchedulingSolution.

    Raises ValueError if no feasible schedule is found and the answer
    did not declare the instance infeasible.
    """
    # 0. Not feasible?
    if RE_NOT_FEASIBLE.search(txt):
        return JobShopSchedulingSolution(
            problem_id=problem_id,
            status='INFEASIBLE',
            optimal_makespan=None,
            schedule={}
        )

    # 1. Makespan (optional)
    makespan = _find_makespan(txt)

    # 2. Try to parse a schedule
    lines = txt.splitlines()

    parsers = (_parse_canonical, _parse_loose, _parse_json, _parse_table)
    schedule: Optional[Dict[int, List[ScheduledTask]]] = None
    for p in parsers:
        schedule = p(lines if p is not _parse_json else txt)  # type: ignore[arg-type]
        if schedule:
            break

    if schedule is None:
        return None

    # 3. Fill in missing makespan
    if makespan is None:
        makespan = max(
            task.end for tasks in schedule.values() for task in tasks
        )

    # 4. Status
    status = _decide_status(txt, makespan)

    # 5. Build and return solution
    return JobShopSchedulingSolution(
        problem_id=problem_id,
        status=status,
        optimal_makespan=makespan,
        schedule=schedule
    )
