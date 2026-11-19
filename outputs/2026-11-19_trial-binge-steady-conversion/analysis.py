"""Do trial users who binge on day one and then go quiet convert worse than steady users?

Reads only the saved query results in data/*.json (the queries are the .sql files next to them).
Run from the repo root:
    poetry run python outputs/2026-11-19_trial-binge-steady-conversion/analysis.py

Population: matured trials, ends_at before 2026-09-25 (the weekly_trial_conversion golden query),
which are the trials started 2026-08-01 to 2026-09-10. Conversion is trial_conversion_rate.

Defined in the plan (no YAML file defines them):
- Day 0 is the trial's start date; the first week is days 0 to 6.
- Binge: day-0 minutes at or above the 75th percentile of matured trials (67 minutes).
- First-week groups: binge then quiet (binge, active on at most 1 of days 1 to 6);
  steady (active on 4 or more of days 0 to 6); light then quiet (no binge, at most 1 of days 1 to 6);
  in between (everyone else).
- Days 0 to 3 view: binge on day 0 crossed with how many of days 1 to 3 the user came back.
  No trial is canceled before day 4, so this pattern is seen before any outcome, for every matured trial.
- Main first-week comparison: trials still in trial through day 6 (converted, or canceled on day 7 or later),
  so that quiet days caused by an early cancellation do not count against a group.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from helpers import charts
from helpers.checks import date_boundaries, parts_sum_to_total

RUN = Path(__file__).parent
DATA = RUN / "data"
CHARTS = RUN / "charts"
Z = 1.96

LABELS = {
    "binge_then_quiet": "Binge then quiet",
    "steady": "Steady",
    "light_then_quiet": "Light then quiet",
    "in_between": "In between",
}


def load(name: str) -> pd.DataFrame:
    return pd.read_json(DATA / f"{name}.json", lines=True)


def wilson(k: float, n: float) -> tuple[float, float]:
    """95% Wilson interval for a proportion; stays sensible for small groups."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    centre = (p + Z**2 / (2 * n)) / (1 + Z**2 / n)
    half = Z * np.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / (1 + Z**2 / n)
    return (centre - half, centre + half)


