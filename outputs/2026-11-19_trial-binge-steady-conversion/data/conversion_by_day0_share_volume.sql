-- Conversion by the share of first-week minutes that fell on day 0, within quarters of total first-week minutes, trials still in trial through day 6.
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
, cuts AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY cla.week_minutes) AS p25
        , PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY cla.week_minutes) AS p50
        , PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY cla.week_minutes) AS p75
    FROM classified AS cla
    WHERE TRUE
        AND cla.in_trial_through_day6
)
, banded AS (
    SELECT
        cla.*
        , CASE
            WHEN cla.week_minutes < cut.p25 THEN '1_bottom_quarter'
            WHEN cla.week_minutes < cut.p50 THEN '2_second_quarter'
            WHEN cla.week_minutes < cut.p75 THEN '3_third_quarter'
            ELSE '4_top_quarter'
          END AS volume_band
        , CASE
            WHEN cla.week_minutes = 0 THEN '0_no_first_week_use'
            WHEN cla.day0_minutes::numeric / cla.week_minutes < 0.25 THEN '1_under_25pct'
            WHEN cla.day0_minutes::numeric / cla.week_minutes < 0.50 THEN '2_25_to_50pct'
            WHEN cla.day0_minutes::numeric / cla.week_minutes < 0.75 THEN '3_50_to_75pct'
            ELSE '4_75pct_or_more'
          END AS day0_share_band
    FROM classified AS cla
    CROSS JOIN cuts AS cut
    WHERE TRUE
        AND cla.in_trial_through_day6
)
SELECT
    ban.volume_band
    , ban.day0_share_band
    , COUNT(*) AS trials
    , COUNT(*) FILTER (WHERE ban.outcome = 'converted') AS converted
    , MIN(ban.week_minutes) AS min_week_minutes
    , MAX(ban.week_minutes) AS max_week_minutes
    , ROUND(AVG(ban.active_days), 2) AS avg_active_days
FROM banded AS ban
GROUP BY 1, 2
ORDER BY 1, 2;
