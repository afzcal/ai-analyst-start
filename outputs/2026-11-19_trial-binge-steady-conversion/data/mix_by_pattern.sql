-- Mix of each usage pattern by device, market and start week, with conversion, trials still in trial through day 6.
-- Matured trials (ends_at before 2026-09-25, from the weekly_trial_conversion golden query).
-- Day 0 is the trial's start date; the first week is days 0 to 6. Groups are defined in the analysis plan.
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
SELECT
    cla.pattern
    , CASE
        WHEN GROUPING(usr.device_type) = 0 THEN 'device_type'
        WHEN GROUPING(usr.country) = 0 THEN 'country'
        ELSE 'start_week'
      END AS dimension
    , CASE
        WHEN GROUPING(usr.device_type) = 0 THEN usr.device_type
        WHEN GROUPING(usr.country) = 0 THEN usr.country
        ELSE cla.start_week::text
      END AS value
    , COUNT(*) AS trials
    , COUNT(*) FILTER (WHERE cla.outcome = 'converted') AS converted
FROM classified AS cla
JOIN users AS usr
    ON usr.user_id = cla.user_id
WHERE TRUE
    AND cla.in_trial_through_day6
GROUP BY GROUPING SETS (
    (cla.pattern, usr.device_type)
    , (cla.pattern, usr.country)
    , (cla.pattern, cla.start_week)
)
ORDER BY 2, 1, 3;
