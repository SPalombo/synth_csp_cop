import argparse
import json
import re
from pathlib import Path

import datasets


def load_csvs_to_dataset(path: Path):
    """
    Loads each CSV file in a given path into a pandas DataFrame and stores them
    in a dictionary where the key is the basename of the filename (without extension).

    Args:
        path (Path): The directory path containing the CSV files.

    Returns:
        dict: A dictionary where keys are CSV basenames and values are pandas DataFrames.
              Returns an empty dictionary if no CSV files are found or the path is invalid.
    """
    raw_datasets = {}
    if not path.is_dir(): # Replaced os.path.isdir with Path.is_dir()
        raise ValueError(f"Error: Path '{path}' is not a valid directory.")

    # Replaced os.listdir and os.path.join with Path.glob for elegance
    for filepath in path.glob("*.csv"):
        basename = filepath.stem # Replaced os.path.splitext with Path.stem
        try:
            # datasets.load_dataset expects a string path, so convert Path object to string
            raw_datasets[basename] = datasets.load_dataset("csv", data_files=str(filepath))['train']
        except Exception as e:
            print(f"Error loading '{filepath.name}': {e}") # Replaced os.path.basename with Path.name
    return raw_datasets

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # Changed type to lambda p: Path(p).expanduser() to read arguments as Path objects and handle '~'
    parser.add_argument('--dataset_dir', type=lambda p: Path(p).expanduser(), default='~/data/gsm8k')
    parser.add_argument('--output_dir', type=lambda p: Path(p).expanduser() if p else None, default=None)


    args = parser.parse_args()

    # args.dataset_dir is now a Path object
    raw_datasets = load_csvs_to_dataset(args.dataset_dir)

    # If output_dir is provided, ensure the directory exists
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True) # Create output directory if it doesn't exist

    # add a row to each data item that represents a unique id
    def make_map_fn(split):
        def process_fn(example, idx):
            example_solution = json.loads(example['example_solution'])
            problem = json.loads(example['problem'])

            data = {
                "data_source": 'jsp_full',
                "prompt": [{
                    "role": "user",
                    "content": example['prompt']
                }],
                "ability": "math",
                "reward_model": {
                    "style": "rule",
                    "ground_truth": json.dumps({
                        'example_solution': example_solution,
                        'problem': problem
                    })
                },
                "extra_info": {
                    'split': split,
                    'index': idx
                }
            }
            return data

        return process_fn

    for split, dataset in raw_datasets.items():
        mapped_dataset = dataset.map(function=make_map_fn(split), with_indices=True)
        if args.output_dir:
            mapped_dataset.to_parquet(args.output_dir / f'{split}.parquet')
        else:
            print(f"Warning: --output_dir was not provided. Skipping saving {split}.parquet.")