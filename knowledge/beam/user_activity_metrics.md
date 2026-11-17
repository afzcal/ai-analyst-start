# user_activity_metrics

Grain (a guess from the data, confirm it): no id column found. 998 rows.

Grain in plain words: one row per calendar day, with 998 distinct dates over 998 rows. (inferred)

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| date | datetime64[ns] | 0.00% | 998 |
| dau | int64 | 0.00% | 842 |
| wau | int64 | 0.00% | 950 |
| mau | int64 | 0.00% | 985 |

## Date ranges

- `date`: 2024-01-01T00:00:00 to 2026-09-24T00:00:00

## Low-cardinality values

- None

## Meaning

- `date`: the day measured. Dates carry midnight times, so compare on dates, per the "Timestamps everywhere" quirk. (inferred)
- `dau`: users active that day. (inferred)
- `wau`: users active in the 7 days ending that day. The window length is not stated in the data. (inferred)
- `mau`: users active in a window of about 30 days ending that day. It changes almost every day (985 distinct values over 998 days), so it is a rolling window, not a calendar month. Monthly actives jump at September 2025, and the daily-to-monthly ratio falls, per the "September 2025 spike" quirk. (inferred)

This table holds platform-wide daily totals only. It has no user id, plan, country or device, so it cannot say which users or groups drove a change in activity.
