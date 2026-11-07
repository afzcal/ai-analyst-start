# subscriptions

Grain (a guess from the data, confirm it): one row per subscription_id. 30,747 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| subscription_id | int64 | 0.00% | 30,747 |
| user_id | int64 | 0.00% | 30,747 |
| plan | object | 0.00% | 3 |
| start_date | datetime64[ns] | 0.00% | 9,584 |
| end_date | datetime64[ns] | 87.90% | 1,789 |
| status | object | 0.00% | 3 |

## Date ranges

- `start_date`: 2022-01-11T00:00:00 to 2026-10-04T17:15:33
- `end_date`: 2022-03-07T00:00:00 to 2026-11-11T18:47:46

## Low-cardinality values

- `plan`: free (18,234), monthly (9,376), annual (3,137)
- `status`: active (27,028), expired (2,929), canceled (790)

## Meaning



- `subscription_id`: the subscription's id, unique per row. (inferred)
- `user_id`: the subscriber. It is unique here, so each user has a single subscription row. (inferred)
- `plan`: `free`, `monthly` or `annual`. Free plans never end, per the "Free plans never end" quirk, so they stay out of churn and retention. (inferred)
- `start_date`: when the subscription began. Values after 2026-09-24 are scheduled starts, per the "Future start dates" quirk, and are excluded from counts of what has happened. (inferred)
- `end_date`: when the subscription ended or is set to end. Most of the 87.90% empty values are free plans and paid plans still running. Values after 2026-09-24 are scheduled cancellations, still active on the analysis date, per the "Future end dates" quirk. (inferred)
- `status`: `active`, `expired` or `canceled`. (inferred)

Grain in plain words: one row per subscription, and one subscription per user. (inferred)
