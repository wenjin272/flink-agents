#!/usr/bin/env python3
"""Data analysis helper script.

This script provides common data analysis utilities.
"""
import sys
from pathlib import Path


def load_and_summarize(file_path: str) -> None:
    """Load a data file and print summary statistics.

    Args:
        file_path: Path to the data file (CSV or JSON).
    """
    import pandas as pd

    path = Path(file_path)

    if path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif path.suffix == '.json':
        df = pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    print(f"\n=== Data Summary for {path.name} ===")
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"\nColumn Types:\n{df.dtypes}")
    print(f"\nMissing Values:\n{df.isnull().sum()}")
    print(f"\nSummary Statistics:\n{df.describe()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <data_file>")
        sys.exit(1)

    load_and_summarize(sys.argv[1])
