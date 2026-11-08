"""Did the March 2026 price increase hurt retention, and for whom?

Run from the repo root:
    poetry run python outputs/2026-11-06_price-increase-retention/analysis.py
"""

from pathlib import Path

import pandas as pd

from helpers import charts
from helpers.checks import date_boundaries, join_fan_out, parts_sum_to_total

RUN = Path(__file__).parent
OUT = RUN / "data"
CHARTS = RUN / "charts"
OUT.mkdir(exist_ok=True)

# The data ends on 2026-09-24. Use the end of that day as "today".
AS_OF = pd.Timestamp("2026-09-24 23:59:59")
PRICE_CHANGE = pd.Timestamp("2026-03-01")
# March 2026 is the first month billed at the new price, so it sits between the windows.
# September 2026 is cut off on the 24th, so it is left out of the after window.
BEFORE = pd.period_range("2025-10", "2026-02", freq="M")
AFTER = pd.period_range("2026-04", "2026-08", freq="M")
BASELINE_2025 = pd.period_range("2025-01", "2025-08", freq="M")
CHART_MONTHS = pd.period_range("2025-01", "2026-08", freq="M")

subs = pd.read_csv("data/subscriptions.csv", parse_dates=["start_date", "end_date"])
users = pd.read_csv("data/users.csv", parse_dates=["signup_date"])
payments = pd.read_csv("data/payments.csv", parse_dates=["payment_date"])

print("== Checks ==")
print(join_fan_out(subs, users, on="user_id")["summary"], "(subscriptions to users)")
print(join_fan_out(payments, subs, on="subscription_id")["summary"], "(payments to subscriptions)")
print(date_boundaries(payments, "payment_date")["summary"])

future_starts = int((subs["start_date"] > AS_OF).sum())
paid = subs[(subs["plan"] != "free") & (subs["start_date"] <= AS_OF)].merge(users, on="user_id", how="left")
scheduled = int((paid["end_date"] > AS_OF).sum())
# A subscription with a future end date is still active today.
paid["end_eff"] = paid["end_date"].where(paid["end_date"] <= AS_OF)
print(f"Subscriptions starting after {AS_OF.date()} left out: {future_starts:,}.")
print(f"Paid subscriptions with a scheduled end after {AS_OF.date()}, counted as active: {scheduled:,}.")

# 1. Who paid the new price: monthly payments by period and by when the subscriber started.
pm = payments.merge(subs[["subscription_id", "plan", "start_date"]], on="subscription_id", how="left")
pm["period"] = (pm["payment_date"] >= PRICE_CHANGE).map({False: "Before 2026-03-01", True: "From 2026-03-01"})
pm["subscriber"] = (pm["start_date"] >= PRICE_CHANGE).map(
    {False: "Started before 2026-03-01", True: "Started from 2026-03-01"}
)
price_check = (
    pm.groupby(["plan", "period", "subscriber", "amount_usd"]).size().reset_index(name="payments")
)
price_check.to_csv(OUT / "price_check.csv", index=False)

# 2. A panel of subscriber-months: who was active at the start of each month, and who left in it.
panel = []
for month in pd.period_range("2025-01", "2026-09", freq="M"):
    start, end = month.start_time, month.end_time
    active = paid[(paid["start_date"] < start) & (paid["end_eff"].isna() | (paid["end_eff"] >= start))].copy()
    active["left"] = (active["end_eff"] >= start) & (active["end_eff"] <= end)
    active["tenure_months"] = (start - active["start_date"]).dt.days / 30.44
    active["month"] = month
    panel.append(active)
panel = pd.concat(panel, ignore_index=True)
panel["window"] = None
panel.loc[panel["month"].isin(BEFORE), "window"] = "before"
panel.loc[panel["month"].isin(AFTER), "window"] = "after"
panel["tenure"] = pd.cut(
    panel["tenure_months"], [0, 3, 6, 12, 1000],
    labels=["Under 3 months", "3 to 6 months", "6 to 12 months", "12 months or more"], right=False,
)
panel["start_cohort"] = (panel["start_date"].dt.to_period("M") == pd.Period("2025-09", "M")).map(
    {True: "Started in September 2025", False: "Started in another month"}
)

