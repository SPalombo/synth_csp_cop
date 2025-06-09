import random

# ─── 2.1. Define the template lists ─────────────────────────────────────────────

CSP_TEMPLATES = [
    # Template CSP‐1 (Revised)
    """You are given a job shop scheduling problem with the following jobs:
{jobs_description}
The goal is to schedule all tasks so that everything finishes by time {makespan_target}.

• If it is not possible to meet this deadline, reply with exactly:
Not feasible

• If it is possible, provide the schedule for each job (in ascending job ID order), one per line, using this format:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …""",

    # Template CSP‐2 (Revised)
    """You are given the following jobs, where each tuple is (machine_id, duration):
{jobs_description}
Is there a way to schedule all tasks so they finish by time {makespan_target}?

- If it is not possible, respond with exactly:
Not feasible

- If it is possible, write the schedule for each job (in ascending job ID order), one per line, like this:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …""",

    # Template CSP‐3 (Revised)
    """Here is a job shop scheduling problem:
{jobs_description}
All tasks must be completed by time {makespan_target}.

If you cannot produce a schedule that meets this requirement, respond with exactly:
Not feasible

If you can, provide the schedule for each job (in ascending job ID order), using this format:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …""",

    # Template CSP‐4 (Revised)
    """Schedule the following jobs, making sure to run the tasks in the given order:
{jobs_description}
All jobs must be completed by time {makespan_target}.

• If there is no schedule that meets this deadline, reply with exactly:
Not feasible

• If it is possible, list the schedule for each job (in ascending job ID order), one per line, as follows:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …""",

    # Template CSP‐5 (Revised)
    """You are given this job shop instance:
{jobs_description}
Find a schedule that completes all tasks by time {makespan_target}.

• If this is not possible, reply with exactly:
Not feasible

• If it is possible, write the schedule for each job (in ascending job ID order), one per line, like this:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …"""
]

COP_TEMPLATES = [
    # Template COP-1 (Revised)
    """You are given a job shop scheduling problem:
{jobs_description}
The goal is to schedule all tasks to minimize the total makespan.

• Provide the schedule for each job (in ascending job ID order), one per line, using this format:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …

• After listing all jobs, append:
Makespan: <M>""",

    # Template COP-2 (Revised)
    """Here are the jobs to schedule, where each task is (machine_id, duration):
{jobs_description}
Find a schedule that completes all jobs in the shortest possible time.

- For each job (in ascending ID order), write one line like:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …

- After all job lines, add:
Makespan: <M>""",

    # Template COP-3 (Revised)
    """You are given this job shop scheduling instance:
{jobs_description}
Determine a schedule that minimizes the overall completion time (makespan).

Provide one line per job (in ascending job ID order), formatted like this:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …

Then, write:
Makespan: <M>""",

    # Template COP-4 (Revised)
    """Schedule the following jobs to minimize the total makespan:
{jobs_description}
Each job should be listed (in ascending ID order) using this format:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …

At the end, include:
Makespan: <M>""",

    # Template COP-5 (Revised)
    """You are given a set of jobs with ordered tasks:
{jobs_description}
Find a schedule that minimizes the time at which all jobs finish.

• For each job (in ascending ID order), output one line like:
Job <i>: (machine_<m₁>, <start₁>, <end₁>), (machine_<m₂>, <start₂>, <end₂>), …

• After listing all jobs, write:
Makespan: <M>"""
]

# ─── 2.2. Helper: format the jobs list as a readable string ────────────────────────

def _format_jobs_description(jobs):
    """
    Convert jobs = [[(machine_id, duration), …], …] into a single string like:
      Job 0: Machine 0 for 2, then Machine 1 for 3; Job 1: Machine 1 for 2, then Machine 0 for 3
    """
    lines = []
    for job_idx, task_list in enumerate(jobs):
        # Build a “Machine X for D” sequence for this job
        pieces = [f"Machine {m} for {d}" for (m, d) in task_list]
        # Join with “then”
        line = f"Job {job_idx}: " + " then ".join(pieces)
        lines.append(line)
    # Join all jobs with “; ”
    return "; ".join(lines)

# ─── 2.3. Main function: pick a template and fill it in ────────────────────────────

def generate_jobshop_prompt(problem_dict):
    """
    Given a dictionary of the form:
      {
        'problem_id': '…',
        'problem_type': 'JobShopScheduling',
        'jobs': [[(machine, dur), …], …],
        'makespan_target': <int> or None,
        'derived_parameters': { … }
      }
    return a single string that is a natural‐language prompt.
    """
    jobs = problem_dict.get("jobs", [])
    makespan_target = problem_dict.get("makespan_target", None)

    # 1) Build the jobs‐description string
    jobs_desc = _format_jobs_description(jobs)

    # 2) Choose CSP vs. COP
    if makespan_target is not None:
        # CSP‐style
        template = random.choice(CSP_TEMPLATES)
        return template.format(
            jobs_description=jobs_desc,
            makespan_target=makespan_target
        )
    else:
        # COP‐style
        template = random.choice(COP_TEMPLATES)
        return template.format(jobs_description=jobs_desc)