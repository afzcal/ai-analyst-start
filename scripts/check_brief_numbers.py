"""Check that every number in a run's brief.md appears in the result tables the script saved.

Run from the repo root:
    poetry run python scripts/check_brief_numbers.py outputs/<run>

Numbers not found in data/*.csv are then looked up in what analysis.py prints, and in
what review_checks.py prints if the run has one. Dates, file names and code are skipped.
"""

import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

NUMBER = re.compile(r"(?<![\w.])-?\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.,])-?\d+(?:\.\d+)?(?![\w])")


def numbers_in(text: str) -> list[str]:
    return NUMBER.findall(text)


def to_float(token: str) -> float:
    return float(token.replace(",", ""))


def table_values(run: Path) -> set[float]:
    values = set()
    for csv in sorted((run / "data").glob("*.csv")):
        frame = pd.read_csv(csv)
        for col in frame.columns:
            numeric = pd.to_numeric(frame[col], errors="coerce").dropna()
            values.update(float(v) for v in numeric)
    return values


def printed_values(script: Path) -> set[float]:
    if not script.exists():
        return set()
    out = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, check=True
    ).stdout
    return {to_float(t) for t in numbers_in(out)}


def matches(value: float, pool: set[float], decimals: int) -> bool:
    # A brief may round a table value, so compare at the brief's own precision.
    return any(round(v, decimals) == value for v in pool)


def main(run: Path) -> None:
    brief = (run / "brief.md").read_text()
    # Skip code spans, image links, dates and years, which are labels rather than results.
    text = re.sub(r"`[^`]*`|\]\([^)]*\)|\d{4}-\d{2}(?:-\d{2})?|\b20\d{2}\b", " ", brief)
    # Skip list numbers and figure or table labels.
    text = re.sub(r"(?m)^\s*\d+\.\s|\*\*(?:Figure|Table) \d+:\*\*", " ", text)
    tables = table_values(run)
    printed = printed_values(run / "analysis.py")
    review = printed_values(run / "review_checks.py")

    groups = {"result tables": [], "analysis.py output only": [], "review_checks.py output only": [], "not found": []}
    for line in text.splitlines():
        for token in numbers_in(line):
            decimals = len(token.split(".")[1]) if "." in token else 0
            value = to_float(token)
            if matches(value, tables, decimals) or matches(abs(value), tables, decimals):
                key = "result tables"
            elif matches(value, printed, decimals):
                key = "analysis.py output only"
            elif matches(value, review, decimals):
                key = "review_checks.py output only"
            else:
                key = "not found"
            groups[key].append((token, line.strip()[:90]))

    total = sum(len(v) for v in groups.values())
    print(f"{total} numbers in {run / 'brief.md'}")
    for key, items in groups.items():
        print(f"\n{key}: {len(items)}")
        if key != "result tables":
            for token, context in items:
                print(f"  {token:>10}  {context}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