by_month = panel.groupby(["month", "plan"]).agg(active=("left", "size"), left=("left", "sum")).reset_index()
by_month["churn_pct"] = (by_month["left"] / by_month["active"] * 100).round(2)
by_month["month"] = by_month["month"].astype(str)
by_month.to_csv(OUT / "churn_by_month.csv", index=False)

# 3. Headline: pooled monthly churn before and after, for both plans.
win = panel[panel["window"].notna()]
ba = win.groupby(["plan", "window"]).agg(subscriber_months=("left", "size"), leavers=("left", "sum"))
ba["churn_pct"] = (ba["leavers"] / ba["subscriber_months"] * 100).round(2)
headline = ba["churn_pct"].unstack()[["before", "after"]]
headline["change_pp"] = (headline["after"] - headline["before"]).round(2)
headline["change_rel_pct"] = ((headline["after"] / headline["before"] - 1) * 100).round(1)
headline = headline.join(ba["subscriber_months"].unstack().add_prefix("subscriber_months_"))
headline = headline.join(ba["leavers"].unstack().add_prefix("leavers_")).reset_index()
# A second baseline: churn had already stepped up in October 2025, before any price change.
base25 = panel[panel["month"].isin(BASELINE_2025)].groupby("plan")["left"].agg(["size", "sum"])
headline["baseline_2025_pct"] = headline["plan"].map((base25["sum"] / base25["size"] * 100).round(2))
headline.to_csv(OUT / "churn_before_after.csv", index=False)
mo = headline.set_index("plan").loc["monthly"]
an = headline.set_index("plan").loc["annual"]

# 4. For whom: monthly-plan churn before and after by segment.
mwin = win[win["plan"] == "monthly"]
rows = []
for col, label in [("tenure", "Tenure"), ("country", "Country"), ("device_type", "Device"), ("start_cohort", "Start cohort")]:
    g = mwin.groupby([col, "window"], observed=True)["left"].agg(subscriber_months="size", leavers="sum")
    for w in ["before", "after"]:
        part = g.xs(w, level="window")
        print(parts_sum_to_total(part["leavers"], int(mwin.loc[mwin["window"] == w, "left"].sum()))["summary"], f"({label}, leavers {w})")
        print(parts_sum_to_total(part["subscriber_months"], int((mwin["window"] == w).sum()))["summary"], f"({label}, subscriber-months {w})")
    for seg in g.index.get_level_values(0).unique():
        b, a = g.loc[(seg, "before")], g.loc[(seg, "after")]
        before_pct = b["leavers"] / b["subscriber_months"] * 100
        after_pct = a["leavers"] / a["subscriber_months"] * 100
        rows.append({
            "segment_type": label, "segment": seg,
            "before_pct": round(before_pct, 2), "after_pct": round(after_pct, 2),
            "change_pp": round(after_pct - before_pct, 2),
            "change_rel_pct": round((after_pct / before_pct - 1) * 100, 1),
            "subscriber_months_after": int(a["subscriber_months"]), "leavers_after": int(a["leavers"]),
        })
segments = pd.DataFrame(rows)
segments.to_csv(OUT / "churn_by_segment.csv", index=False)

# 5. How monthly-plan leavers left, before and after.
leavers = mwin[mwin["left"]]
how_left = pd.crosstab(leavers["window"], leavers["status"]).reindex(["before", "after"]).reset_index()
how_left.to_csv(OUT / "leavers_by_status.csv", index=False)

