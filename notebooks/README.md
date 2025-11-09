# Notebooks guidance

This folder contains exploratory Jupyter notebooks for EDA. Use the modules in `src/` to
refactor repeated logic and keep notebooks concise and reproducible.

Examples

- To use the `DataCleaner` class inside a notebook:

```python
from src.cleaning import DataCleaner
dc = DataCleaner('..\/data\/benin-malanville.csv')
df_clean = dc.run(out_path='..\/data\/benin_clean.csv')
```

- To perform a cross-country comparison (after loading/cleaning each dataset):

```python
from src.compare import compare_countries
dfs = {'benin': df_benin_clean, 'togo': df_togo_clean}
summary = compare_countries(dfs)
display(summary)
```

Document non-obvious notebook logic with short inline comments and consider extracting
repeatable cells into `src/` modules so they can be unit-tested and reused.
