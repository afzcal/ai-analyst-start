-- Whether subscribers who started before the increase kept the old price: payments by plan, payment period, start period and amount.
SELECT
    sub.plan
    , CASE WHEN pay.payment_date::date < DATE '2026-03-01' THEN 'paid before 2026-03-01' ELSE 'paid from 2026-03-01' END AS payment_period
    , CASE WHEN sub.start_date::date < DATE '2026-03-01' THEN 'started before 2026-03-01' ELSE 'started from 2026-03-01' END AS subscriber
    , pay.amount_usd
    , COUNT(*) AS payments
FROM payments AS pay
JOIN subscriptions AS sub
    ON pay.subscription_id = sub.subscription_id
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;