# 6. Monthly-plan revenue by month, for scale.
mp = pm[(pm["plan"] == "monthly") & (pm["payment_date"] < "2026-09-01")].copy()
mp["month"] = mp["payment_date"].dt.to_period("M")
revenue = mp[mp["month"] >= pd.Period("2025-10", "M")].groupby("month").agg(
    payments=("amount_usd", "size"), revenue_usd=("amount_usd", "sum")
).reset_index()
revenue["window"] = revenue["month"].map(lambda m: "before" if m in BEFORE else ("after" if m in AFTER else "transition"))
revenue["month"] = revenue["month"].astype(str)
revenue.to_csv(OUT / "monthly_revenue.csv", index=False)
rev = revenue[revenue["window"] != "transition"].groupby("window")["revenue_usd"].mean()
rev_rel = (rev["after"] / rev["before"] - 1) * 100
rev_summary = pd.DataFrame({
    "window": ["before", "after"],
    "months": ["2025-10 to 2026-02", "2026-04 to 2026-08"],
    "avg_monthly_revenue_usd": [round(rev["before"]), round(rev["after"])],
    "change_rel_pct": [None, round(rev_rel, 1)],
})
rev_summary.to_csv(OUT / "revenue_before_after.csv", index=False)

# Charts: every title states the takeaway.
cm = by_month[by_month["month"].isin(CHART_MONTHS.astype(str))]
fig = charts.line(
    cm.loc[cm["plan"] == "monthly", "month"],
    {
        "Monthly plan": cm.loc[cm["plan"] == "monthly", "churn_pct"],
        "Annual plan": cm.loc[cm["plan"] == "annual", "churn_pct"],
    },
    f"Monthly-plan churn rose from {mo['before']:.2f}% to {mo['after']:.2f}% a month after the price increase, "
    f"while annual churn held",
    highlight="Monthly plan",
    ylabel="Active subscribers who left that month (%)",
    source="Source: data/churn_by_month.csv, from analysis.py",
)
charts.save(fig, CHARTS / "churn_by_month.png")

seg_plot = segments[segments["segment_type"].isin(["Tenure", "Country", "Device"])]
first_year = segments[(segments["segment_type"] == "Tenure") & (segments["segment"] != "12 months or more")]
long_tenure = segments[(segments["segment_type"] == "Tenure") & (segments["segment"] == "12 months or more")].iloc[0]
fig = charts.bar(
    seg_plot["segment"],
    seg_plot["change_pp"],
    f"1st-year subscribers saw churn rise {first_year['change_pp'].min():.1f} to "
    f"{first_year['change_pp'].max():.1f} points, versus {long_tenure['change_pp']:.1f} "
    f"for those tenured more than a year",
    highlight=list(first_year["segment"]),
    ylabel="Change in monthly churn (percentage points)",
    source="Source: data/churn_by_segment.csv, from analysis.py",
    horizontal=True,
    fmt="{:.1f}",
)
charts.save(fig, CHARTS / "churn_change_by_segment.png")

print("\n== Headline numbers ==")
print(
    f"Monthly-plan churn: {mo['before']:.2f}% a month before, {mo['after']:.2f}% after: "
    f"{mo['change_pp']:+.2f} percentage points, {mo['change_rel_pct']:+.1f}% relative."
)
print(
    f"Annual-plan churn, price unchanged: {an['before']:.2f}% before, {an['after']:.2f}% after: "
    f"{an['change_pp']:+.2f} percentage points, {an['change_rel_pct']:+.1f}% relative."
)
print(
    f"Second baseline, January to August 2025: monthly {mo['baseline_2025_pct']:.2f}%, "
    f"annual {an['baseline_2025_pct']:.2f}%."
)
print(
    f"Monthly-plan revenue: {rev['before']:,.0f} USD a month before, {rev['after']:,.0f} after: "
    f"{rev_rel:+.1f}% relative."
)
print(segments.to_string(index=False))
print(how_left.to_string(index=False))
print(price_check[price_check["plan"] == "monthly"].to_string(index=False))
