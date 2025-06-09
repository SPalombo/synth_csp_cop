import pandas as pd
import json
import os

from csp_cop_src.problems.job_shop_scheduling import JobShopSchedulingProblem
from csp_cop_src.solutions.job_shop_scheduling_solution import JobShopSchedulingSolution
from csp_cop_src.validators.job_shop_scheduling_validator import validate_job_shop_solution
from csp_cop_src.solutions.base_solution import SolutionStatus # Needed for potential direct status checks if required, and used internally by validator

# Determine the absolute path to the directory containing this script
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the data directory relative to this script
# Data is in: <script_dir>/../data/llm_training_data/job_shop_scheduling/
BASE_DATA_PATH = os.path.join(os.path.dirname(_SCRIPT_DIR), "data", "llm_training_data", "job_shop_scheduling")

CSV_FILES = [
    "jsp_full_test.csv",
    "jsp_full_train.csv",
    "jsp_full_val.csv",
]

def main():
    overall_valid_count = 0
    overall_invalid_count = 0
    overall_error_parsing_count = 0 # Count entries that couldn't be parsed

    for csv_file_name in CSV_FILES:
        file_path = os.path.join(BASE_DATA_PATH, csv_file_name)
        print(f"Processing file: {file_path}")

        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            overall_error_parsing_count +=1 # Or a different counter for file not found
            continue

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
            overall_error_parsing_count +=1
            continue

        file_valid_count = 0
        file_invalid_count = 0
        file_parsing_errors = 0

        for index, row in df.iterrows():
            try:
                problem_dict = json.loads(row['problem'])
                solution_dict = json.loads(row['example_solution'])

                problem = JobShopSchedulingProblem.from_dict(problem_dict)
                solution = JobShopSchedulingSolution.from_dict(solution_dict)

                is_valid, violations_count, error_details = validate_job_shop_solution(problem, solution)

                if is_valid:
                    file_valid_count += 1
                else:
                    file_invalid_count += 1
                    # print(f"  Row {index+2}: Invalid solution for problem {problem.problem_id}.")
                    # print(f"    Violations: {violations_count}")
                    # print(f"    Details: {error_details}")

            except json.JSONDecodeError as e:
                # print(f"  Row {index+2}: Error decoding JSON: {e}")
                file_parsing_errors += 1
            except KeyError as e:
                # print(f"  Row {index+2}: Missing expected column (e.g., 'problem' or 'example_solution'): {e}")
                file_parsing_errors += 1
            except ValueError as e: # Catch ValueErrors from from_dict or validator
                # print(f"  Row {index+2}: Error processing problem/solution data: {e}")
                file_parsing_errors += 1
            except Exception as e: # Catch-all for other unexpected errors
                # print(f"  Row {index+2}: An unexpected error occurred: {e}")
                file_parsing_errors += 1

        print(f"Finished processing {csv_file_name}:")
        print(f"  Valid solutions: {file_valid_count}")
        print(f"  Invalid solutions: {file_invalid_count}")
        print(f"  Rows with parsing/processing errors: {file_parsing_errors}")
        print("-" * 30)

        overall_valid_count += file_valid_count
        overall_invalid_count += file_invalid_count
        overall_error_parsing_count += file_parsing_errors

    print("\n" + "=" * 30)
    print("Overall Validation Summary:")
    print(f"  Total valid solutions: {overall_valid_count}")
    print(f"  Total invalid solutions: {overall_invalid_count}")
    print(f"  Total rows with parsing/processing errors: {overall_error_parsing_count}")
    print("=" * 30)

if __name__ == "__main__":
    # BASE_DATA_PATH is now defined globally and is absolute, so no complex path logic needed here.
    main()
