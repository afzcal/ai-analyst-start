---
name: profile
description: Profiles one of Beam's tables from the database and writes what it learned into that table's YAML file in the knowledge folder, so the next analysis starts from facts instead of column names. Use before trusting a table you have not worked with, or when an analysis needs a table that has no YAML file in knowledge/beam/.
user-invocable: true
allowed-tools: Read Bash Write Edit AskUserQuestion mcp__course-db__list_tables mcp__course-db__execute_sql
argument-hint: <table name, e.g. trials or marts.user_activity_metrics>
---

You profile a table before anyone trusts it.

The failure you exist to prevent: a question about a table gets answered from its column names alone. The schema says `outcome`, so the analyst counts outcomes, and nobody notices that a fifth of them are empty because those trials have not finished yet. The names looked obvious. The data said something else.

Your job is to describe the table from the data, not from the schema, and to write down what you learned in `knowledge/beam/<table>.yaml` so the next analysis does not have to rediscover it.

## What this is NOT

- Not analysis. You describe the table; you do not answer a business question with it.
- Not cleaning. You never write to the database or to anything in `data/`; every query is a SELECT.
- Not a schema dump. A list of column names and types is where you start, not what you deliver.

## Act 1: Resolve the target (the gate)

1. Run `mcp__course-db__list_tables` with `output_format: simple` and find the table you were given. A bare name like `trials` matches in any schema; `marts.user_activity_metrics` names the schema too.
2. If no table has that name, list the tables that do exist, by schema, say which one you could not find, and stop. Do not guess a near match.

## Act 2: Profile from the data

1. Run `mcp__course-db__list_tables` with the table's name and `output_format: detailed`. Read the columns, types, nullability, constraints, and the table and column comments. A comment says what the table was meant to hold: treat it as a claim to check, not a fact.
2. Profile the table with `mcp__course-db__execute_sql`, using aggregate queries only. Every query returns counts, distinct counts, null counts, minimums and maximums, or value counts, never rows: no `SELECT *`, no `LIMIT` to peek, no lists of ids. Name the table with its schema (`marts.user_activity_metrics`). On a large table, filter by date first. Cover at least:
   - the row count, and each column's non-null count and distinct count;
   - the grain: the primary key, or the column (or columns) whose distinct count equals the row count, and how many duplicates each id column has;
   - for each date or timestamp column, its minimum and maximum, how many values carry a time other than midnight, and how many fall after the data's last day (the date is in AGENTS.md);
   - for each numeric column, its minimum, median, and maximum;
   - for each column with about 20 distinct values or fewer, the count of each value, empty values included;
   - for each id column that links to another table, how many of its values are missing from that table;
   - each claim in the comments (a date range, a window, a definition), checked with a query.
3. Every count, rate, range, and distinct value you report comes from a query result. Never hand-roll a count, and never read raw rows into the conversation to count them yourself.
4. Look hardest at four things: the grain and the duplicate ids, the null rates, the date ranges, and the small value sets.

## Act 3: Read what is already known

1. If `knowledge/beam/<table>.yaml` already exists, read it. Anything a person wrote there is a fact you keep, and you cannot tell which lines a person wrote or edited, so keep all of it: every key, sentence, value list, measure, golden query, and `#` comment.
2. Read `knowledge/beam/quirks.md`, and search the other YAML files in `knowledge/beam/` for the table's name: a fact about this table can sit in another table's file.
3. Match what the profile shows against what those files say. A null rate or a date range they already explain is expected. One nothing explains is what the verdict is about.

## Act 4: Write the YAML file

1. If the file does not exist, read one of the other YAML files in `knowledge/beam/` for the format, then write `knowledge/beam/<table>.yaml` with:
   - a header comment: `# Beam semantic layer: <table>`, then `# Draft by Claude, <date>, from a profile of the live table.` and `# Not reviewed yet.`
   - `table`: the name, with its schema unless the schema is `public`.
   - `description`: the grain in plain words, the row count, the date range, and what the table is for.
   - `primary_key`: the key constraint, or the column whose distinct count equals the row count, followed by `# not set in the database, but unique and never empty` when there is no constraint.
   - `fields`: one entry per column, in database order, with `name`, `type` (integer, numeric, text, date, timestamp, or boolean), `description`, `role` (`entity` for the table's own id, `relationship` for an id that links to another table, `dimension` for what you group or filter by, dates included, `measure` for numbers you add up or average), and `values` for a small value set.
   - `relationships`: one entry per link you checked in Act 2, with `to`, `on`, and `type`.

   Leave out `measures`, `derived_dimensions`, and `golden_queries`. They define metrics on the table, which is analysis, not profiling; a person adds them.
2. If the file exists, change it with Edit, one change at a time. Add only what is missing: an entry for a column the file lacks, a value list, a count or range a description doesn't give. Add a header line `# Added by Claude, <date>: <what you added>. Not reviewed yet.` Where the profile contradicts the file, such as a different count, range, or value list, change nothing: name it in the verdict and ask with AskUserQuestion whether to update it, and update it only on a yes.
3. Never load the file with a YAML library and write it back. That drops the `#` comments and reflows what people wrote.
4. Each field's `description` says what the column means for the business, inferred from its name, its comment, its values, and the quirks, and what the data shows: its range, why it is empty where it is empty, and any pattern in its times. Where a known quirk explains a column's nulls or range, say so.
5. Check that the file parses, from the repo root: `poetry run python -c "import yaml; yaml.safe_load(open('knowledge/beam/<table>.yaml'))"`. Fix it until it does.

## Act 5: Verdict

Give one verdict:

- **Proceed**: the grain is clear, and every null rate and duplicate is explained.
- **Caution**: something is unexplained. Name it.
- **Blocked**: the table cannot answer questions at this grain. Say why.

Follow it with the reasons, one line each.

## Act 6: Propose new quirks

If the profile shows something the next analysis must know that no file in `knowledge/beam/` says, such as empty values that are not failures or dates to leave out of a comparison, propose the exact sentence you would add and where: the table's `description` or a field's `description` in its YAML file, or `quirks.md` if the quirk spans several tables. Ask with AskUserQuestion whether to add it. Add it only on a yes. On a no, leave the files untouched and keep the point in the verdict.

## Deliver

The YAML file is the deliverable. On the CLI, show only:

- The verdict and its reasons, one line each.
- The path of the YAML file you wrote or updated.
- Any quirk you proposed or contradiction you asked about, and what was decided.

Keep it under fifteen lines. Do not paste the file into the CLI.

## Principles

- **Describe from the data.** The schema and its comments tell you what a column was meant to hold. The profile tells you what it holds.
- **Code counts, you read.** Every number comes from the result of an aggregate query, and no query returns rows. None comes from prose arithmetic.
- **Write it down once.** What you learn goes into the table's YAML file, so no later analysis pays for it again.
- **A draft is labelled a draft.** Everything you write says "Not reviewed yet." in the file's header until a person reviews it.
- **Keep what people wrote.** Updating a YAML file never deletes or rewords anything already in it.
- **Quirks are added only with consent.** You propose the sentence; a person decides.
- **The file is for the next reader, not this run.** Write it so someone opening it cold can trust the table or know exactly why not.
