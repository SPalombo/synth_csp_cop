import json
from typing import Dict, Any, List, Optional
from csp_cop_src.solutions.base_solution import BaseSolution, SolutionStatus

class BinPackingSolution(BaseSolution):
    """
    Represents a solution to a Bin Packing Problem.
    """
    def __init__(self,
                 problem_id: str,
                 status: str,
                 num_bins_used: Optional[int],
                 bins: Dict[int, List[int]], # {bin_id: [item_idx1, item_idx2, ...]}
                 bin_contents_weights: Dict[int, List[int]], # {bin_id: [item_weight1, item_weight2, ...]}
                 ):
        """
        Initializes a Bin Packing Solution instance.

        Args:
            problem_id (str): The ID of the problem instance this is a solution for.
            status (str): The status of the solution.
            num_bins_used (Optional[int]): The number of bins used in this solution.
            bins (Dict[int, List[int]]): A dictionary mapping bin_id to a list of item_indices it contains.
            bin_contents_weights (Dict[int, List[int]]): A dictionary mapping bin_id to a list of actual item weights.
                                                         This is redundant if `item_sizes` from the problem is easily
                                                         available, but useful for quick validation/display.
        """
        super().__init__(problem_id, status, num_bins_used) # num_bins_used is the optimal_value for COP
        if not isinstance(bins, dict) or not all(isinstance(k, int) and isinstance(v, list) for k, v in bins.items()):
            raise ValueError("bins must be a dictionary mapping int bin_id to list of item_indices.")
        if not isinstance(bin_contents_weights, dict) or not all(isinstance(k, int) and isinstance(v, list) for k, v in bin_contents_weights.items()):
             raise ValueError("bin_contents_weights must be a dictionary mapping int bin_id to list of item_weights.")

        self.num_bins_used = num_bins_used # Alias for clarity
        self.bins = bins
        self.bin_contents_weights = bin_contents_weights

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Bin Packing solution instance to a dictionary."""
        return {
            "solution_type": "BinPacking",
            "problem_id": self.problem_id,
            "status": self.status,
            "num_bins_used": self.num_bins_used,
            "bins": self.bins,
            "bin_contents_weights": self.bin_contents_weights,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Creates a Bin Packing solution instance from a dictionary."""
        if data.get("solution_type") != "BinPacking":
            raise ValueError("Invalid solution type for BinPackingSolution.")
        return cls(
            problem_id=data["problem_id"],
            status=data["status"],
            num_bins_used=data["num_bins_used"],
            bins={int(k): v for k, v in data["bins"].items()}, # Ensure keys are ints
            bin_contents_weights={int(k): v for k, v in data["bin_contents_weights"].items()} # Ensure keys are ints
        )