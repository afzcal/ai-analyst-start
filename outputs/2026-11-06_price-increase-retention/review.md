# Review

**Verdict:** Think on it

The mechanics hold: joins do not fan out, segments add back to their totals, and the headline churn recomputes exactly by a second method. But the before window is not a quiet baseline, since churn had already stepped up once without a price change, and the brief has to weigh higher churn against monthly-plan revenue that still rose.

## Findings

1. **Reasoning: churn had already stepped up once, in October 2025, without a price change, and the headline shows only the window after that step.**
   - Where: `analysis.py`, line 24
   - Evidence: outside the September 2025 cohort, monthly churn rose from 0.80% (January to August 2025) to 1.96% (October 2025 to February 2026), before rising to 5.28% after the increase. Annual churn also rose in October 2025 (0.27% in August, 0.73% in October), but held after March 2026.
   - Effect: the 3.42 point rise is read against a baseline that had already moved. The April step stands apart because it hit the monthly plan only, while the October step hit both plans.
   - Fix: add January to August 2025 as a second baseline window in `churn_before_after.csv`, for both plans (small)

2. **Reasoning: monthly-plan revenue rose 29.4% after the increase, so the "so what" is a trade-off, not only a loss.**
   - Where: `analysis.py`, line 133
   - Evidence: monthly-plan revenue averaged 50,730 USD a month before and 65,635 after, while churn rose 3.42 points.
   - Effect: a rollback for any group gives up revenue now to keep subscribers later. Five months after the increase do not show whether higher churn shrinks the base enough to outweigh the price.
   - Fix: say so in the brief, and size a rollback against the revenue it gives up before deciding (larger)

## Checked and clean

- Joins: subscriptions to users and payments to subscriptions keep their row counts without fanning out.
- Grain: 8,951 monthly subscriptions, one row each, so each can leave at most once.
- Independent recompute: counting the base month by month from starts and ends gives 626 leavers over 26,387 subscriber-months before (2.37%) and 1,553 over 26,821 after (5.79%), matching the headline.
- Price: every monthly payment from 2026-03-01 is 12 USD, including subscribers who started before March, so the increase reached the whole monthly base.
- Windows: adding March 2026 to the after window gives 5.25%, so the result does not depend on leaving March out. The same months a year earlier ran at 0.85%.
- For whom: the country and device gaps are not a tenure gap. Each group has between 52% and 56% of its subscriber-months past a year, and US and iOS churn stays lowest within both tenure bands.
- Filters: 1,549 future starts are left out, and 154 monthly subscriptions with a scheduled end after 2026-09-24 count as active.
- Denominator: subscriptions that start and leave in the same month never enter a month-start base (4 before, 18 after), which slightly understates the rise.

## Not checked

- What happens after August 2026: September is cut off on the 24th, and the 154 scheduled cancellations have not ended yet.
- Whether a rollback would bring churn back down: nothing in the data has a group that kept the old price.
- What "expired" and "canceled" mean: no leaver was marked canceled before the increase, and 355 were after, but the statuses are not defined anywhere.
