"""Review checks for the price-increase retention analysis. Reads only saved results in data/*.json.

Run from the repo root:
    poetry run python outputs/2026-11-19_price-increase-retention-rollback/review_checks.py
"""

from pathlib import Path

import pandas as pd

from helpers.checks import date_boundaries, parts_sum_to_total

DATA = Path(__file__).parent / "data"


def load(name: str) -> pd.DataFrame:
    return pd.read_json(DATA / f"{name}.json", lines=True)


def pooled(df: pd.DataFrame) -> float:
    return df["churned_subscriptions_from_start"].sum() / df["active_paid_subscriptions_at_start"].sum()


print("== Mechanics ==")
# Reruns against the database match what the script read.
for name in ["churn_by_plan_month", "churn_by_segment_window"]:
    same = load(name).equals(load(f"review_{name}"))
    print(f"Rerun of {name}: {'matches' if same else 'DOES NOT MATCH'} the saved result.")

# 1. Joins.
fan = load("check_join_fan_out")
for r in fan.itertuples():
    print(f"Join {r.join_name}: {r.rows_before:,} rows before, {r.rows_after:,} after, {r.distinct_keys_after:,} distinct keys.")
grain = load("review_panel_grain").iloc[0]
print(f"Month-by-subscription panel: {grain.panel_rows:,} rows, {grain.distinct_month_subscription:,} distinct "
      f"(month, subscription) pairs, so each subscription is counted at most once a month.")

# 2 and 3. Grain and denominators.
filt = load("review_filters").iloc[0]
print(f"Subscriptions: {filt.all_subscriptions:,}; free dropped {filt.free_dropped:,}; null plan {filt.null_plan}; "
      f"paid with no start {filt.paid_null_start}; paid ending before start {filt.paid_end_before_start}; "
      f"paid with no end date (active) {filt.paid_no_end_date:,}.")
print(f"Paid end dates with a time of day: {filt.paid_end_with_time:,}; start dates: {filt.paid_start_with_time:,}. "
      "Comparisons run against midnight month starts, so a time on a day keeps the row in that day's month.")
opn = load("check_open_windows").iloc[0]
print(f"Scheduled starts after 2026-09-24 kept out: {opn.scheduled_starts_excluded:,}; the latest month used starts 2026-08-01, "
      "so no start after the data's last day can enter a base.")

# 4. Date boundaries.
bounds = load("check_date_boundaries")
for r in bounds.itertuples():
    edges = pd.DataFrame({"d": pd.to_datetime([r.min_value, r.max_value]).tz_localize(None)})
    print(f"{r.column_name}: {date_boundaries(edges, 'd')['summary']}")
months = pd.to_datetime(load("churn_by_plan_month")["month_start"]).dt.tz_localize(None)
print(f"Months in the churn series: {months.min().date()} to {months.max().date()}; the last one closes on 2026-08-31, "
      "before the data's last day, 2026-09-24.")

# Independent recompute of the headline.
ind = load("review_independent_headline").set_index("price_window")
seg = load("churn_by_segment_window")
for w in ["before", "after"]:
    s = seg[(seg["price_window"] == w) & (seg["plan"] == "monthly") & (seg["dimension"] == "all")].iloc[0]
    res = parts_sum_to_total([ind.loc[w, "churned"]], s["churned_subscriptions_from_start"], tolerance=0)
    res_n = parts_sum_to_total([ind.loc[w, "active_at_start"]], s["active_paid_subscriptions_at_start"], tolerance=0)
    print(f"Independent recompute, monthly plan, {w}: churned {res['summary']} Base: {res_n['summary']} "
          f"Rate {ind.loc[w, 'churn_rate']:.4f} vs {s['churn_rate_month_start']:.4f}.")

print("\n== Reasoning ==")
# A. The September 2025 cohort moves from 'under 6 months' to '6 to 12 months' across the two windows.
tj = load("review_tenure_by_join_group")
spike = tj[tj["join_group"] == "started Sep 2025"]
for band in ["under 6 months", "6 to 12 months"]:
    for w in ["before", "after"]:
        cell = tj[(tj["tenure_band"] == band) & (tj["price_window"] == w)]
        share = cell.loc[cell["join_group"] == "started Sep 2025", "active_paid_subscriptions_at_start"].sum() / cell["active_paid_subscriptions_at_start"].sum()
        print(f"Share of '{band}' subscriber-months from the September 2025 cohort, {w}: {share:.1%}.")
rows = []
for band in ["under 6 months", "6 to 12 months", "12 to 24 months", "over 24 months"]:
    with_spike = {w: pooled(tj[(tj["tenure_band"] == band) & (tj["price_window"] == w)]) for w in ["before", "after"]}
    no_spike = {w: pooled(tj[(tj["tenure_band"] == band) & (tj["price_window"] == w) & (tj["join_group"] != "started Sep 2025")])
                for w in ["before", "after"]}
    rows.append({
        "tenure_band": band,
        "change_pp_as_reported": (with_spike["after"] - with_spike["before"]) * 100,
        "change_pp_without_sep_2025": (no_spike["after"] - no_spike["before"]) * 100,
        "before_without": no_spike["before"] * 100, "after_without": no_spike["after"] * 100,
    })
print(pd.DataFrame(rows).round(2).to_string(index=False))

# B. Joined at $12 against moved from $10 to $12, same tenure band, after the increase.
u6 = tj[(tj["tenure_band"] == "under 6 months") & (tj["price_window"] == "after")].set_index("join_group")
joined12 = u6.loc["started from 2026-03-01"]
moved = u6.loc["other start before 2026-03-01"]
print(f"Under 6 months, Mar-Aug 2026: joined at $12 {joined12.churn_rate_month_start:.2%} "
      f"({joined12.churned_subscriptions_from_start} of {joined12.active_paid_subscriptions_at_start:,}) vs joined at $10 and moved "
      f"{moved.churn_rate_month_start:.2%} ({moved.churned_subscriptions_from_start} of {moved.active_paid_subscriptions_at_start:,}); "
      f"{(joined12.churn_rate_month_start - moved.churn_rate_month_start) * 100:+.2f} pp.")
before_u6 = tj[(tj["tenure_band"] == "under 6 months") & (tj["price_window"] == "before") & (tj["join_group"] == "other start before 2026-03-01")].iloc[0]
print(f"Same band before the increase, cohort excluded: {before_u6.churn_rate_month_start:.2%}.")

# C. Does the after-window churn look like a one-off shakeout or a new level?
m = load("churn_by_plan_month")
m = m[m["plan"] == "monthly"].copy()
m["month"] = pd.to_datetime(m["month_start"]).dt.strftime("%Y-%m")
after = m[m["month"] >= "2026-04"]
first2 = pooled(after[after["month"] <= "2026-05"])
last2 = pooled(after[after["month"] >= "2026-07"])
print(f"Monthly-plan churn, Apr-May 2026 {first2:.2%} vs Jul-Aug 2026 {last2:.2%}: "
      f"{(last2 - first2) * 100:+.2f} pp over the five months seen, so no sign yet of churn settling back.")
cash = pd.read_csv(DATA / "monthly_plan_cash_by_window.csv").set_index("price_window")
print(f"Monthly-plan cash: ${cash.loc['before', 'revenue_usd']:,.0f} before vs ${cash.loc['after', 'revenue_usd']:,.0f} after "
      f"({(cash.loc['after', 'revenue_usd'] / cash.loc['before', 'revenue_usd'] - 1) * 100:+.1f}% relative); "
      "the -49% expected revenue per subscriber is a projection at constant churn, not an observed number.")
