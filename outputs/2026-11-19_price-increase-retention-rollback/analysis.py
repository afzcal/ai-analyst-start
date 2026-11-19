"""Did the March 2026 price increase hurt retention, and for whom?

Reads only the saved query results in data/*.json (the queries are the .sql files next to them).
Run from the repo root:
    poetry run python outputs/2026-11-19_price-increase-retention-rollback/analysis.py

Windows (months of churn_rate_month_start, pooled):
    a_year_earlier = Mar to Aug 2025, before = Sep 2025 to Feb 2026, after = Mar to Aug 2026.
September 2026 is left out because the data stops on 2026-09-24.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from helpers import charts
from helpers.checks import date_boundaries, parts_sum_to_total

RUN = Path(__file__).parent
DATA = RUN / "data"
CHARTS = RUN / "charts"

OLD_PRICE, NEW_PRICE = 10, 12
# Defined in the plan: at a constant monthly churn c, a subscriber pays price / c in expectation,
# so a 20% higher price keeps revenue per subscriber whole only while churn rises by less than 12/10.
BREAK_EVEN_RATIO = NEW_PRICE / OLD_PRICE
WINDOWS = {
    "a_year_earlier": pd.period_range("2025-03", "2025-08", freq="M"),
    "before": pd.period_range("2025-09", "2026-02", freq="M"),
    "after": pd.period_range("2026-03", "2026-08", freq="M"),
}


def load(name: str) -> pd.DataFrame:
    return pd.read_json(DATA / f"{name}.json", lines=True)


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def change_table(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Before and after pooled churn side by side, with the change in points, relative, and a 95% interval."""
    wide = df.pivot_table(
        index=keys, columns="price_window",
        values=["active_paid_subscriptions_at_start", "churned_subscriptions_from_start"], aggfunc="sum",
    )
    out = pd.DataFrame(index=wide.index)
    for w in ["before", "after"]:
        out[f"n_{w}"] = wide[("active_paid_subscriptions_at_start", w)]
        out[f"churned_{w}"] = wide[("churned_subscriptions_from_start", w)]
        out[f"churn_{w}"] = out[f"churned_{w}"] / out[f"n_{w}"]
    out["change_pp"] = (out["churn_after"] - out["churn_before"]) * 100
    out["change_rel_pct"] = (out["churn_after"] / out["churn_before"] - 1) * 100
    out["ratio_after_to_before"] = out["churn_after"] / out["churn_before"]
    # Normal approximation on subscriber-months; a subscriber appears in several months of a window.
    se = np.sqrt(
        out["churn_before"] * (1 - out["churn_before"]) / out["n_before"]
        + out["churn_after"] * (1 - out["churn_after"]) / out["n_after"]
    )
    out["ci95_low_pp"] = out["change_pp"] - 1.96 * se * 100
    out["ci95_high_pp"] = out["change_pp"] + 1.96 * se * 100
    return out.reset_index()


monthly = load("churn_by_plan_month")
monthly["month"] = pd.to_datetime(monthly["month_start"]).dt.tz_localize(None).dt.to_period("M")
seg = load("churn_by_segment_window")
cross = load("churn_country_tenure_window")
join_grp = load("churn_tenure_by_join_group")
price_month = load("price_by_month")
price_month["month"] = pd.to_datetime(price_month["payment_month"]).dt.tz_localize(None).dt.to_period("M")
price_cohort = load("price_by_start_cohort")
fan_out = load("check_join_fan_out")
bounds = load("check_date_boundaries")
open_win = load("check_open_windows").iloc[0]

# ---------------------------------------------------------------- checks
print("== Checks ==")
for row in fan_out.itertuples():
    ok = row.rows_after == row.rows_before == row.distinct_keys_after
    print(f"Join fan-out, {row.join_name}: {row.rows_before:,} rows before, {row.rows_after:,} after, "
          f"{row.distinct_keys_after:,} distinct keys, so {'no fan-out' if ok else 'IT FANS OUT'}.")

