-- Check: trials left out because their 14 days were not over by 2026-09-24, and matured trials
-- left out of the main comparison because they were canceled before day 7.
SELECT
    COUNT(*) AS trials_total
    , COUNT(*) FILTER (WHERE tri.ends_at < DATE '2026-09-25') AS matured
    , COUNT(*) FILTER (WHERE tri.ends_at >= DATE '2026-09-25') AS not_matured_excluded
    , COUNT(*) FILTER (WHERE tri.ends_at >= DATE '2026-09-25' AND tri.outcome IS NULL) AS not_matured_still_open
    , COUNT(*) FILTER (WHERE tri.ends_at >= DATE '2026-09-25' AND tri.outcome = 'canceled') AS not_matured_already_canceled
    , COUNT(*) FILTER (WHERE tri.ends_at < DATE '2026-09-25' AND tri.outcome IS NULL) AS matured_without_outcome
    , COUNT(*) FILTER (WHERE tri.ends_at < DATE '2026-09-25' AND tri.outcome = 'converted' AND tri.outcome_at <> tri.ends_at) AS converted_not_at_ends_at
    , COUNT(*) FILTER (WHERE tri.ends_at < DATE '2026-09-25' AND tri.outcome = 'canceled'
        AND tri.outcome_at::date - tri.started_at::date < 7) AS matured_canceled_before_day7
    , MIN(tri.outcome_at::date - tri.started_at::date) FILTER (WHERE tri.outcome = 'canceled') AS min_cancel_day
    , MAX(tri.outcome_at::date - tri.started_at::date) FILTER (WHERE tri.outcome = 'canceled') AS max_cancel_day
FROM trials AS tri;
