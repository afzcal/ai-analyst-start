# Frame

- **Question:** Did the March 2026 price increase hurt retention, and for whom?
- **Decision:** Whether to roll back part of the increase for some customers.
- **Audience:** The head of growth.
- **What would change the decision:** (inferred) If monthly subscribers churned more after the March 2026 increase than before it, and more than annual subscribers (whose price did not change), and the rise is concentrated in identifiable groups, a partial rollback for those groups is on the table. If churn did not rise, or rose evenly for everyone, there is no group to target and the case for a partial rollback is weak.
- **Not in scope:** Every monthly subscriber was moved to the new price on 2026-03-01, so no monthly group kept the old price, and the data cannot show how retention would respond to a rollback or to any other price. Annual prices did not change, but annual subscribers differ from monthly ones in more than price, so they are a comparison, not a control. The data ends on 2026-09-24, so at most six full months after the increase can be seen, not the longer-run effect. The data has no cancellation reasons, so it cannot show whether people left because of price.

## Tables likely involved

- `subscriptions`: plan, start and end dates, to compute monthly churn before and after March 2026 and tenure bands.
- `payments`: the amount charged, to confirm who paid \$10 and who paid \$12, and when the new price first hit each subscriber.
- `users`: country and signup device, the segments to test for "for whom".
