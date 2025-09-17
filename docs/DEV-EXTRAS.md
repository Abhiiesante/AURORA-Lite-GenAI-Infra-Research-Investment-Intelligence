# Developer Extras (Optional Dependencies)

Some scripts and workflows are optional and not required for running the API or tests. To support those, install the following extras in your virtual environment.

## Indexing script: `flows/index_search.py`
- pandas
- pyarrow (optional but recommended for faster CSV/Parquet IO)

Install:

```
pip install -r requirements-dev.txt
```

Or directly:

```
pip install pandas pyarrow
```

Notes:
- The script guards imports and will print a friendly message if `pandas` is not installed.
- These packages are not required for CI or unit tests.