for row in bounds.itertuples():
    edges = pd.DataFrame({"d": pd.to_datetime([row.min_value, row.max_value]).tz_localize(None)})
    print(f"{row.column_name}: {date_boundaries(edges, 'd')['summary']}")
print("The last month used is August 2026, so the partial September 2026 is outside every window.")

print(f"Open windows: {open_win.scheduled_starts_excluded:,} paid subscriptions with a scheduled start after "
      f"2026-09-24 are in no base; {open_win.scheduled_ends_counted_active:,} with a scheduled end after 2026-09-24 "
      f"count as active; {open_win.ended_sep_2026_left_out:,} ended in September 2026 (open month, left out); "
      f"{open_win.started_from_aug_2026_in_no_base:,} started from August 2026 (trial conversions among them) "
      f"and are in no month-start base yet.")

seg_checks_ok = True
for (window, plan), grp in seg.groupby(["price_window", "plan"]):
    total = grp.loc[grp["dimension"] == "all"].iloc[0]
    for dim, parts in grp[grp["dimension"] != "all"].groupby("dimension"):
        for col in ["active_paid_subscriptions_at_start", "churned_subscriptions_from_start"]:
            res = parts_sum_to_total(parts[col], total[col], tolerance=0)
            seg_checks_ok &= res["ok"]
            if not res["ok"]:
                print(f"Parts check failed: {window}, {plan}, {dim}, {col}: {res['summary']}")
print(f"Segments sum to their plan totals in every window and dimension: {seg_checks_ok}.")

for window, months in WINDOWS.items():
    for plan in ["monthly", "annual"]:
        m = monthly[(monthly["plan"] == plan) & monthly["month"].isin(months)]
        total = seg[(seg["price_window"] == window) & (seg["plan"] == plan) & (seg["dimension"] == "all")].iloc[0]
        res = parts_sum_to_total(m["churned_subscriptions_from_start"], total["churned_subscriptions_from_start"], 0)
        res_n = parts_sum_to_total(m["active_paid_subscriptions_at_start"], total["active_paid_subscriptions_at_start"], 0)
        print(f"Monthly series vs window total, {window}, {plan}: churned {res['summary']} Base: {res_n['summary']}")

for window in ["before", "after"]:
    total = seg[(seg["price_window"] == window) & (seg["plan"] == "monthly") & (seg["dimension"] == "all")].iloc[0]
    cells = cross[cross["price_window"] == window]
    res = parts_sum_to_total(cells["active_paid_subscriptions_at_start"], total["active_paid_subscriptions_at_start"], 0)
    print(f"Country by tenure cells vs monthly total, {window}: {res['summary']}")
    cells = join_grp[join_grp["price_window"] == window]
    res = parts_sum_to_total(cells["churned_subscriptions_from_start"], total["churned_subscriptions_from_start"], 0)
    print(f"Tenure by join group cells vs monthly total, {window}: churned {res['summary']}")

monthly_pay = price_cohort[price_cohort["plan"] == "monthly"]
grandfathered = monthly_pay[(monthly_pay["payment_period"] == "paid from 2026-03-01") & (monthly_pay["amount_usd"] != NEW_PRICE)]
old_after = int(grandfathered["payments"].sum())
print(f"Monthly payments from 2026-03-01 not at ${NEW_PRICE}: {old_after:,} "
      f"(of {int(monthly_pay.loc[monthly_pay['payment_period'] == 'paid from 2026-03-01', 'payments'].sum()):,}); "
      f"subscribers who started before the increase were {'not ' if old_after == 0 else ''}kept on the old price.")
annual_amounts = sorted(int(a) for a in price_cohort.loc[price_cohort["plan"] == "annual", "amount_usd"].unique())
print(f"Annual payment amounts in all periods: {annual_amounts}, so the annual price did not change.")

# ---------------------------------------------------------------- 1. headline: monthly vs annual, three windows
overall = seg[seg["dimension"] == "all"][
    ["price_window", "plan", "active_paid_subscriptions_at_start", "churned_subscriptions_from_start"]
].copy()
overall["churn_pct"] = overall["churned_subscriptions_from_start"] / overall["active_paid_subscriptions_at_start"] * 100
overall["price_window"] = pd.Categorical(overall["price_window"], ["a_year_earlier", "before", "after"], ordered=True)
overall = overall.sort_values(["plan", "price_window"])
overall.to_csv(DATA / "churn_overall_by_window.csv", index=False)

