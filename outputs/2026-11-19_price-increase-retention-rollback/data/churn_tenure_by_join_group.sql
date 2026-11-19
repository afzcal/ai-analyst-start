-- Monthly plan: pooled churn_rate_month_start by window, tenure_band, and when the subscriber joined
-- (the September 2025 spike cohort, other starts before the increase at $10, starts from 2026-03-01 at $12).
WITH months AS (
    SELECT generate_series(DATE '2025-09-01', DATE '2026-08-01', INTERVAL '1 month')::date AS month_start
)
, base AS (
    SELECT
        CASE WHEN mon.month_start < DATE '2026-03-01' THEN 'before' ELSE 'after' END AS price_window
        , CASE
            WHEN mon.month_start - sub.start_date < INTERVAL '6 months' THEN 'under 6 months'
            WHEN mon.month_start - sub.start_date < INTERVAL '12 months' THEN '6 to 12 months'
            WHEN mon.month_start - sub.start_date < INTERVAL '24 months' THEN '12 to 24 months'
            ELSE 'over 24 months'
          END AS tenure_band
        , CASE
            WHEN DATE_TRUNC('month', sub.start_date)::date = DATE '2025-09-01' THEN 'started Sep 2025'
            WHEN sub.start_date < DATE '2026-03-01' THEN 'other start before 2026-03-01'
            ELSE 'started from 2026-03-01'
          END AS join_group
        , (sub.end_date < mon.month_start + INTERVAL '1 month') AS churned
    FROM months AS mon
    JOIN subscriptions AS sub
        ON sub.plan = 'monthly'
        AND sub.start_date < mon.month_start
        AND (sub.end_date IS NULL OR sub.end_date >= mon.month_start)
)
SELECT
    price_window
    , tenure_band
    , join_group
    , COUNT(*) AS active_paid_subscriptions_at_start
    , COUNT(*) FILTER (WHERE churned) AS churned_subscriptions_from_start
    , ROUND(COUNT(*) FILTER (WHERE churned)::numeric / COUNT(*), 4) AS churn_rate_month_start
FROM base
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
