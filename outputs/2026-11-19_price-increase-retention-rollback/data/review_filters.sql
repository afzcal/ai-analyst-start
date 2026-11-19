-- What the filters drop or let through, for the subscriptions behind the churn queries.
SELECT
    COUNT(*) AS all_subscriptions
    , COUNT(*) FILTER (WHERE plan = 'free') AS free_dropped
    , COUNT(*) FILTER (WHERE plan IS NULL) AS null_plan
    , COUNT(*) FILTER (WHERE plan IN ('monthly', 'annual') AND start_date IS NULL) AS paid_null_start
    , COUNT(*) FILTER (WHERE plan IN ('monthly', 'annual') AND end_date < start_date) AS paid_end_before_start
    , COUNT(*) FILTER (WHERE plan IN ('monthly', 'annual') AND end_date IS NULL) AS paid_no_end_date
    , COUNT(*) FILTER (WHERE plan IN ('monthly', 'annual') AND end_date IS NOT NULL AND end_date::date <> end_date) AS paid_end_with_time
    , COUNT(*) FILTER (WHERE plan IN ('monthly', 'annual') AND start_date::date <> start_date) AS paid_start_with_time
FROM subscriptions;
