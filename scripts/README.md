# Scripts

## check_brief_numbers.py

Checks that every number in a run's `brief.md` comes from the run's saved result tables (`data/*.csv`). A number that is not in a table is then looked up in what `analysis.py` prints, and in what `review_checks.py` prints if the run has one. Anything left is listed with its line, so you can see whether it is a label (such as "3 months") or a number with no source.

Run it from the repo root:

```bash
poetry run python scripts/check_brief_numbers.py outputs/<run folder>
```

It reruns `analysis.py` and `review_checks.py` to read their output, which rewrites the run's tables and charts with the same values.
