---
name: data-analysis
description: Analyze and process datasets using Python. Use when working with CSV, JSON data, or when the user mentions data analysis, statistics, or visualization.
license: Apache-2.0
compatibility: Requires python3 with pandas and matplotlib
---

# Data Analysis Skill

This skill provides guidance for analyzing and processing datasets.

## When to Use

Use this skill when:
- Analyzing CSV or JSON data files
- Computing statistics or aggregations
- Creating data visualizations
- Cleaning or transforming data

## Steps

1. **Load the Data**
   - Use `pandas.read_csv()` or `pandas.read_json()` to load data
   - Check data shape and types with `df.info()` and `df.head()`

2. **Explore the Data**
   - Compute summary statistics with `df.describe()`
   - Check for missing values with `df.isnull().sum()`
   - Identify unique values with `df.nunique()`

3. **Clean the Data**
   - Handle missing values (drop or impute)
   - Remove duplicates with `df.drop_duplicates()`
   - Convert data types as needed

4. **Analyze and Visualize**
   - Create plots using matplotlib or seaborn
   - Compute correlations with `df.corr()`
   - Group and aggregate data

## Example Code

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('data.csv')

# Summary statistics
print(df.describe())

# Correlation matrix
print(df.corr())

# Create a simple plot
df.plot(kind='bar')
plt.savefig('output.png')
```

## Common Issues

- **Encoding errors**: Try different encodings like 'utf-8', 'latin-1', or 'cp1252'
- **Memory issues**: Use `chunksize` parameter for large files
- **Date parsing**: Use `parse_dates` parameter for date columns
