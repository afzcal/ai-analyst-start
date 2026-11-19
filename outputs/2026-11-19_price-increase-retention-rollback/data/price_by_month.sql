-- Payments and amounts per month and plan, September 2025 through August 2026 (golden query monthly_revenue_by_plan, payments.yaml, with amount added).
SELECT
    DATE_TRUNC('month', pay.payment_date)::date AS payment_month
    , sub.plan
    , pay.amount_usd
    , COUNT(*) AS payments
    , SUM(pay.amount_usd) AS revenue_usd
FROM payments AS pay
JOIN subscriptions AS sub
    ON pay.subscription_id = sub.subscription_id
WHERE TRUE
    AND pay.payment_date >= DATE '2025-09-01'
    AND pay.payment_date < DATE '2026-09-01'
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3;