ov = overall.set_index(["plan", "price_window"])["churn_pct"]
m_change = ov["monthly", "after"] - ov["monthly", "before"]
a_change = ov["annual", "after"] - ov["annual", "before"]
print("\n== 1. Pooled monthly churn of the starting base (churn_rate_month_start) ==")
for plan in ["monthly", "annual"]:
    print(f"{plan:8s}: Mar-Aug 2025 {ov[plan, 'a_year_earlier']:.2f}%, Sep 2025-Feb 2026 {ov[plan, 'before']:.2f}%, "
          f"Mar-Aug 2026 {ov[plan, 'after']:.2f}%")
print(f"Monthly plan: {m_change:+.2f} pp before to after ({(ov['monthly', 'after'] / ov['monthly', 'before'] - 1) * 100:+.0f}% relative, "
      f"{ov['monthly', 'after'] / ov['monthly', 'before']:.2f}x).")
print(f"Annual plan (price unchanged): {a_change:+.2f} pp. Difference in differences: {m_change - a_change:+.2f} pp.")

mon_m = monthly[monthly["plan"] == "monthly"].set_index("month")
before_range = mon_m.loc[WINDOWS["before"], "churn_rate_month_start"]
print(f"Monthly plan by month: Sep 2025-Feb 2026 ranged {pct(before_range.min())} to {pct(before_range.max())}; "
      f"March 2026 (first month billed at $12) {pct(mon_m.loc[pd.Period('2026-03', 'M'), 'churn_rate_month_start'])}; "
      f"April to August 2026 " + ", ".join(pct(v) for v in mon_m.loc[pd.period_range('2026-04', '2026-08', freq='M'), 'churn_rate_month_start'])
      + ".")
print("Note: the September 2025 signup spike enters the before window; it is split out in section 2.")

series = monthly.pivot(index="month", columns="plan", values="churn_rate_month_start") * 100
series.index = series.index.astype(str)
series.to_csv(DATA / "churn_month_start_by_plan_month.csv")
fig = charts.line(
    series.index, {"Monthly plan": series["monthly"], "Annual plan": series["annual"]},
    title="Monthly-plan churn more than doubled from April 2026; annual churn did not move",
    highlight="Monthly plan", ylabel="Monthly churn of the starting base (%)",
    source="Source: subscriptions, churn_rate_month_start, Jan 2025 to Aug 2026. Monthly price \\$10 to \\$12 on 2026-03-01.",
)
ax = fig.axes[0]
ax.axvline(pd.Timestamp("2026-03-01"), color=charts.GRAY, linestyle="--", linewidth=1)
ax.annotate("Price \\$10 to \\$12", xy=(pd.Timestamp("2026-03-01"), ax.get_ylim()[1] * 0.95),
            xytext=(-5, 0), textcoords="offset points", ha="right", color=charts.TEXT, fontsize=9)
charts.save(fig, CHARTS / "churn_by_plan_month.png")

