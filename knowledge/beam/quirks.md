# Beam data quirks

This is no longer where facts about Beam's data live. Each table's quirks, rules, and definitions belong in that table's YAML file in this folder (the semantic layer), so every fact has one home and one version. Check the YAML files first.

A quirk that doesn't fit any table's YAML file yet can sit here for a while. Under each entry, say why it is here and where it should go, and move it there as soon as that file exists. An entry stays here for good only when no single table owns it, such as a quirk that spans several tables, and the entry has to say so.

Corrections from the user go in `corrections.md`, not here.

## Waiting for a home

- **Activity windows fill late.** In `user_activity_metrics`, the first days of January 2024 have weekly and monthly windows that are not full yet, so daily actives read as a high share of monthly actives. Start any comparison after January 2024.
  - Here because `user_activity_metrics` has no YAML file yet; it moves there. Found in the Module 01 CSV export: check it against the database, whose table comment says the metrics run "since 2025".
- **Daily-to-monthly ratio drop in September 2025.** With the September 2025 signup spike, the daily-to-monthly active ratio falls from about .25 to about .21. Treat it as a known anomaly and say so whenever it enters a comparison.
  - Here for the same reason, and it moves to the same file. The spike itself is already in `users.yaml` and `sessions.yaml`.
