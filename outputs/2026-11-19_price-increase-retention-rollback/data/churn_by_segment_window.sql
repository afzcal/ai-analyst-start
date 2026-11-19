-- churned_subscriptions_from_start and active_paid_subscriptions_at_start (subscriptions.yaml), summed over the
-- months of each window (pooled churn_rate_month_start, defined in the plan), by plan and one segment at a time.
-- Windows: a_year_earlier = Mar to Aug 2025, before = Sep 2025 to Feb 2026, after = Mar to Aug 2026.
-- tenure_band uses the formula in subscriptions.yaml with period_start = the month's first day.
WITH months AS (
    SELECT
        generate_series(DATE '2025-03-01', DATE '2026-08-01', INTERVAL '1 month')::date AS month_start
)
, windows AS (
    SELECT
        mon.month_start
        , CASE
            WHEN mon.month_start < DATE '2025-09-01' THEN 'a_year_earlier'
            WHEN mon.month_start < DATE '2026-03-01' THEN 'before'
            ELSE 'after'
          END AS price_window
    FROM months AS mon
)
, base AS (
    SELECT
        win.price_window
        , sub.plan
        , usr.country
        , usr.device_type
        , CASE
            WHEN win.month_start - sub.start_date < INTERVAL '6 months' THEN 'under 6 months'
            WHEN win.month_start - sub.start_date < INTERVAL '12 months' THEN '6 to 12 months'
            WHEN win.month_start - sub.start_date < INTERVAL '24 months' THEN '12 to 24 months'
            ELSE 'over 24 months'
          END AS tenure_band
        , CASE
            WHEN DATE_TRUNC('month', sub.start_date)::date = DATE '2025-09-01' THEN 'started Sep 2025'
            ELSE 'started another month'
          END AS start_cohort
        , (sub.end_date < win.month_start + INTERVAL '1 month') AS churned
    FROM windows AS win
    JOIN subscriptions AS sub
        ON sub.plan IN ('monthly', 'annual')
        AND sub.start_date < win.month_start
        AND (sub.end_date IS NULL OR sub.end_date >= win.month_start)
    JOIN users AS usr
        ON sub.user_id = usr.user_id
)
SELECT
    price_window
    , plan
    , CASE
        WHEN GROUPING(country) = 0 THEN 'country'
        WHEN GROUPING(device_type) = 0 THEN 'device_type'
        WHEN GROUPING(tenure_band) = 0 THEN 'tenure_band'
        WHEN GROUPING(start_cohort) = 0 THEN 'start_cohort'
        ELSE 'all'
      END AS dimension
    , COALESCE(country, device_type, tenure_band, start_cohort, 'all') AS segment
    , COUNT(*) AS active_paid_subscriptions_at_start
    , COUNT(*) FILTER (WHERE churned) AS churned_subscriptions_from_start
    , ROUND(COUNT(*) FILTER (WHERE churned)::numeric / COUNT(*), 4) AS churn_rate_month_start
FROM base
GROUP BY GROUPING SETS (
    (price_window, plan)
    , (price_window, plan, country)
    , (price_window, plan, device_type)
    , (price_window, plan, tenure_band)
    , (price_window, plan, start_cohort)
)
ORDER BY price_window, plan, dimension, segment;
