# Frame

- **Question:** Did the March 2026 price increase hurt retention, and for whom?
- **Decision:** Whether to roll back part of the increase for some customers.
- **Audience:** The head of growth.
- **What would change the decision:** A rollback for a group is supported if that group's subscribers left clearly faster after the increase than before it. Keeping the price is supported if retention held for every group. (inferred)

## Tables likely involved

- `subscriptions`: plans, start and end dates, the base for retention before and after March 2026.
- `payments`: what each subscription paid, to confirm when and for whom the price changed.
- `users`: country and device, to find which customers were hurt.
