import json

from csp_cop_src.problems.job_shop_scheduling import JobShopSchedulingProblem
from csp_cop_src.answer_parsers.job_shop_answer_parser import parse_job_shop
from csp_cop_src.validators.job_shop_scheduling_validator import validate_job_shop_solution


def compute_score(solution_str, ground_truth):
    """The scoring function for GSM8k.

    Reference: Trung, Luong, et al. "Reft: Reasoning with reinforced fine-tuning." Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). 2024.

    Args:
        solution_str: the solution text
        ground_truth: the ground truth
        method: the method to extract the solution, choices are 'strict' and 'flexible'
        format_score: the score for the format
        score: the score for the correct answer
    """
    model_solution = parse_job_shop(solution_str)
    if model_solution is None:
        return 0

    # Expected to be a dict with keys "example_solution" and "problem"
    ground_truth = json.loads(ground_truth)
    valid_solution, _, _ = validate_job_shop_solution(
        JobShopSchedulingProblem.from_json(ground_truth['problem']),
        model_solution
    )
    return int(valid_solution)