-- Review: the days 0 to 3 headline recomputed without the analysis's shared CTE.
-- Counts distinct session days directly and takes the binge threshold as a discrete 75th percentile.
WITH tri AS (
    SELECT
        t.trial_id
        , t.user_id
        , t.started_at::date AS d0
        , t.outcome
    FROM trials AS t
    WHERE TRUE
        AND t.ends_at < DATE '2026-09-25'
)
, per_trial AS (
    SELECT
        tri.trial_id
        , tri.outcome
        , COALESCE(SUM(ses.duration_minutes) FILTER (WHERE ses.session_date::date = tri.d0), 0) AS m0
        , COUNT(DISTINCT ses.session_date::date) FILTER (WHERE ses.session_date::date > tri.d0) AS back_days
    FROM tri
    LEFT JOIN sessions AS ses
        ON ses.session_date >= DATE '2026-08-01'
        AND ses.session_date < DATE '2026-09-14'
        AND ses.user_id = tri.user_id
        AND ses.session_date::date BETWEEN tri.d0 AND tri.d0 + 3
    GROUP BY 1, 2
)
, thr AS (
    SELECT
        PERCENTILE_DISC(0.75) WITHIN GROUP (ORDER BY pt.m0) AS p75
    FROM per_trial AS pt
)
SELECT
    MIN(thr.p75) AS binge_threshold
    , COUNT(*) AS matured_trials
    , COUNT(*) FILTER (WHERE pt.outcome = 'converted') AS matured_converted
    , COUNT(*) FILTER (WHERE pt.m0 >= thr.p75 AND pt.back_days = 0) AS binge_no_return_trials
    , COUNT(*) FILTER (WHERE pt.m0 >= thr.p75 AND pt.back_days = 0 AND pt.outcome = 'converted') AS binge_no_return_converted
    , COUNT(*) FILTER (WHERE pt.back_days = 3) AS back_all_three_trials
    , COUNT(*) FILTER (WHERE pt.back_days = 3 AND pt.outcome = 'converted') AS back_all_three_converted
    , COUNT(*) FILTER (WHERE pt.back_days <= 1) AS back_at_most_one_trials
    , COUNT(*) FILTER (WHERE pt.back_days <= 1 AND pt.outcome = 'converted') AS back_at_most_one_converted
FROM per_trial AS pt
CROSS JOIN thr;
