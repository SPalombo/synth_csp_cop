import argparse
import yaml
import random
import uuid
import warnings
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any, Tuple
import copy
import pandas as pd
import os

from csp_cop_src.nl_probem_generators.job_shop_scheduling_make_nl import generate_jobshop_prompt
from csp_cop_src.problems.base_problem import BaseProblem
from csp_cop_src.problem_generators.job_shop_scheduling_generator import JobShopProblemCOPGenerator, JobShopProblemCSPGenerator
from csp_cop_src.problem_generators.base_problem_generator import ProblemGenerator
from csp_cop_src.solvers.solve_job_shop_scheduling import solve_job_shop_scheduling

PROBLEM_GENERATOR_CLASSES: Dict[str, type[ProblemGenerator]] = {
    "JobShopProblemCOPGenerator": JobShopProblemCOPGenerator,
    "JobShopProblemCSPGenerator": JobShopProblemCSPGenerator,
}

def main():
    parser = argparse.ArgumentParser(description="Generate and split problems based on a YAML config.")
    parser.add_argument("--config", "-c", type=str, required=True,
                        help="Path to the YAML configuration file.")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save the generated dataset splits.")
    parser.add_argument("--dataset_name", type=str, required=True, help="Base name for the dataset files.")
    args = parser.parse_args()

    output_dir = args.output_dir
    dataset_name = args.dataset_name
    os.makedirs(output_dir, exist_ok=True)

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)

    # 1. Validate data_split proportions
    data_split = config.get('data_split', {})
    train_ratio = data_split.get('train', 0.0)
    val_ratio = data_split.get('val', 0.0)
    test_ratio = data_split.get('test', 0.0)

    total_ratio = train_ratio + val_ratio + test_ratio
    if not (0.999 <= total_ratio <= 1.001): # Allow for small floating point inaccuracies
        raise ValueError(f"Data split ratios must sum to 1.0. Current sum: {total_ratio}")
    print(f"Data split ratios validated: Train={train_ratio}, Val={val_ratio}, Test={test_ratio}")

    # List to hold instantiated generator objects along with their num_samples and prefix
    instantiated_generators: List[Tuple[ProblemGenerator, int, str]] = []

    # 2. Pre-check and Instantiate generators
    problem_generators_config = config.get('problem_generator', {})
    if not problem_generators_config:
        raise ValueError("No 'problem_generator' configurations found in the YAML.")

    for problem_type_key, generator_spec in problem_generators_config.items():
        # Check for required keys in the generator specification
        for required_key in ['class', 'num_samples', 'kwargs']:
            if required_key not in generator_spec:
                raise ValueError(
                    f"Missing required key '{required_key}' in generator configuration for '{problem_type_key}'."
                )

        class_name = generator_spec['class']
        num_samples = generator_spec['num_samples']
        kwargs = generator_spec['kwargs']

        if class_name not in PROBLEM_GENERATOR_CLASSES:
            raise ValueError(f"Unknown problem generator class: {class_name} for '{problem_type_key}'.")

        if not isinstance(num_samples, int) or num_samples <= 0:
            raise ValueError(
                f"'num_samples' for '{problem_type_key}' must be a positive integer. Got: {num_samples}"
            )
        if not isinstance(kwargs, dict):
            raise ValueError(
                f"'kwargs' for '{problem_type_key}' must be a dictionary. Got: {type(kwargs)}"
            )

        GeneratorClass = PROBLEM_GENERATOR_CLASSES[class_name]
        try:
            generator_instance = GeneratorClass(**kwargs)
            instantiated_generators.append((generator_instance, num_samples, problem_type_key))
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate generator '{class_name}' for '{problem_type_key}' "
                f"with kwargs {kwargs}: {e}"
            )

    print("\nAll problem generators successfully instantiated.")

    all_problems: List[BaseProblem] = []
    # 3. Generate problems using the instantiated generators
    for generator_instance, num_samples, prefix in instantiated_generators:
        print(f"Generating {num_samples} problems for '{prefix}' using {type(generator_instance).__name__}...")
        problems_for_type = generator_instance.generate_problems(num_samples, prefix=prefix)
        problem_nl_query_soln = []
        from csp_cop_src.validators.job_shop_scheduling_validator import validate_job_shop_solution
        for problem in problems_for_type:
            solution = solve_job_shop_scheduling(problem)
            is_valid, _, _ = validate_job_shop_solution(problem, solution)
            if not is_valid:
                breakpoint
            print(f"Problem {problem.problem_id} is valid")

            problem_dict = {
                'problem': problem.to_jsons(),
                'prompt': generate_jobshop_prompt(problem.to_dict()),
                'example_solution': solution.to_jsons()
            }
            problem_nl_query_soln.append(problem_dict)
        all_problems.extend(problem_nl_query_soln)
        print(f"Generated {len(problems_for_type)} problems for '{prefix}'.")
    print(f"\nTotal problems generated: {len(all_problems)}")

    # 4. Shuffle all problems
    random.shuffle(all_problems)
    print("All problems shuffled.")

    # 5. Create train, val, and test splits
    total_problems = len(all_problems)
    train_size = int(total_problems * train_ratio)
    val_size = int(total_problems * val_ratio)
    test_size = total_problems - train_size - val_size # Assign remaining to test to avoid rounding issues

    train_problems = all_problems[:train_size]
    val_problems = all_problems[train_size : train_size + val_size]
    test_problems = all_problems[train_size + val_size :]

    print(f"\nData split results:")
    print(f"  Train problems: {len(train_problems)}")
    print(f"  Validation problems: {len(val_problems)}")
    print(f"  Test problems: {len(test_problems)}")

    # Save splits to CSV files
    pd.DataFrame(train_problems).to_csv(os.path.join(output_dir, f"{dataset_name}_train.csv"), index=False)
    pd.DataFrame(val_problems).to_csv(os.path.join(output_dir, f"{dataset_name}_val.csv"), index=False)
    pd.DataFrame(test_problems).to_csv(os.path.join(output_dir, f"{dataset_name}_test.csv"), index=False)
    print(f"Saved train/val/test splits to {output_dir} with base name '{dataset_name}_<split>.csv'.")

    # You can now use train_problems, val_problems, test_problems for your downstream tasks.
    # For example, saving them to files or passing them to a model.

if __name__ == "__main__":
    main()