# ---------------------------------------------------------------- 2. for whom: monthly plan by segment
seg_ba = seg[seg["price_window"].isin(["before", "after"])]
by_seg = change_table(seg_ba, ["plan", "dimension", "segment"])
# Tenure bands are not groups people stay in, so the constant-churn break-even only applies to the other dimensions.
by_seg["above_break_even"] = np.where(
    by_seg["dimension"] == "tenure_band", np.nan, by_seg["ratio_after_to_before"] > BREAK_EVEN_RATIO
)
annual_change = by_seg[by_seg["plan"] == "annual"].set_index(["dimension", "segment"])["change_pp"]
by_seg_m = by_seg[by_seg["plan"] == "monthly"].copy()
by_seg_m["annual_change_pp"] = [annual_change.get((d, s), np.nan) for d, s in zip(by_seg_m["dimension"], by_seg_m["segment"])]
by_seg_m["diff_in_diff_pp"] = by_seg_m["change_pp"] - by_seg_m["annual_change_pp"]
# The September 2025 cohort is half of "under 6 months" before the increase and half of "6 to 12 months" after it,
# so tenure bands are reported without it (review finding 1). The rows with it stay in the CSV, labeled.
by_seg_m.loc[by_seg_m["dimension"] == "tenure_band", "dimension"] = "tenure_band_incl_sep_2025"
no_spike = join_grp[join_grp["join_group"] != "started Sep 2025"].assign(
    plan="monthly", dimension="tenure_band", segment=lambda d: d["tenure_band"]
)
tenure_ex = change_table(no_spike, ["plan", "dimension", "segment"])
tenure_ex["above_break_even"] = np.nan
by_seg_m = pd.concat([by_seg_m, tenure_ex], ignore_index=True)
order = {"all": 0, "tenure_band": 1, "tenure_band_incl_sep_2025": 2, "country": 3, "device_type": 4, "start_cohort": 5}
tenure_order = {"under 6 months": 0, "6 to 12 months": 1, "12 to 24 months": 2, "over 24 months": 3}
by_seg_m["_o1"] = by_seg_m["dimension"].map(order)
by_seg_m["_o2"] = by_seg_m["segment"].map(tenure_order).fillna(0)
by_seg_m = by_seg_m.sort_values(["_o1", "_o2", "segment"]).drop(columns=["_o1", "_o2"])
by_seg_m.to_csv(DATA / "monthly_churn_change_by_segment.csv", index=False)
by_seg[by_seg["plan"] == "annual"].to_csv(DATA / "annual_churn_change_by_segment.csv", index=False)

print("\n== 2. Monthly plan, Sep 2025-Feb 2026 vs Mar-Aug 2026, by segment ==")
print(f"Break-even (defined in plan, a projection): churn may rise by at most {BREAK_EVEN_RATIO:.1f}x for the $12 price to keep "
      f"expected revenue per subscriber at the $10 level, if churn stays at its new rate.")
print("tenure_band rows exclude the September 2025 cohort; tenure_band_incl_sep_2025 rows are the bands with it.")
for r in by_seg_m.itertuples():
    be = "" if pd.isna(r.above_break_even) else ("  above break-even" if r.above_break_even else "  below break-even")
    print(f"{r.dimension:12s} {r.segment:22s} {r.churn_before * 100:5.2f}% -> {r.churn_after * 100:5.2f}%  "
          f"{r.change_pp:+5.2f} pp [{r.ci95_low_pp:+.2f}, {r.ci95_high_pp:+.2f}]  {r.ratio_after_to_before:.2f}x  "
          f"annual {r.annual_change_pp:+5.2f} pp{be}")

# US against the other three markets, before and after.
country = seg_ba[(seg_ba["plan"] == "monthly") & (seg_ba["dimension"] == "country")].copy()
country["market"] = np.where(country["segment"] == "US", "US", "EU, India and Rest")
us_vs = change_table(country, ["market"])
us_vs.to_csv(DATA / "monthly_churn_change_us_vs_rest.csv", index=False)
us, rest = us_vs.set_index("market").loc["US"], us_vs.set_index("market").loc["EU, India and Rest"]
gap = rest["change_pp"] - us["change_pp"]
gap_se = np.sqrt(((us["ci95_high_pp"] - us["change_pp"]) / 1.96) ** 2 + ((rest["ci95_high_pp"] - rest["change_pp"]) / 1.96) ** 2)
print(f"US {us['change_pp']:+.2f} pp vs EU, India and Rest {rest['change_pp']:+.2f} pp: the other markets rose "
      f"{gap:.2f} pp more (95% interval {gap - 1.96 * gap_se:+.2f} to {gap + 1.96 * gap_se:+.2f}).")

