# Review

**Verdict:** Think on it

The mechanics hold: the reruns match the saved results, an independent query reproduces the headline exactly, and grain, denominators, dates, and filters are clean. But one secondary claim overstates how little a day-0 binge matters. The headline group is also too small to carry the decision by itself, and the result is an association, which the decision needs read as such.

## Findings

1. **Reasoning: "a day-0 binge barely moves conversion" holds only at the 67-minute binge threshold.**
   - Where: `analysis.py`, line 268 (title of `charts/conversion_by_return_days.png`)
   - Evidence: among users back on all of days 1 to 3, bingers convert 1.3 points above non-bingers at a 32-minute threshold, 6.3 points below them at 67 minutes, and 25.3 points below them at 113 minutes (48/86, 55.8%, against 632/779, 81.1%). In the analysis's own first-week table, at 5, 6, and 7 active days, bingers convert 17.0, 20.9, and 7.7 points below non-bingers.
   - Effect: return days are still the larger factor (7.0% for no return against 80.4% for all three days, without a binge), but a heavy day-0 binge goes with lower conversion even among users who come back. That supports spreading the first week out more than the chart title says.
   - Fix: retitle the chart so it says return days move conversion most, without "barely", and print the binge gap at equal active days from the analysis's own tables (small).

2. **Reasoning: the group the question asks about is 10 to 17 trials, so its rate is loose and the email would reach about 1 in 100 trial users.**
   - Where: `analysis.py`, lines 172 and 227
   - Evidence: binge then no return on days 1 to 3 is 1/10 (10.0%, 95% Wilson interval 1.8% to 40.4%); the first-week group is 0/17 (0.0%, interval 0.0% to 18.4%); that is 0.6% to 1.1% of 1,553 matured trials. Users back on at most 1 of days 1 to 3 are 312 trials (20.1%), converting 35/312 (11.2%).
   - Effect: the gap against steady users (68.6 points) is real, since its interval runs from 38.1 to 77.2 points below, but on its own it overstates how much the binge pattern matters to the email decision.
   - Fix: lead the brief with the group's size and interval, and put the larger no-return group next to it (small).

3. **Reasoning: the data shows that coming back goes with converting, not that an email that brings users back would raise conversion.**
   - Where: `frame.md`, "Not in scope"; the brief's recommendations
   - Evidence: no onboarding email or usage test exists in the data; users who return on days 1 to 3 may be those who already meant to stay.
   - Effect: a recommendation to send the emails on this evidence alone would claim more than the numbers carry.
   - Fix: recommend the email as a holdout test measured on trial conversion (small).

## Checked and clean

- Reruns: `conversion_by_early_pattern`, `conversion_by_pattern`, and `conversion_by_day0_share_volume` return exactly the saved results.
- Independent recompute: a query without the shared CTE, counting distinct session days directly, gives the same 1/10, 680/865, 35/312, and 828/1,553, and the same 67-minute threshold.
- Joins: 1,553 matured trials stay 1,553 rows after the sessions and users joins; first-week sessions (28,251) and minutes (299,652) match a direct count. The script makes no joins on saved results.
- Grain: one row per trial and per user (1,553 trial ids, 1,553 users), so conversion counts users.
- Denominators: matured trials only (ends_at before 2026-09-25 keeps the whole last day); 520 unmatured trials left out, including 102 already canceled, so the base stays symmetric; no matured trial lacks an outcome.
- Early cancellations: the 204 matured trials canceled on days 4 to 6 are left out of the first-week comparison; no trial cancels before day 4, so the days 0 to 3 view covers every matured trial without that bias.
- Date boundaries: trial start days run 2026-08-01 to 2026-09-10, and the last one ends on 2026-09-24; first-week sessions run 2026-08-01 to 2026-09-16, inside the sessions prefilter, so the prefilter drops nothing.
- Day-0 length: 385 trials (24.8%) start at 18:00 or later; their binge share is 23.4% against 26.1% for earlier starts, so a short day 0 barely shifts the binge flag.
- Parts sum to totals for every grouping (1,553 or 1,349 trials, and 828 conversions).

## Not checked

- Whether sessions and trial start times share a time zone; day 0 is the calendar date of `started_at`, which assumes they do.
- Activity in days 7 to 13, after the first week.
- Whether the gaps differ by device or market within each usage group; the mix table shows similar group shares by segment, but no segment-by-group conversion test was run.
- Trials started after 2026-09-10, which had not finished their 14 days by 2026-09-24.
