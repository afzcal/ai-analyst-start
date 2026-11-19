-- Golden query monthly_paid_churn_rate (subscriptions.yaml), extended to January 2025 through August 2026 and split by plan.
WITH months AS (
    SELECT
        generate_series(DATE '2025-01-01', DATE '2026-08-01', INTERVAL '1 month')::date AS month_start
)
SELECT
    mon.month_start
    , sub.plan
    , COUNT(*) AS active_paid_subscriptions
    , COUNT(*) FILTER (WHERE sub.end_date < mon.month_start + INTERVAL '1 month') AS churned_subscriptions
    , ROUND(COUNT(*) FILTER (WHERE sub.end_date < mon.month_start + INTERVAL '1 month')::numeric
        / COUNT(*), 4) AS churn_rate
    , COUNT(*) FILTER (WHERE sub.start_date < mon.month_start) AS active_paid_subscriptions_at_start
    , COUNT(*) FILTER (WHERE sub.start_date < mon.month_start
        AND sub.end_date < mon.month_start + INTERVAL '1 month') AS churned_subscriptions_from_start
    , ROUND(COUNT(*) FILTER (WHERE sub.start_date < mon.month_start
        AND sub.end_date < mon.month_start + INTERVAL '1 month')::numeric
        / COUNT(*) FILTER (WHERE sub.start_date < mon.month_start), 4) AS churn_rate_month_start
FROM months AS mon
JOIN subscriptions AS sub
    ON sub.plan IN ('monthly', 'annual')
    AND sub.start_date < mon.month_start + INTERVAL '1 month'
    AND (sub.end_date IS NULL OR sub.end_date >= mon.month_start)
GROUP BY mon.month_start, sub.plan
ORDER BY mon.month_start, sub.plan;
