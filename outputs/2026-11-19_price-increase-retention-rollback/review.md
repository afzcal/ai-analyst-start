# Review

**Verdict:** Think on it

The mechanics hold. Both headline queries rerun to the same results, and an independent recompute gives the same monthly-plan churn (2.22% before, 5.25% after). The "for whom" answer needs three changes before it is read. The tenure-band changes are distorted by the September 2025 cohort moving between bands. Subscribers who joined at \$12 are not separated from those moved from \$10, and that split is exactly what a partial rollback would target. The break-even verdict is a projection, not an observed result.

## Findings

1. **Reasoning: the tenure-band changes mix the September 2025 cohort moving from "under 6 months" into "6 to 12 months", so the per-band rises are misstated.**
   - Where: `data/churn_by_segment_window.sql`, line 30 (tenure_band) and `analysis.py`, line 174 (segment table)
   - Evidence: the cohort is 51.9% of "under 6 months" subscriber-months before the increase and 13.4% after, and 0.0% of "6 to 12 months" before and 50.8% after. Without it, "under 6 months" rises +6.07 pp (2.57% to 8.64%), not +4.73 pp, and "6 to 12 months" rises +3.75 pp (3.41% to 7.15%), not +4.57 pp. The two longer bands do not change.
   - Effect: the overall +3.03 pp is unaffected. The ranking of who was hurt most shifts: the newest subscribers (under 6 months) rose most, by a clear margin.
   - Fix: report tenure-band changes with the September 2025 cohort filtered out, from a saved query grouped by tenure band and join group (the query in `data/review_tenure_by_join_group.sql`) (small)

2. **Reasoning: the analysis does not separate subscribers who joined at \$12 from those moved from \$10 to \$12, which is the split a partial rollback would act on.**
   - Where: `analysis.py`, line 174 (segments: country, device, tenure band, and September 2025 cohort only)
   - Evidence: in the under-6-months band from March to August 2026, those who joined at \$12 churned 10.14% a month (289 of 2,850 subscriber-months), against 7.34% (239 of 3,258) for those who joined at \$10 and were moved, +2.80 pp. The same band churned 2.57% before the increase.
   - Effect: a rollback limited to existing subscribers would leave out the group leaving fastest. Both groups are well above the pre-increase rate.
   - Fix: add the join group (joined at \$12, moved from \$10, September 2025 cohort) as a segment, from the same query as finding 1 (small)

3. **Reasoning: "every group's churn rose past the 1.2x a 20% price rise can absorb" and the -49% expected revenue per subscriber are projections at constant churn, while observed cash from monthly payments rose 30.4%.**
   - Where: `analysis.py`, line 230 (chart title) and line 272 (expected revenue)
   - Evidence: monthly-plan cash was \$303,130 from September 2025 to February 2026 and \$395,208 from March to August 2026, +30.4% relative. Churn shows no sign of settling: 5.81% in April and May against 5.73% in July and August (-0.09 pp).
   - Effect: the break-even verdict is plausible but rests on churn staying at five months' level and on new subscriptions not changing. A reader could take it as an observed revenue loss.
   - Fix: label the break-even and expected-revenue figures as a projection at constant churn, next to the observed +30.4% cash (small)

## Checked and clean

- Reruns: `churn_by_plan_month` and `churn_by_segment_window` return the saved results unchanged.
- Independent recompute: monthly-plan churn computed from end months and month-start bases separately gives 677 of 30,518 (0.0222) before and 1,697 of 32,307 (0.0525) after, the same as the headline.
- Joins: paid subscriptions to users keep 12,513 rows with 12,513 distinct keys; payments to subscriptions keep 144,065 rows with 144,065 distinct keys. No fan-out.
- Grain: the month-by-subscription panel has 125,344 rows and 125,344 distinct (month, subscription) pairs, so each subscription counts at most once a month. One subscription per user, so subscriptions equal subscribers.
- Denominators: free plans out (18,234 dropped); no null plans, no paid subscription without a start, none ending before it starts; 8,794 paid with no end date count as active; 582 scheduled starts after 2026-09-24 cannot enter any base, since the last month used starts 2026-08-01.
- Date boundaries: start_date, end_date, and payment_date all end on 2026-09-24, so September 2026 is partial. The series runs January 2025 to August 2026, and its last month closes on 2026-08-31, before the data's last day.
- Filters: 1,199 paid end dates and 4,909 start dates carry a time of day. Comparisons are against midnight month starts, so no row moves months.
- Parts sum to totals: every segment adds back to its plan total in every window; the monthly series adds back to each window total; country-by-tenure cells add back to the monthly totals.
- Price exposure: no monthly payment from 2026-03-01 was at the old price (0 of 37,384), and annual payments were \$100 throughout, so the annual plan is a valid untouched comparison.

## Not checked

- The 95% intervals treat subscriber-months as independent; one subscriber appears in several months of a window, so the intervals are somewhat too narrow. Not recomputed with clustering.
- Whether churn after August 2026 settles back: only five months after the first \$12 charge are in the data.
- New monthly subscriptions and the monthly-versus-annual mix after the increase. The analysis covers retention only, so it cannot say whether the price also changed who signs up.
- Why monthly and annual churn both roughly doubled between spring 2025 and autumn 2025, before the increase. The before window absorbs it, and the annual plan shows no change at March 2026, but its cause was not looked into.
