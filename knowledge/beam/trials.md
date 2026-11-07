# trials

Grain (a guess from the data, confirm it): one row per trial_id. 2,073 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| trial_id | int64 | 0.00% | 2,073 |
| user_id | int64 | 0.00% | 2,073 |
| started_at | datetime64[ns] | 0.00% | 2,071 |
| ends_at | datetime64[ns] | 0.00% | 2,071 |
| outcome | object | 20.16% | 2 |
| outcome_at | datetime64[ns] | 20.16% | 1,655 |

## Date ranges

- `started_at`: 2026-08-01T00:29:17 to 2026-09-24T22:59:05
- `ends_at`: 2026-08-15T00:29:17 to 2026-10-08T22:59:05
- `outcome_at`: 2026-08-06T05:37:23 to 2026-09-24T23:55:08

## Low-cardinality values

- `outcome`: converted (828), canceled (827)

## Meaning



- `trial_id`: the trial's id, unique per row. (inferred)
- `user_id`: the user who took the trial. It is unique here too, so each user has at most one trial. (inferred)
- `started_at`: when the trial began. Trials start on 2026-08-01, matching the "Trials mature late" quirk. (inferred)
- `ends_at`: when the 14-day window closes, 14 days after `started_at`. Values after 2026-09-24 belong to trials still open on the analysis date. (inferred)
- `outcome`: `converted` or `canceled` once the trial resolves. Empty for trials that have not matured yet, which the "Trials mature late" quirk explains; those are open, not failures. (inferred)
- `outcome_at`: when the outcome happened. It can fall before `ends_at`, so a user can convert or cancel early. Empty at the same rate as `outcome`. (inferred)

Grain in plain words: one row per trial, and one trial per user. (inferred)
