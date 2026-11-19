-- Paid subscriptions the open windows leave out or count as still active.
SELECT
    COUNT(*) FILTER (WHERE start_date >= DATE '2026-09-25') AS scheduled_starts_excluded
    , COUNT(*) FILTER (WHERE start_date < DATE '2026-09-25' AND end_date >= DATE '2026-09-25') AS scheduled_ends_counted_active
    , COUNT(*) FILTER (WHERE start_date >= DATE '2026-08-01' AND start_date < DATE '2026-09-25') AS started_from_aug_2026_in_no_base
    , COUNT(*) FILTER (WHERE end_date >= DATE '2026-09-01' AND end_date < DATE '2026-09-25') AS ended_sep_2026_left_out
FROM subscriptions
WHERE plan IN ('monthly', 'annual');
