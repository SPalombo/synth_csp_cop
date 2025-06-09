import json
from typing import Dict, Any, List, Optional
from csp_cop_src.solutions.base_solution import BaseSolution, SolutionStatus
# Assuming Job and Task classes are available for internal structure,
# but for JSON, we'll keep it simple as tuples.
# from csp_cop_src.problems.job_shop_scheduling import Job, Task # Not strictly needed for solution, but can be useful

class ScheduledTask:
    """
    Represents a scheduled task in the solution schedule.
    """
    def __init__(self, task_idx: int, machine_id: int, start: int, end: int, duration: Optional[int] = None):
        self.task_idx = task_idx
        self.machine_id = machine_id
        self.start = start
        self.end = end
        self.duration = duration if duration is not None else (end - start)

    def to_dict(self) -> Dict[str, int]:
        return {
            "task_idx": self.task_idx,
            "machine_id": self.machine_id,
            "start": self.start,
            "end": self.end,
            "duration": self.duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]):
        return cls(
            task_idx=data["task_idx"],
            machine_id=data["machine_id"],
            start=data["start"],
            end=data["end"],
            duration=data.get("duration")
        )

class JobShopSchedulingSolution(BaseSolution):
    """
    Represents a solution to a Job-Shop Scheduling Problem.
    """
    def __init__(self,
                 problem_id: str,
                 status: str,  # SolutionStatus
                 optimal_makespan: Optional[int],
                 schedule: Dict[int, List[ScheduledTask]],
                 ):
        """
        Initializes a Job-Shop Scheduling Solution instance.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (SolutionStatus): The status of the solution (e.g., OPTIMAL, FEASIBLE, INFEASIBLE).
            optimal_makespan (Optional[int]): The makespan achieved by this solution.
            schedule (Dict[int, List[ScheduledTask]]): A dictionary where keys are job_ids
                                                        and values are lists of ScheduledTask objects.
        """
        super().__init__(problem_id, status, optimal_makespan)
        if not isinstance(schedule, dict):
            raise ValueError("schedule must be a dictionary.")
        # Validate that all values are lists of ScheduledTask
        for job_id, tasks in schedule.items():
            if not isinstance(tasks, list) or not all(isinstance(t, ScheduledTask) for t in tasks):
                raise ValueError("Each job's schedule must be a list of ScheduledTask objects.")
        self.schedule = schedule
        self.makespan = optimal_makespan # Alias for clarity

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Job-Shop Scheduling solution instance to a dictionary."""
        # Convert schedule to dict of lists of dicts
        schedule_dict = {
            int(job_id): [task.to_dict() for task in tasks]
            for job_id, tasks in self.schedule.items()
        }
        return {
            "solution_type": "JobShopScheduling",
            "problem_id": self.problem_id,
            "status": self.status,
            "optimal_makespan": self.makespan,
            "schedule": schedule_dict,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Job-Shop Scheduling solution instance from a dictionary."""
        if data.get("solution_type") != "JobShopScheduling":
            raise ValueError("Invalid solution type for JobShopSchedulingSolution.")
        # Convert schedule dict of lists of dicts to dict of lists of ScheduledTask
        raw_schedule = data["schedule"]
        schedule = {
            int(job_id): [ScheduledTask.from_dict(task_dict) for task_dict in tasks]
            for job_id, tasks in raw_schedule.items()
        }
        return cls(
            problem_id=data["problem_id"],
            status=data["status"],
            optimal_makespan=data["optimal_makespan"],
            schedule=schedule
        )