-- Row and key counts with and without each join used.
SELECT
    'paid subscriptions to users' AS join_name
    , (SELECT COUNT(*) FROM subscriptions WHERE plan IN ('monthly', 'annual')) AS rows_before
    , (SELECT COUNT(*) FROM subscriptions AS sub JOIN users AS usr ON sub.user_id = usr.user_id
        WHERE sub.plan IN ('monthly', 'annual')) AS rows_after
    , (SELECT COUNT(DISTINCT sub.subscription_id) FROM subscriptions AS sub JOIN users AS usr ON sub.user_id = usr.user_id
        WHERE sub.plan IN ('monthly', 'annual')) AS distinct_keys_after
UNION ALL
SELECT
    'payments to subscriptions'
    , (SELECT COUNT(*) FROM payments)
    , (SELECT COUNT(*) FROM payments AS pay JOIN subscriptions AS sub ON pay.subscription_id = sub.subscription_id)
    , (SELECT COUNT(DISTINCT pay.payment_id) FROM payments AS pay JOIN subscriptions AS sub ON pay.subscription_id = sub.subscription_id);
