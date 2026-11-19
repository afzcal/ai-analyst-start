# Frame

- **Question:** Do trial users who binge on day one and then go quiet convert worse than steady users? The head of growth is deciding whether the onboarding emails should push trial users to spread their first week out.
- **Decision:** whether the onboarding emails should push trial users to spread their first week out
- **Audience:** the head of growth
- **What would change the decision:** (inferred) If trial users who binge on day one and then go quiet convert clearly worse than steady users, including steady users with a similar amount of first-week use, that supports emails that push users to spread their first week out. If they convert about the same or better, or the gap disappears once total first-week use is held level, the data gives no reason to push spreading out.
- **Not in scope:** The data holds no record of onboarding emails or of any test that changed how trial users spread their use, so it can show only how usage pattern and conversion go together, not whether pushing users to spread out would raise conversion. Trials launched on 2026-08-01, so only trials started by 2026-09-10 have finished their 14 days by 2026-09-24, about six weeks of cohorts.

## Tables likely involved

- `trials`: each trial's start day, 14-day window, and outcome (converted or canceled), with open trials left out.
- `sessions`: each trial user's sessions by day, to tell day-one bingers who go quiet from steady users over the first week.
- `users`: signup day and device and market, to check whether the two groups differ in mix.
