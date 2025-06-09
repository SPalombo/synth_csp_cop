import random
import warnings
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from csp_cop_src.problems.base_problem import BaseProblem
import uuid

ProblemType = TypeVar("ProblemType", bound=BaseProblem) # Constraint ProblemType to be a subclass of BaseProblem
MAX_DUPLICATE_RETRIES = 5 # Maximum number of retries if a duplicate problem is generated

class ProblemGenerator(ABC, Generic[ProblemType]):
    def __init__(self) -> None:
        return

    @abstractmethod
    def generate_problem(self, problem_id: Optional[str] = None) -> ProblemType:
        pass

    def generate_problems(self, num_samples: int, prefix: Optional[str] = None) -> List[ProblemType]:
        """
        Generates a list of problem instances, checking for duplicates based on hash.
        Retries generation if a duplicate is found, up to MAX_DUPLICATE_RETRIES.
        If duplicates persist, a warning is issued, and the duplicate is included.

        Returns:
            A list containing num_samples problem instances.
        """
        problems: List[ProblemType] = []
        seen_hashes = set()

        for i in range(num_samples):
            # Determine the problem_id for the current sample *before* retries
            if prefix is not None:
                current_problem_id_for_sample = f"{prefix}_{i}"
            else:
                current_problem_id_for_sample = str(uuid.uuid4())

            generated_problem: Optional[ProblemType] = None
            for attempt in range(MAX_DUPLICATE_RETRIES + 1):
                candidate_problem = self.generate_problem(problem_id=current_problem_id_for_sample)
                problem_hash = hash(candidate_problem)

                if problem_hash not in seen_hashes:
                    seen_hashes.add(problem_hash)
                    generated_problem = candidate_problem
                    break  # Unique problem found
                else:
                    if attempt == MAX_DUPLICATE_RETRIES:
                        warnings.warn(
                            f"Failed to generate a unique problem for {current_problem_id_for_sample} "
                            f"after {MAX_DUPLICATE_RETRIES} retries. Adding duplicate.",
                            RuntimeWarning
                        )
                        generated_problem = candidate_problem # Add the duplicate
                        break

            if generated_problem is not None:
                problems.append(generated_problem)
            else:
                warnings.warn(
                    f"Unexpected: No problem was selected for {current_problem_id_for_sample}. "
                    "This might indicate an issue in generation logic.",
                    RuntimeWarning
                )

        return problems
