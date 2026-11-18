# AI Analyst

A data analyst that runs inside Claude Code on Beam's data. Beam is a media app with free, monthly and annual plans and 14-day trials.

## How work routes
- A business question: `/analyst <question>` runs the whole chain.
- A script, notebook or run folder to check: `/validate`.
- Finished results to write up: `/deliver`.
- Each step is also its own skill (`/frame`, `/profile`, `/analyse`) and works alone; skills share nothing except the files in the run folder and `knowledge/beam/`.

## Where things live
```
data/                    Beam CSV exports; never modified
knowledge/beam/          one YAML file per table (the semantic layer), quirks.md, corrections.md
helpers/                 profile, checks, charts; the arithmetic runs here
outputs/<date>_<slug>/   one folder per question:
                         frame.md, analysis.py, data/, charts/, review.md, brief.md
.claude/skills/          analyst, frame, profile, analyse, validate, deliver
```

## Conventions
- Run Python with `poetry run python ...` from the repo root.
- Never print raw rows into the conversation; aggregates only.
- Never modify anything in `data/`.
- Name run folders with today's date (YYYY-MM-DD).
- The data ends on 2026-09-24. Treat that as "today" in every analysis, never the real date.
- No em dashes in anything written for a reader.
- Read `knowledge/beam/` (the table YAML files, `quirks.md`, `corrections.md`) before touching data; when the user corrects you, append one dated line to `corrections.md` and continue.
