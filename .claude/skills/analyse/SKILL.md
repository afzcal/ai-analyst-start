---
name: analyse
description: Answers a framed business question about Beam's data with aggregate queries to the database, built from the semantic layer in knowledge/beam/, and one pandas script that can be rerun, where every headline number carries its comparison. Use after a question has been framed, when it is time to compute the answer. Reads the frame note in the run folder under outputs/ and writes the queries, their results, the script, result tables and charts next to it.
user-invocable: true
allowed-tools: Read Bash Write Edit Glob AskUserQuestion mcp__course-db__list_tables mcp__course-db__execute_sql
argument-hint: "[path to the run folder under outputs/]"
---

You answer the framed question with code that can be rerun.

The failure you exist to prevent: a confident number with no baseline, or a number that came out of a chain of arithmetic written in prose that nobody can check. "Trial conversion is 50%" tells a reader nothing until it says 50% against what. And a number computed in the conversation cannot be rerun, reviewed or corrected. The answer might even be right. Nobody can tell.

So the model reasons and the code computes. You decide what to compute and what to compare it with. Queries saved in the run folder, and a script that reads their results, do every count, rate, check and chart.

## What this is NOT

- Not the brief. You report numbers on the CLI; the Deliver step writes the brief.
- Not the review. You run the checks your plan needs; the Validate step reviews the work.
- Not a notebook. The output is one script that runs top to bottom.
- Not a window into raw rows. You never print raw rows into the conversation: every query returns aggregates, and the script prints aggregates only.
- Not a data editor. You never write to the database or modify anything in the repo's `data/` folder.

## The rules

These hold in every act.

- **A number alone is not a finding.** Every headline number carries a comparison: a prior period, a segment, or a benchmark.
- **If no comparison exists, say "no comparison available".** Never invent a baseline to fill the gap.
- **Segment before you average** when the frame or a quirk suggests groups behave differently. An average over groups that move in opposite directions hides both.
- **Percentage points and relative percent are different numbers.** A rate going from 40% to 44% is up 4 percentage points and up 10% relative. Name which one you mean, every time.
- **Never trust a period that has not closed.** A month still in progress, or a trial still inside its 14 days, is not a result yet.
- **Use the semantic layer's definitions.** A measure or golden query in a YAML file in `knowledge/beam/` is used as written. Never redefine one, such as reading churn from `status` instead of `end_date`. If the question needs a number no YAML file defines, say so in the plan and define it there.

## Act 1: Find the question (the gate)

1. Find the run folder. Use the argument if given. Otherwise use the newest folder under `outputs/` that holds a `frame.md`.
2. Read `frame.md` for the question, the decision it informs, the audience, and what would change the decision.
3. If there is no frame note, ask with AskUserQuestion for the question and the decision it informs. Then write `outputs/<YYYY-MM-DD>_<slug>/frame.md` yourself before anything else, with the same fields the Frame step writes: question, decision, audience, what would change the decision, and the tables likely involved. Get the date with `date +%F`; never guess it.
4. Never proceed on a guessed question. You may confirm a question you infer; you may not assume one.

## Act 2: Load the context

1. Before any query, read every YAML file in `knowledge/beam/`, then `knowledge/beam/quirks.md` and `knowledge/beam/corrections.md`. A fact about one table can sit in another table's file.
2. If a table involved has no YAML file, run the profile skill on it first: read `.claude/skills/profile/SKILL.md` and follow it, then come back here.
3. Say in one line which quirks apply to this question, and which corrections, if any. Say in another which measures and golden queries you will use.

## Act 3: Plan

Write three to six bullets describing the computation. The plan must say:

- What each headline number is, the measure or golden query that defines it (by name), and the comparison it will carry (prior period, segment or benchmark), or that none exists. A number no YAML file defines gets its formula here, marked as defined in this plan.
- Which queries you will run, by name, and what each returns.
- How each applicable quirk is handled. For example: matured trials only; free plans excluded from churn; scheduled starts after today excluded; the September 2025 anomaly named if it enters a comparison.
- Which segments you will split by and why.
- Which checks will run, in SQL and in the script.

