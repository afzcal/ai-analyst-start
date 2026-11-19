-- Independent recompute of the monthly-plan pooled churn: churners counted from their end month, base counted per month start, separately.
WITH months AS (
    SELECT generate_series(DATE '2025-09-01', DATE '2026-08-01', INTERVAL '1 month')::date AS month_start
)
, base AS (
    SELECT
        mon.month_start
        , (SELECT COUNT(*) FROM subscriptions AS sub
            WHERE sub.plan = 'monthly'
                AND sub.start_date < mon.month_start
                AND (sub.end_date IS NULL OR sub.end_date >= mon.month_start)) AS active_at_start
    FROM months AS mon
)
, churners AS (
    SELECT
        DATE_TRUNC('month', sub.end_date)::date AS month_start
        , COUNT(*) AS churned
    FROM subscriptions AS sub
    WHERE TRUE
        AND sub.plan = 'monthly'
        AND sub.end_date >= DATE '2025-09-01'
        AND sub.end_date < DATE '2026-09-01'
        AND sub.start_date < DATE_TRUNC('month', sub.end_date)
    GROUP BY 1
)
SELECT
    CASE WHEN bas.month_start < DATE '2026-03-01' THEN 'before' ELSE 'after' END AS price_window
    , SUM(bas.active_at_start) AS active_at_start
    , SUM(COALESCE(chu.churned, 0)) AS churned
    , ROUND(SUM(COALESCE(chu.churned, 0))::numeric / SUM(bas.active_at_start), 4) AS churn_rate
FROM base AS bas
LEFT JOIN churners AS chu
    ON bas.month_start = chu.month_start
GROUP BY 1
ORDER BY 1;
