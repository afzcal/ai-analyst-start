-- Grain of the month-by-subscription panel behind every churn query: rows against distinct (month, subscription) pairs.
WITH months AS (
    SELECT generate_series(DATE '2025-01-01', DATE '2026-08-01', INTERVAL '1 month')::date AS month_start
)
SELECT
    COUNT(*) AS panel_rows
    , COUNT(DISTINCT (mon.month_start, sub.subscription_id)) AS distinct_month_subscription
FROM months AS mon
JOIN subscriptions AS sub
    ON sub.plan IN ('monthly', 'annual')
    AND sub.start_date < mon.month_start
    AND (sub.end_date IS NULL OR sub.end_date >= mon.month_start)
JOIN users AS usr
    ON sub.user_id = usr.user_id;
