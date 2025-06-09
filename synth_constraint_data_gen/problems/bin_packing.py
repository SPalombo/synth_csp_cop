from typing import List, Dict, Any
from csp_cop_src.problems.base_problem import BaseProblem

class BinPackingProblem(BaseProblem):
    """
    Represents an instance of a Bin Packing Problem.
    """
    def __init__(self, problem_id: str, bin_capacity: int, item_sizes: List[int], num_bins_target: int = None):
        super().__init__(problem_id, {})
        if not isinstance(bin_capacity, int) or bin_capacity <= 0:
            raise ValueError("bin_capacity must be a positive integer.")
        if not isinstance(item_sizes, list) or not all(isinstance(s, int) and s > 0 for s in item_sizes):
            raise ValueError("item_sizes must be a list of positive integers.")

        self.bin_capacity = bin_capacity
        self.item_sizes = item_sizes
        self.num_bins_target = num_bins_target
        self.num_items = len(item_sizes)
        self.total_item_size = sum(item_sizes)
        self.parameters = self._derive_parameters()

    def _derive_parameters(self) -> Dict[str, Any]:
        parameters = {
            "num_items": self.num_items,
            "bin_capacity": self.bin_capacity,
            "total_item_size": self.total_item_size,
            "average_item_size": round(self.total_item_size / self.num_items, 2) if self.num_items > 0 else 0,
            "item_sizes_list": self.item_sizes # Can be useful for NL generation
        }
        if self.num_bins_target is not None:
            parameters["num_bins_target"] = self.num_bins_target
            parameters["problem_type"] = "CSP"
        else:
            parameters["problem_type"] = "COP" # Minimize number of bins
        return parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "problem": "BinPacking",
            "bin_capacity": self.bin_capacity,
            "item_sizes": self.item_sizes,
            "num_bins_target": self.num_bins_target,
            "derived_parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        if data.get("problem") != "BinPacking":
            raise ValueError("Invalid problem type for BinPackingProblem.")
        return cls(
            problem_id=data["problem_id"],
            bin_capacity=data["bin_capacity"],
            item_sizes=data["item_sizes"],
            num_bins_target=data.get("num_bins_target")
        )

    def _normalized_data(self):
        return {
            'bin_capacity': self.bin_capacity,
            'item_sizes': tuple(sorted(self.item_sizes)),
            'num_bins_target': self.num_bins_target
        }