def diff(k1: float, n1: float, k2: float, n2: float) -> dict:
    """Group 1 minus group 2 in points and relative percent, with a Newcombe 95% interval in points."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    low = d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    high = d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return {
        "rate_1_pct": p1 * 100, "rate_2_pct": p2 * 100,
        "diff_pp": d * 100, "diff_rel_pct": (p1 / p2 - 1) * 100 if p2 else np.nan,
        "ci95_low_pp": low * 100, "ci95_high_pp": high * 100,
    }


def add_rate(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["conversion_pct"] = df["converted"] / df["trials"] * 100
    ci = [wilson(k, n) for k, n in zip(df["converted"], df["trials"])]
    df["ci95_low_pct"] = [c[0] * 100 for c in ci]
    df["ci95_high_pct"] = [c[1] * 100 for c in ci]
    return df


def pct(x: float) -> str:
    return f"{x:.1f}%"


pattern = load("conversion_by_pattern")
early = load("conversion_by_early_pattern")
share = load("conversion_by_day0_share_volume")
pattern_vol = load("conversion_by_pattern_volume")
active = load("conversion_by_active_days")
mix = load("mix_by_pattern")
windows = load("check_open_windows").iloc[0]
fan = load("check_join_fan_out").iloc[0]
bounds = load("check_date_boundaries").iloc[0]

# ---------------------------------------------------------------- checks
print("== Checks ==")
print(
    f"Open windows: {windows['not_matured_excluded']:,} of {windows['trials_total']:,} trials left out because their "
    f"14 days were not over by 2026-09-24 ({windows['not_matured_still_open']:,} still open, "
    f"{windows['not_matured_already_canceled']:,} canceled early but not yet at day 14). "
    f"{windows['matured_without_outcome']} matured trials lack an outcome; "
    f"{windows['converted_not_at_ends_at']} conversions fall off ends_at."
)
print(
    f"Early cancellations: {windows['matured_canceled_before_day7']:,} of {windows['matured']:,} matured trials were canceled "
    f"before day 7 and are left out of the main first-week comparison. Cancellations run from day "
    f"{windows['min_cancel_day']} to day {windows['max_cancel_day']}, so none falls inside days 0 to 3."
)
fan_ok = (
    fan["matured_trials"] == fan["matured_distinct_trials"] == fan["matured_distinct_users"]
    == fan["classified_rows"] == fan["classified_distinct_trials"] == fan["rows_after_users_join"]
    and fan["sessions_via_trial_days"] == fan["sessions_direct"]
    and fan["minutes_via_trials"] == fan["minutes_direct"]
)
print(
    f"Join fan-out: {'passed' if fan_ok else 'FAILED'}. {fan['matured_trials']:,} matured trials stay "
    f"{fan['classified_rows']:,} rows after the sessions join and {fan['rows_after_users_join']:,} after the users join; "
    f"first-week sessions {fan['sessions_via_trial_days']:,} against {fan['sessions_direct']:,} counted directly, "
    f"minutes {fan['minutes_via_trials']:,} against {fan['minutes_direct']:,}."
)
for col_min, col_max, label in [
    ("min_start_day", "max_start_day", "trial start day"),
    ("min_session_day", "max_session_day", "first-week session day"),
]:
    edges = pd.DataFrame({label: [bounds[col_min], bounds[col_max]]})
    edges[label] = pd.to_datetime(edges[label]).dt.tz_localize(None)
    print("Date boundaries:", date_boundaries(edges, label)["summary"])
print(
    f"Trial days in the sessions join run from {bounds['min_trial_day']} to {bounds['max_trial_day']}, "
    "so no session before the start or after day 6 leaks in."
)

matured = int(windows["matured"])
main_n = matured - int(windows["matured_canceled_before_day7"])
total_converted = int(pattern["converted"].sum())
sums = [
    ("first-week groups, all matured trials", pattern["trials"], matured),
    ("first-week groups, still in trial through day 6", pattern.loc[pattern["in_trial_through_day6"], "trials"], main_n),
    ("days 0 to 3 groups, all matured trials", early["trials"], matured),
    ("day-0 share by volume cells", share["trials"], main_n),
    ("pattern by volume cells", pattern_vol["trials"], main_n),
    ("active-day cells", active["trials"], main_n),
    ("conversions in the days 0 to 3 groups", early["converted"], total_converted),
]
for dim in ["device_type", "country", "start_week"]:
    sums.append((f"mix by {dim}", mix.loc[mix["dimension"] == dim, "trials"], main_n))
for label, parts, total in sums:
    print(f"Parts sum ({label}):", parts_sum_to_total(parts, total)["summary"])

# ---------------------------------------------------------------- result tables
pattern_tbl = add_rate(pattern)
pattern_tbl["population"] = np.where(
    pattern_tbl["in_trial_through_day6"], "still in trial through day 6", "canceled before day 7"
)
all_matured = (
    pattern.groupby("pattern", as_index=False)[["trials", "converted"]].sum().assign(population="all matured")
)
pattern_tbl = pd.concat([add_rate(all_matured), pattern_tbl.drop(columns="in_trial_through_day6")], ignore_index=True)
pattern_tbl["label"] = pattern_tbl["pattern"].map(LABELS)
pattern_tbl.to_csv(DATA / "pattern_conversion.csv", index=False)

early_tbl = add_rate(early)
early_tbl["share_of_matured_pct"] = early_tbl["trials"] / matured * 100
early_tbl.to_csv(DATA / "early_pattern_conversion.csv", index=False)


def pick(df: pd.DataFrame, mask) -> tuple[int, int]:
    rows = df[mask]
    return int(rows["converted"].sum()), int(rows["trials"].sum())


binge_quiet_03 = pick(early, early["day0_binge"] & (early["active_days_1_to_3"] == 0))
steady_03 = pick(early, early["active_days_1_to_3"] == 3)
quiet_no_binge_03 = pick(early, ~early["day0_binge"] & (early["active_days_1_to_3"] == 0))
binge_back_03 = pick(early, early["day0_binge"] & (early["active_days_1_to_3"] == 3))
no_binge_back_03 = pick(early, ~early["day0_binge"] & (early["active_days_1_to_3"] == 3))
mostly_quiet_03 = pick(early, early["active_days_1_to_3"] <= 1)
all_03 = pick(early, early["trials"] > 0)

pat_all = all_matured.set_index("pattern")
pat_main = pattern[pattern["in_trial_through_day6"]].set_index("pattern")

comparisons = [
    ("Days 0 to 3: binge then no return vs back on all of days 1 to 3", binge_quiet_03, steady_03),
    ("Days 0 to 3: binge then no return vs no binge and no return", binge_quiet_03, quiet_no_binge_03),
    ("Days 0 to 3: back on all of days 1 to 3, binge vs no binge", binge_back_03, no_binge_back_03),
    ("Days 0 to 3: binge then no return vs all matured trials", binge_quiet_03, all_03),
    ("Days 0 to 3: back on at most 1 of days 1 to 3 vs all matured trials", mostly_quiet_03, all_03),
    ("First week, all matured: binge then quiet vs steady",
     (pat_all.loc["binge_then_quiet", "converted"], pat_all.loc["binge_then_quiet", "trials"]),
     (pat_all.loc["steady", "converted"], pat_all.loc["steady", "trials"])),
    ("First week, still in trial through day 6: binge then quiet vs steady",
     (pat_main.loc["binge_then_quiet", "converted"], pat_main.loc["binge_then_quiet", "trials"]),
     (pat_main.loc["steady", "converted"], pat_main.loc["steady", "trials"])),
]
rows = []
for name, (k1, n1), (k2, n2) in comparisons:
    rows.append({"comparison": name, "converted_1": k1, "trials_1": n1, "converted_2": k2, "trials_2": n2,
                 **diff(k1, n1, k2, n2)})
headline = pd.DataFrame(rows)
headline.to_csv(DATA / "headline_comparisons.csv", index=False)

share_tbl = add_rate(share)
share_tbl.to_csv(DATA / "day0_share_by_volume.csv", index=False)
pattern_vol_tbl = add_rate(pattern_vol)
pattern_vol_tbl.to_csv(DATA / "pattern_by_volume.csv", index=False)
active_tbl = add_rate(active)
active_tbl.to_csv(DATA / "active_days_conversion.csv", index=False)

# Review finding 1: the binge gap at equal return days, from the analysis's own tables.
gap_rows = []
for view, df, col in [("days 0 to 3, all matured", early_tbl, "active_days_1_to_3"),
                      ("first week, still in trial through day 6", active_tbl, "active_days")]:
    for days, grp in df.groupby(col):
        g = grp.set_index("day0_binge")
        if True in g.index and False in g.index:
            gap_rows.append({
                "view": view, "active_days": days,
                "binge_trials": g.loc[True, "trials"], "binge_conversion_pct": g.loc[True, "conversion_pct"],
                "no_binge_trials": g.loc[False, "trials"], "no_binge_conversion_pct": g.loc[False, "conversion_pct"],
                "binge_minus_no_binge_pp": g.loc[True, "conversion_pct"] - g.loc[False, "conversion_pct"],
            })
binge_gap = pd.DataFrame(gap_rows)
binge_gap.to_csv(DATA / "binge_gap_by_active_days.csv", index=False)

mix_tbl = add_rate(mix)
mix_tbl["share_of_value_pct"] = mix_tbl["trials"] / mix_tbl.groupby(["dimension", "value"])["trials"].transform("sum") * 100
mix_tbl.to_csv(DATA / "pattern_mix.csv", index=False)

# ---------------------------------------------------------------- headline numbers
print("\n== Headline ==")
print(
    f"Benchmark: {total_converted:,} of {matured:,} matured trials converted ({pct(total_converted / matured * 100)}); "
    f"{total_converted:,} of {main_n:,} still in trial through day 6 ({pct(total_converted / main_n * 100)})."
)
for _, r in headline.iterrows():
    print(
        f"{r['comparison']}: {r['converted_1']}/{r['trials_1']} ({pct(r['rate_1_pct'])}) vs "
        f"{r['converted_2']}/{r['trials_2']} ({pct(r['rate_2_pct'])}), {r['diff_pp']:+.1f} percentage points "
        f"({r['diff_rel_pct']:+.1f}% relative), 95% interval {r['ci95_low_pp']:+.1f} to {r['ci95_high_pp']:+.1f} points."
    )
print(
    f"Size: binge then no return on days 1 to 3 is {binge_quiet_03[1]} of {matured:,} matured trials "
    f"({pct(binge_quiet_03[1] / matured * 100)}); the strict first-week group is {int(pat_all.loc['binge_then_quiet', 'trials'])} "
    f"({pct(pat_all.loc['binge_then_quiet', 'trials'] / matured * 100)}). Back on at most 1 of days 1 to 3: "
    f"{mostly_quiet_03[1]} ({pct(mostly_quiet_03[1] / matured * 100)})."
)
bq_lo, bq_hi = wilson(*binge_quiet_03)
fw_lo, fw_hi = wilson(pat_all.loc["binge_then_quiet", "converted"], pat_all.loc["binge_then_quiet", "trials"])
print(
    f"Intervals: binge then no return {pct(binge_quiet_03[0] / binge_quiet_03[1] * 100)} "
    f"(95% Wilson {pct(bq_lo * 100)} to {pct(bq_hi * 100)}); first-week binge then quiet "
    f"{pct(pat_all.loc['binge_then_quiet', 'converted'] / pat_all.loc['binge_then_quiet', 'trials'] * 100)} "
    f"(95% Wilson {pct(fw_lo * 100)} to {pct(fw_hi * 100)})."
)
print("\nBinge minus no binge at equal return days, percentage points:")
print(binge_gap[["view", "active_days", "binge_trials", "no_binge_trials", "binge_minus_no_binge_pp"]].round(1).to_string(index=False))

print("\nConversion by day-0 share of first-week minutes, within quarters of first-week minutes (still in trial through day 6):")
wide = share_tbl.pivot(index="day0_share_band", columns="volume_band", values="conversion_pct").round(1)
counts = share_tbl.pivot(index="day0_share_band", columns="volume_band", values="trials")
print(wide.to_string())
print("Trials per cell:")
print(counts.to_string())

print("\nConversion by active days in the first week, day-0 binge or not (still in trial through day 6):")
print(active_tbl.pivot(index="active_days", columns="day0_binge", values="conversion_pct").round(1).to_string())

print("\nPattern share and steady conversion by segment (still in trial through day 6):")
seg = mix_tbl[mix_tbl["pattern"] == "steady"][["dimension", "value", "share_of_value_pct", "trials", "conversion_pct"]]
print(seg.round(1).to_string(index=False))

# ---------------------------------------------------------------- charts
bars = [
    ("Binge, no return", binge_quiet_03),
    ("No binge, no return", quiet_no_binge_03),
    ("Back 1 of 3 days", pick(early, early["active_days_1_to_3"] == 1)),
    ("Back 2 of 3 days", pick(early, early["active_days_1_to_3"] == 2)),
    ("Back all 3 days", steady_03),
]
fig = charts.bar(
    [b[0] for b in bars], [k / n * 100 for _, (k, n) in bars],
    title=f"Bingers who go quiet convert at {binge_quiet_03[0] / binge_quiet_03[1] * 100:.1f}%, "
          f"users back every day at {steady_03[0] / steady_03[1] * 100:.1f}%",
    highlight=["Binge, no return", "Back all 3 days"], ylabel="Converted (%)", fmt="{:.1f}",
    source="Matured trials started 2026-08-01 to 2026-09-10; return days are days 1 to 3 after the start day.",
)
charts.save(fig, CHARTS / "conversion_by_early_pattern.png")

line_df = early_tbl.pivot(index="active_days_1_to_3", columns="day0_binge", values="conversion_pct")
fig = charts.line(
    list(line_df.index),
    {"Binged on day 0": list(line_df[True]), "No day-0 binge": list(line_df[False])},
    title="Coming back on days 1 to 3 moves conversion far more than a day-0 binge",
    highlight=["Binged on day 0"], ylabel="Converted (%)",
    source="Matured trials; binge is 67 or more minutes on the start day (top quarter).",
)
fig.axes[0].set_xticks([0, 1, 2, 3])
fig.axes[0].set_xlabel("Days back out of days 1 to 3")
fig.tight_layout(rect=(0, 0.04, 1, 1))
charts.save(fig, CHARTS / "conversion_by_return_days.png")

band_names = {"1_under_25pct": "Under 25%", "2_25_to_50pct": "25 to 50%", "3_50_to_75pct": "50 to 75%",
              "4_75pct_or_more": "75% or more"}
vol_names = {"1_bottom_quarter": "Bottom quarter", "2_second_quarter": "Second quarter",
             "3_third_quarter": "Third quarter", "4_top_quarter": "Top quarter"}
plot = share_tbl[share_tbl["day0_share_band"].isin(band_names)]
# Reversed so the lines end on the low day-0 share, where they sit far enough apart to label.
plot_wide = plot.pivot(index="day0_share_band", columns="volume_band", values="conversion_pct").iloc[::-1]
fig = charts.line(
    [band_names[b] for b in plot_wide.index],
    {vol_names[v]: list(plot_wide[v]) for v in plot_wide.columns},
    title="At the same first-week minutes, conversion rises as less of the week falls on day 0",
    highlight=["Second quarter", "Third quarter"], ylabel="Converted (%)",
    source="Trials still in trial through day 6; lines are quarters of total first-week minutes.",
)
fig.axes[0].set_xlabel("Share of first-week minutes on day 0")
fig.tight_layout(rect=(0, 0.04, 1, 1))
charts.save(fig, CHARTS / "conversion_by_day0_share.png")

print(f"\nTables and charts written to {RUN}")