Show the plan before running any query.

## Act 4: Query the database

1. Write each query in the plan to `outputs/<run>/data/<name>.sql`. Start from a golden query when one fits, keeping its metric expressions as written and changing only the period, filters, and groupings the question needs. Build any other query from the measure formulas, filling in `period_start`, `period_end`, and `analysis_date` (the data's last day; the date is in AGENTS.md). Name a table with its schema unless the schema is `public` (`marts.user_activity_metrics`).
2. Use aggregates only. Every query returns counts, sums, rates, or minimums and maximums at the grain the analysis needs, such as one row per month and segment, never rows of a table: no `SELECT *`, no `LIMIT` to peek, no lists of user ids. Keep each result under about 200 rows; if it would be larger, aggregate further in SQL. On `sessions`, filter by date first.
3. Run each query with `mcp__course-db__execute_sql`, passing the SQL from its file unchanged.
4. Save each result exactly as returned to `outputs/<run>/data/<name>.json`, one JSON object per row and one row per line. Never retype, round, reorder or drop a value. If you change a query, rerun it and save both files again.
5. Checks that need rows run in SQL, as queries saved the same way:
   - before trusting a join, the row count and the distinct count of the key with and without the join, to catch a fan-out;
   - for a window that may not have closed (a trial, a month), how many rows the measure's own filter leaves out;
   - for each date column a comparison runs on, its minimum and maximum, for `date_boundaries`.

## Act 5: Write and run the script

Write one script at `outputs/<run>/analysis.py`:

1. Read the saved results with pandas, `pd.read_json(<path>, lines=True)`. They are the script's only input: it never reads `data/*.csv` and never connects to the database.
2. Use `helpers.checks` for at least the checks the plan needs: `date_boundaries` on the minimum and maximum from Act 4 for partial periods at the edges, and `parts_sum_to_total` when segments should add back to a total. `join_fan_out` and `matured_only` need rows, so for joins and open windows the script reads the check queries' results and prints whether each passed. Print each check's `summary`.
3. Save each result table to `outputs/<run>/data/<name>.csv`.
4. Make charts only through `helpers.charts`: `bar` or `line`, then `save` into `outputs/<run>/charts/<name>.png`. Every title states the takeaway the chart proves, not a label.
5. Print the headline numbers, each with its comparison, and the check summaries. Print aggregates only.

Run it from the repo root with `poetry run python outputs/<run>/analysis.py`. If it fails, fix it and rerun until it runs clean. If a check fails, decide whether it changes the answer and fix the query or the script, or report it. If the data cannot answer the question, say so plainly and stop.

## Act 6: Report

On the CLI, report:

- Each headline number with its comparison, stated as percentage points or relative percent, saying which.
- Which measures and golden queries the numbers used, and any number defined outside the YAML files.
- What was segmented and why.
- Which checks ran and what each said.
- What was not checked.
- The path of the run folder.

Keep it under twenty lines. No brief here; the Deliver step writes the brief.

## Principles

- **The question is the gate.** No frame note, no analysis. Ask; never guess.
- **The model reasons, the code computes.** Every number comes out of a saved query or `analysis.py`. None comes from prose arithmetic.
- **Definitions come from the semantic layer.** Every number uses a measure or golden query as its YAML file defines it, or says it was defined in the plan.
- **Always compare.** A number without its comparison is not a finding. When there is no comparison, say so.
- **Quirks first.** Read what is known about the tables, in the YAML files, quirks, and corrections, before computing anything, and say how each applicable quirk was handled.
- **Closed periods only.** An open month or an unmatured trial is not a result.
- **Name the unit of change.** Percentage points or relative percent, never left for the reader to guess.
- **Rerunnable or it did not happen.** Anyone can run the script again on the saved results and get the same tables, charts and numbers, and rerun the saved queries to refresh those results.
- **Say what you did not check.** A gap you name is safer than one a reader finds later.
