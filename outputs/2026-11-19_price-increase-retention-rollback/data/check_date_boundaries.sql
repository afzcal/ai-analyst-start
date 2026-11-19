-- Minimum and maximum of each date column the comparison runs on, up to the analysis date (2026-09-24).
SELECT 'subscriptions.start_date' AS column_name, MIN(start_date) AS min_value, MAX(start_date) AS max_value
FROM subscriptions WHERE plan IN ('monthly', 'annual') AND start_date < DATE '2026-09-25'
UNION ALL
SELECT 'subscriptions.end_date', MIN(end_date), MAX(end_date)
FROM subscriptions WHERE plan IN ('monthly', 'annual') AND end_date < DATE '2026-09-25'
UNION ALL
SELECT 'payments.payment_date', MIN(payment_date), MAX(payment_date)
FROM payments;
