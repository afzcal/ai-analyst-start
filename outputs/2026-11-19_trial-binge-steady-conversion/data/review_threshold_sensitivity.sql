-- Review: does the days 0 to 3 result hold at other binge thresholds (50th, 75th, 90th percentile of day-0 minutes)?
WITH matured AS (
    SELECT
        tri.trial_id
        , tri.user_id
        , tri.started_at::date AS start_day
        , DATE_TRUNC('week', tri.started_at)::date AS start_week
        , tri.outcome
        , (tri.outcome_at::date - tri.started_at::date) AS outcome_day
    FROM trials AS tri
    WHERE TRUE
        AND tri.ends_at < DATE '2026-09-25'
)
, first_week_days AS (
    SELECT
        mat.trial_id
        , (ses.session_date::date - mat.start_day) AS trial_day
        , COUNT(*) AS sessions
        , SUM(ses.duration_minutes) AS minutes
    FROM matured AS mat
    JOIN sessions AS ses
        ON ses.session_date >= DATE '2026-08-01'
        AND ses.session_date < DATE '2026-09-17'
        AND ses.user_id = mat.user_id
        AND ses.session_date >= mat.start_day
        AND ses.session_date < mat.start_day + 7
    GROUP BY 1, 2
)
, per_trial AS (
    SELECT
        mat.trial_id
        , mat.user_id
        , mat.start_week
        , mat.outcome
        , mat.outcome_day
        , COALESCE(SUM(fwd.minutes) FILTER (WHERE fwd.trial_day = 0), 0) AS day0_minutes
        , COALESCE(SUM(fwd.minutes), 0) AS week_minutes
        , COUNT(fwd.trial_day) AS active_days
        , COUNT(fwd.trial_day) FILTER (WHERE fwd.trial_day BETWEEN 1 AND 6) AS later_active_days
    FROM matured AS mat
    LEFT JOIN first_week_days AS fwd
        ON fwd.trial_id = mat.trial_id
    GROUP BY 1, 2, 3, 4, 5
)
, threshold AS (
    SELECT
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY pt.day0_minutes) AS binge_minutes
    FROM per_trial AS pt
)
, classified AS (
    SELECT
        pt.*
        , thr.binge_minutes
        , CASE
            WHEN pt.day0_minutes >= thr.binge_minutes AND pt.later_active_days <= 1 THEN 'binge_then_quiet'
            WHEN pt.active_days >= 4 THEN 'steady'
            WHEN pt.later_active_days <= 1 THEN 'light_then_quiet'
            ELSE 'in_between'
          END AS pattern
        , (pt.outcome = 'converted' OR pt.outcome_day >= 7) AS in_trial_through_day6
    FROM per_trial AS pt
    CROSS JOIN threshold AS thr
)
, early AS (
    SELECT
        cla.trial_id
        , cla.outcome
        , cla.day0_minutes
        , COUNT(fwd.trial_day) FILTER (WHERE fwd.trial_day BETWEEN 1 AND 3) AS active_days_1_to_3
    FROM classified AS cla
    LEFT JOIN first_week_days AS fwd
        ON fwd.trial_id = cla.trial_id
    GROUP BY 1, 2, 3
)
, cuts AS (
    SELECT
        q.pct
        , PERCENTILE_CONT(q.pct) WITHIN GROUP (ORDER BY ear.day0_minutes) AS binge_minutes
    FROM early AS ear
    CROSS JOIN (VALUES (0.50::float8), (0.75::float8), (0.90::float8)) AS q(pct)
    GROUP BY 1
)
SELECT
    cut.pct AS threshold_percentile
    , MIN(cut.binge_minutes) AS binge_minutes
    , (ear.day0_minutes >= cut.binge_minutes) AS day0_binge
    , ear.active_days_1_to_3
    , COUNT(*) AS trials
    , COUNT(*) FILTER (WHERE ear.outcome = 'converted') AS converted
FROM early AS ear
CROSS JOIN cuts AS cut
GROUP BY 1, 3, 4
ORDER BY 1, 3, 4;
