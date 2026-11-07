# payments

Grain (a guess from the data, confirm it): one row per payment_id. 100,914 rows.

## Columns

| Name | Type | Null rate | Distinct |
| --- | --- | --- | --- |
| payment_id | int64 | 0.00% | 100,914 |
| subscription_id | int64 | 0.00% | 11,122 |
| payment_date | datetime64[ns] | 0.00% | 13,232 |
| amount_usd | float64 | 0.00% | 3 |
| method | object | 0.00% | 4 |

## Date ranges

- `payment_date`: 2025-01-01T00:00:00 to 2026-09-24T23:51:30

## Low-cardinality values

- `amount_usd`: 10.0 (59,064), 12.0 (37,384), 100.0 (4,466)
- `method`: card (50,237), paypal (20,272), apple_pay (15,298), google_pay (15,107)

## Meaning



- `payment_id`: the payment's id, unique per row. (inferred)
- `subscription_id`: the subscription the payment belongs to, joining to `subscriptions.subscription_id`. A subscription has many payments, one per billing period. (inferred)
- `payment_date`: when the payment was taken. The range starts on 2025-01-01, though subscriptions go back to 2022, so payments before 2025 are not in this export. No quirk explains this yet. (inferred)
- `amount_usd`: the amount charged. 10.0 and 12.0 are the monthly price before and after the March 2026 change, per the "Monthly price change" quirk; 100.0 is likely the annual price, which shows no change. (inferred)
- `method`: how the user paid: `card`, `paypal`, `apple_pay` or `google_pay`. (inferred)

Grain in plain words: one row per payment, many payments per subscription. (inferred)
