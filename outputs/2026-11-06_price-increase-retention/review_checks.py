"""Review checks for analysis.py. Prints aggregates only.

Run from the repo root:
    poetry run python outputs/2026-11-06_price-increase-retention/review_checks.py
"""

import pandas as pd

from helpers.checks import date_boundaries, join_fan_out

AS_OF = pd.Timestamp("2026-09-24 23:59:59")
subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
users = pd.read_csv("data/users.csv", parse_dates=["signup_date"])
payments = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])

monthly = subs[(subs["plan"] == "monthly") & (subs["start_date"] <= AS_OF)].copy()
monthly["end_eff"] = monthly["end_date"].where(monthly["end_date"] <= AS_OF)

print("== 1. Joins ==")
print(join_fan_out(subs, users, on="user_id")["summary"])
print(join_fan_out(payments, subs, on="subscription_id")["summary"])

print("\n== 2. Grain ==")
print(f"Monthly subscriptions: {len(monthly):,}; distinct ids: {monthly['subscription_id'].nunique():,}; each can leave once.")

print("\n== 3. Denominators ==")
# Subscriptions that start and end inside the same month are never in a month-start base.
same_month = monthly[monthly["end_eff"].notna() & (monthly["start_date"].dt.to_period("M") == monthly["end_eff"].dt.to_period("M"))]
for name, months in [("before", ("2025-10", "2026-02")), ("after", ("2026-04", "2026-08"))]:
    m = same_month["end_eff"].dt.to_period("M").astype(str)
    print(f"Started and left in the same month, {name} window: {int(m.between(*months).sum()):,}")

print("\n== Independent recompute: base by cumulative counts ==")
def pooled(months):
    left = base = 0
    for p in pd.period_range(*months, freq="M"):
        s, e = p.start_time, p.end_time
        starts = (monthly["start_date"] < s).sum()
        ended = (monthly["end_eff"] < s).sum()
        base += starts - ended
        left += ((monthly["end_eff"] >= s) & (monthly["end_eff"] <= e) & (monthly["start_date"] < s)).sum()
    return left, base, left / base * 100
for name, months in [("before", ("2025-10", "2026-02")), ("after", ("2026-04", "2026-08"))]:
    left, base, rate = pooled(months)
    print(f"{name}: {left:,} leavers over {base:,} subscriber-months = {rate:.2f}%")

print("\n== 4. Date boundaries ==")
print(date_boundaries(monthly, "start_date")["summary"])
for name, months in [("March 2026 added to after", ("2026-03", "2026-08")), ("Same months a year earlier", ("2025-04", "2025-08"))]:
    left, base, rate = pooled(months)
    print(f"{name}: {rate:.2f}% ({left:,} of {base:,})")

print("\n== 5. Filters ==")
print(f"Future starts left out: {int((subs['start_date'] > AS_OF).sum()):,}; scheduled ends counted active (monthly): {int((monthly['end_date'] > AS_OF).sum()):,}")

print("\n== Reasoning: did churn for cohorts outside September 2025 step up before the price change? ==")
other = monthly[monthly["start_date"].dt.to_period("M") != pd.Period("2025-09", "M")]
for months in [("2025-01", "2025-08"), ("2025-10", "2026-02"), ("2026-04", "2026-08")]:
    left = base = 0
    for p in pd.period_range(*months, freq="M"):
        s, e = p.start_time, p.end_time
        b = other[(other["start_date"] < s) & (other["end_eff"].isna() | (other["end_eff"] >= s))]
        base += len(b)
        left += int(((b["end_eff"] >= s) & (b["end_eff"] <= e)).sum())
    print(f"Other cohorts {months[0]} to {months[1]}: {left / base * 100:.2f}% ({left:,} of {base:,})")

print("\n== Reasoning: is the country and device gap a tenure gap? ==")
rows = []
for p in pd.period_range("2026-04", "2026-08", freq="M"):
    s, e = p.start_time, p.end_time
    b = monthly[(monthly["start_date"] < s) & (monthly["end_eff"].isna() | (monthly["end_eff"] >= s))].copy()
    b["left"] = (b["end_eff"] >= s) & (b["end_eff"] <= e)
    b["long"] = (s - b["start_date"]).dt.days / 30.44 >= 12
    rows.append(b)
after = pd.concat(rows).merge(users, on="user_id")
for col in ["country", "device_type"]:
    g = after.groupby(col).agg(share_12m_plus=("long", "mean"))
    g["churn_under_12m"] = after[~after["long"]].groupby(col)["left"].mean()
    g["churn_12m_plus"] = after[after["long"]].groupby(col)["left"].mean()
    print((g * 100).round(2).to_string())
