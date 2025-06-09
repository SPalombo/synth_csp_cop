import json
from typing import List, Dict, Any, Tuple
from csp_cop_src.problems.base_problem import BaseProblem

class Task:
    """
    Represents a single task within a job in Job-Shop Scheduling.
    A task is performed on a specific machine for a given duration.
    """
    def __init__(self, machine_id: int, duration: int):
        if not isinstance(machine_id, int) or machine_id < 0:
            raise ValueError("machine_id must be a non-negative integer.")
        if not isinstance(duration, int) or duration <= 0:
            raise ValueError("duration must be a positive integer.")
        self.machine_id = machine_id
        self.duration = duration

    def to_tuple(self) -> Tuple[int, int]:
        """Converts the Task object to a (machine_id, duration) tuple."""
        return (self.machine_id, self.duration)

    @classmethod
    def from_tuple(cls, data_tuple: Tuple[int, int]):
        """Creates a Task object from a (machine_id, duration) tuple."""
        if not (isinstance(data_tuple, tuple) and len(data_tuple) == 2):
            raise ValueError("Task data must be a tuple of (machine_id, duration).")
        return cls(machine_id=data_tuple[0], duration=data_tuple[1])

    def __repr__(self):
        return f"Task(machine_id={self.machine_id}, duration={self.duration})"

    def __eq__(self, other):
        if not isinstance(other, Task):
            return NotImplemented
        return self.machine_id == other.machine_id and self.duration == other.duration

class Job:
    """
    Represents a single job in Job-Shop Scheduling, consisting of a sequence of tasks.
    """
    def __init__(self, job_id: int, tasks: List[Task]):
        if not isinstance(job_id, int) or job_id < 0:
            raise ValueError("job_id must be a non-negative integer.")
        if not isinstance(tasks, list) or not all(isinstance(t, Task) for t in tasks):
            raise ValueError("tasks must be a list of Task objects.")
        if not tasks:
            raise ValueError("A job must have at least one task.")
        self.job_id = job_id
        self.tasks = tasks

    def to_list_of_tuples(self) -> List[Tuple[int, int]]:
        """Converts the Job object to a list of (machine_id, duration) tuples."""
        return [task.to_tuple() for task in self.tasks]

    @classmethod
    def from_list_of_tuples(cls, job_id: int, data_list: List[Tuple[int, int]]):
        """Creates a Job object from a list of (machine_id, duration) tuples."""
        if not (isinstance(data_list, list) and all(isinstance(t, tuple) and len(t) == 2 for t in data_list)):
            raise ValueError("Job data must be a list of (machine_id, duration) tuples.")
        tasks = [Task.from_tuple(t_tuple) for t_tuple in data_list]
        return cls(job_id=job_id, tasks=tasks)

    def __repr__(self):
        return f"Job(job_id={self.job_id}, tasks={self.tasks})"

    def __eq__(self, other):
        if not isinstance(other, Job):
            return NotImplemented
        return self.job_id == other.job_id and self.tasks == other.tasks

class JobShopSchedulingProblem(BaseProblem):
    """
    Represents an instance of a Job-Shop Scheduling Problem.
    Now uses explicit Task and Job classes for clearer definition.
    """
    def __init__(self, problem_id: str, jobs: List[Job], makespan_target: int = None):
        """
        Initializes a Job-Shop Scheduling Problem instance.

        Args:
            problem_id (str): A unique identifier for this problem instance.
            jobs (List[Job]): A list of Job objects, where each Job contains a sequence of Task objects.
            makespan_target (int, optional): An optional target for the makespan (for CSP variants).
                                             If not provided, it's typically a COP problem aiming to minimize makespan.
        """
        super().__init__(problem_id, {}) # Parameters will be derived from jobs
        if not isinstance(jobs, list) or not all(isinstance(j, Job) for j in jobs):
            raise ValueError("jobs must be a list of Job objects.")
        if not jobs:
            raise ValueError("The problem must contain at least one job.")
        self.jobs = jobs
        self.num_jobs = len(jobs)
        self.num_machines = self._get_num_machines()
        self.makespan_target = makespan_target
        self.parameters = self._derive_parameters()

    def _get_num_machines(self) -> int:
        """Determines the total number of unique machines across all jobs."""
        machines = set()
        for job in self.jobs:
            for task in job.tasks:
                machines.add(task.machine_id)
        return len(machines)

    def _derive_parameters(self) -> Dict[str, Any]:
        """Derives a comprehensive set of parameters from the jobs data."""
        total_tasks = sum(len(job.tasks) for job in self.jobs)
        total_duration = sum(task.duration for job in self.jobs for task in job.tasks)

        jobs_for_json = [job.to_list_of_tuples() for job in self.jobs]

        parameters = {
            "num_jobs": self.num_jobs,
            "num_machines": self.num_machines,
            "total_tasks": total_tasks,
            "total_duration_sum": total_duration,
            "jobs_description": jobs_for_json, # Store simplified representation in parameters for JSON
        }
        if self.makespan_target is not None:
            parameters["makespan_target"] = self.makespan_target
            parameters["problem_type"] = "CSP"
        else:
            parameters["problem_type"] = "COP"
        return parameters

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Job-Shop Scheduling problem instance to a dictionary.
        The 'jobs' key will contain the simplified list of lists of tuples representation.
        """
        jobs_as_tuples = [job.to_list_of_tuples() for job in self.jobs]
        return {
            "problem_id": self.problem_id,
            "problem": "JobShopScheduling",
            "jobs": jobs_as_tuples, # Storing as list of lists of tuples for JSON
            "makespan_target": self.makespan_target,
            "derived_parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Creates a Job-Shop Scheduling problem instance from a dictionary.
        Converts the list of lists of tuples back into Job and Task objects.
        """
        if data.get("problem") != "JobShopScheduling":
            raise ValueError("Invalid problem type for JobShopSchedulingProblem.")

        jobs_raw = data["jobs"] # This will be List[List[List[int]]] after JSON deserialization
        jobs_objects = []
        for i, job_tasks_list in enumerate(jobs_raw): # job_tasks_list is List[List[int]]
            # Convert the inner lists (representing tasks) to tuples
            tasks_as_tuples_for_job = [tuple(task_data) for task_data in job_tasks_list]
            jobs_objects.append(Job.from_list_of_tuples(job_id=i, data_list=tasks_as_tuples_for_job))

        return cls(
            problem_id=data["problem_id"],
            jobs=jobs_objects,
            makespan_target=data.get("makespan_target")
        )

    def _normalized_data(self):
        # Canonicalize jobs: sort by job_id, and within each job, sort tasks by (machine_id, duration)
        jobs_norm = tuple(
            (job.job_id, tuple(sorted((task.machine_id, task.duration) for task in job.tasks)))
            for job in sorted(self.jobs, key=lambda j: j.job_id)
        )
        return {
            'jobs': jobs_norm,
            'makespan_target': self.makespan_target
        }