plot = by_seg_m[~by_seg_m["dimension"].isin(["all", "tenure_band_incl_sep_2025"])].copy()
labels = {
    "tenure_band": "Tenure", "country": "Market", "device_type": "Device", "start_cohort": "Cohort",
}
plot["label"] = plot["dimension"].map(labels) + ": " + plot["segment"]
overall_pp = by_seg_m.loc[by_seg_m["dimension"] == "all", "change_pp"].iloc[0]
fig = charts.bar(
    plot["label"], plot["change_pp"].round(1),
    title="Churn rose in every group, most for subscribers in their first 6 months",
    highlight=list(plot.loc[plot["change_pp"] > overall_pp, "label"]),
    ylabel=None, horizontal=True, fmt="{:+.1f}",
    source=f"Monthly plan, change in pooled monthly churn (pp), Sep 2025-Feb 2026 to Mar-Aug 2026. All monthly: {overall_pp:+.1f} pp.\n"
           "Tenure bands exclude the September 2025 signup-spike cohort.",
)
fig.subplots_adjust(bottom=0.17)  # room for the two-line source note under the tick labels
charts.save(fig, CHARTS / "churn_change_by_segment.png")

# Joined at $12 against joined at $10 and moved, in their first 6 months (review finding 2).
u6 = join_grp[join_grp["tenure_band"] == "under 6 months"].set_index(["price_window", "join_group"])
jg = pd.DataFrame([
    {"group": "Before: joined at $10", **u6.loc[("before", "other start before 2026-03-01")].to_dict()},
    {"group": "After: joined at $10, moved to $12", **u6.loc[("after", "other start before 2026-03-01")].to_dict()},
    {"group": "After: joined at $12", **u6.loc[("after", "started from 2026-03-01")].to_dict()},
])
jg["churn_pct"] = jg["churned_subscriptions_from_start"] / jg["active_paid_subscriptions_at_start"] * 100
jg.to_csv(DATA / "monthly_churn_under_6_months_by_join_group.csv", index=False)
p12, n12 = jg.loc[2, "churn_pct"] / 100, jg.loc[2, "active_paid_subscriptions_at_start"]
pmv, nmv = jg.loc[1, "churn_pct"] / 100, jg.loc[1, "active_paid_subscriptions_at_start"]
diff = (p12 - pmv) * 100
se = np.sqrt(p12 * (1 - p12) / n12 + pmv * (1 - pmv) / nmv) * 100
print("Monthly plan, first 6 months of tenure, September 2025 cohort excluded:")
for r in jg.itertuples():
    print(f"  {r.group:36s} {r.churn_pct:5.2f}% ({r.churned_subscriptions_from_start} of {r.active_paid_subscriptions_at_start:,})")
print(f"  Joined at $12 vs joined at $10 and moved: {diff:+.2f} pp (95% interval {diff - 1.96 * se:+.2f} to {diff + 1.96 * se:+.2f}).")
fig = charts.bar(
    jg["group"].str.replace("$", r"\$", regex=False), jg["churn_pct"].round(1),
    title="Subscribers who joined at \\$12 leave fastest in their first 6 months",
    highlight=["After: joined at \\$12"], horizontal=True, fmt="{:.1f}%",
    source="Monthly plan, pooled monthly churn in the first 6 months of tenure. Before: Sep 2025-Feb 2026; after: Mar-Aug 2026.\n"
           "September 2025 signup-spike cohort excluded.",
)
fig.subplots_adjust(bottom=0.17)  # room for the two-line source note under the tick labels
charts.save(fig, CHARTS / "churn_first_6_months_by_join_group.png")

stable = plot[plot["dimension"] != "tenure_band"]
fig = charts.bar(
    stable["label"], stable["ratio_after_to_before"].round(1),
    title="If churn stays at its new level, every group is past the 1.2x a 20% price rise can absorb",
    highlight=list(stable.loc[stable["ratio_after_to_before"] > BREAK_EVEN_RATIO, "label"]),
    horizontal=True, fmt="{:.1f}x",
    source="Monthly plan, churn Mar-Aug 2026 divided by churn Sep 2025-Feb 2026. Dashed line: break-even at 12/10 = 1.2x.\n"
           "A projection at constant churn, not an observed revenue change.",
)
fig.axes[0].axvline(BREAK_EVEN_RATIO, color=charts.TEXT, linestyle="--", linewidth=1)
fig.subplots_adjust(bottom=0.17)  # room for the two-line source note under the tick labels
charts.save(fig, CHARTS / "churn_ratio_vs_break_even.png")

# ---------------------------------------------------------------- 3. country within tenure band
ct = change_table(cross, ["tenure_band", "country"])
ct["_o"] = ct["tenure_band"].map(tenure_order)
ct = ct.sort_values(["_o", "country"]).drop(columns="_o")
ct.to_csv(DATA / "monthly_churn_change_country_by_tenure.csv", index=False)
print("\n== 3. Monthly plan, change in pp by tenure band and market ==")
pivot = ct.pivot(index="tenure_band", columns="country", values="change_pp").loc[list(tenure_order)]
print(pivot.round(2).to_string())
us_lowest = (pivot["US"] == pivot.min(axis=1))
print(f"US has the smallest rise in {int(us_lowest.sum())} of 4 tenure bands.")

# ---------------------------------------------------------------- 4. revenue and base context
mp = price_month[price_month["plan"] == "monthly"]
rev = {w: mp[mp["month"].isin(WINDOWS[w])][["payments", "revenue_usd"]].sum() for w in ["before", "after"]}
rev_tbl = pd.DataFrame(rev).T
rev_tbl.index.name = "price_window"
rev_tbl.to_csv(DATA / "monthly_plan_cash_by_window.csv")
print("\n== 4. Monthly plan cash and base ==")
print(f"Cash from monthly payments: ${rev['before']['revenue_usd']:,.0f} (Sep 2025-Feb 2026) -> "
      f"${rev['after']['revenue_usd']:,.0f} (Mar-Aug 2026), {(rev['after']['revenue_usd'] / rev['before']['revenue_usd'] - 1) * 100:+.1f}% relative; "
      f"payments {rev['before']['payments']:,.0f} -> {rev['after']['payments']:,.0f}, "
      f"{(rev['after']['payments'] / rev['before']['payments'] - 1) * 100:+.1f}% relative.")
base = mon_m["active_paid_subscriptions_at_start"]
b25 = base[pd.Period("2025-08", "M")] / base[pd.Period("2025-03", "M")] - 1
b26 = base[pd.Period("2026-08", "M")] / base[pd.Period("2026-03", "M")] - 1
base_tbl = pd.DataFrame({
    "period": ["Mar to Aug 2025", "Mar to Aug 2026"],
    "base_march": [base[pd.Period("2025-03", "M")], base[pd.Period("2026-03", "M")]],
    "base_august": [base[pd.Period("2025-08", "M")], base[pd.Period("2026-08", "M")]],
    "change_rel_pct": [b25 * 100, b26 * 100],
})
base_tbl.to_csv(DATA / "monthly_base_growth.csv", index=False)
print(f"Monthly subscribers active on the 1st: March to August 2025 {b25 * 100:+.1f}% relative; "
      f"March to August 2026 {b26 * 100:+.1f}% relative.")
ev_before = OLD_PRICE / (ov["monthly", "before"] / 100)
ev_after = NEW_PRICE / (ov["monthly", "after"] / 100)
print(f"Projection, not observed: expected revenue per monthly subscriber at constant churn (defined in plan): ${ev_before:,.0f} at $10 and "
      f"{ov['monthly', 'before']:.2f}% churn vs ${ev_after:,.0f} at $12 and {ov['monthly', 'after']:.2f}% churn "
      f"({(ev_after / ev_before - 1) * 100:+.0f}% relative). Holds only if churn stays at the Mar-Aug 2026 rate; "
      f"observed cash over the same six months rose {(rev['after']['revenue_usd'] / rev['before']['revenue_usd'] - 1) * 100:+.1f}%.")
pd.DataFrame({
    "price_usd": [OLD_PRICE, NEW_PRICE], "monthly_churn_pct": [ov["monthly", "before"], ov["monthly", "after"]],
    "expected_revenue_per_subscriber_usd": [ev_before, ev_after],
}, index=["before", "after"]).to_csv(DATA / "expected_revenue_per_subscriber.csv")
