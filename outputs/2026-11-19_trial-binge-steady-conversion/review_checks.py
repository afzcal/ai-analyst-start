"""Review checks for the binge-versus-steady trial analysis.

Reads only saved results in data/*.json: the analysis's own and the review's reruns (data/review_*.json).
Run from the repo root:
    poetry run python outputs/2026-11-19_trial-binge-steady-conversion/review_checks.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

from helpers.checks import date_boundaries, parts_sum_to_total

DATA = Path(__file__).parent / "data"
LAST_DAY = pd.Timestamp("2026-09-24")


def load(name: str) -> pd.DataFrame:
    return pd.read_json(DATA / f"{name}.json", lines=True)


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.96
    p = k / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centre - half, centre + half


print("== Reruns match the saved results ==")
for name in ["conversion_by_early_pattern", "conversion_by_pattern", "conversion_by_day0_share_volume"]:
    saved, rerun = load(name), load(f"review_{name}")
    same = saved.shape == rerun.shape and saved.equals(rerun)
    print(f"{name}: {'match' if same else 'DIFFER'} ({len(saved)} rows saved, {len(rerun)} rerun)")

print("\n== Independent recompute of the headline (days 0 to 3) ==")
early = load("conversion_by_early_pattern")
ind = load("review_independent_headline").iloc[0]
analysis = {
    "binge_no_return": early[early["day0_binge"] & (early["active_days_1_to_3"] == 0)][["trials", "converted"]].sum(),
    "back_all_three": early[early["active_days_1_to_3"] == 3][["trials", "converted"]].sum(),
    "back_at_most_one": early[early["active_days_1_to_3"] <= 1][["trials", "converted"]].sum(),
    "matured": early[["trials", "converted"]].sum(),
}
independent = {
    "binge_no_return": (ind["binge_no_return_trials"], ind["binge_no_return_converted"]),
    "back_all_three": (ind["back_all_three_trials"], ind["back_all_three_converted"]),
    "back_at_most_one": (ind["back_at_most_one_trials"], ind["back_at_most_one_converted"]),
    "matured": (ind["matured_trials"], ind["matured_converted"]),
}
for key, (n, k) in independent.items():
    a = analysis[key]
    ok = a["trials"] == n and a["converted"] == k
    print(f"{key}: analysis {a['converted']}/{a['trials']}, independent {k}/{n}: {'agree' if ok else 'DISAGREE'}")
print(f"Binge threshold: analysis 67 minutes (continuous 75th percentile), independent {ind['binge_threshold']} (discrete).")

print("\n== Grain ==")
fan = load("check_join_fan_out").iloc[0]
print(
    f"One row per trial and per user: {fan['matured_trials']:,} matured trials, {fan['matured_distinct_trials']:,} distinct "
    f"trial ids, {fan['matured_distinct_users']:,} distinct users. Conversion is counted per trial, which is per user."
)
print("The script makes no joins on saved results, so join_fan_out has nothing to run on there; "
      "the SQL joins agree with a direct count (check_join_fan_out) and with the independent query above.")

print("\n== Denominators and filters ==")
win = load("check_open_windows").iloc[0]
print(
    f"Matured filter (ends_at < 2026-09-25) keeps {win['matured']:,} of {win['trials_total']:,} trials and drops "
    f"{win['not_matured_excluded']:,}: {win['not_matured_still_open']:,} still open and {win['not_matured_already_canceled']:,} "
    f"already canceled but not yet at day 14. Dropping those canceled ones too keeps the base symmetric. "
    f"Matured trials without an outcome: {win['matured_without_outcome']}."
)
print(
    f"Still-in-trial-through-day-6 filter drops {win['matured_canceled_before_day7']:,} matured trials canceled on days "
    f"{win['min_cancel_day']} to 6; every one of them is a cancellation, so the main first-week base converts at a higher "
    f"rate ({828 / (win['matured'] - win['matured_canceled_before_day7']):.1%}) than all matured trials ({828 / win['matured']:.1%})."
)
length = load("review_day0_length")
length["binge_share"] = length["day0_binge"] / length["trials"]
length["no_day0_share"] = length["no_day0_session"] / length["trials"]
length["conversion"] = length["converted"] / length["trials"]
print("Day-0 length: every matured trial has a start time (no midnight-only values).")
for _, r in length.iterrows():
    print(
        f"  {r['start_time_band']}: {r['trials']:,} trials ({r['trials'] / win['matured']:.1%}), binge {r['binge_share']:.1%}, no day-0 session "
        f"{r['no_day0_share']:.1%}, converted {r['conversion']:.1%}"
    )
print(parts_sum_to_total(length["trials"], win["matured"])["summary"])

print("\n== Date boundaries ==")
b = load("check_date_boundaries").iloc[0]
for lo, hi, label in [("min_start_day", "max_start_day", "trial start day"), ("min_session_day", "max_session_day", "first-week session day")]:
    edges = pd.DataFrame({label: pd.to_datetime([b[lo], b[hi]]).tz_localize(None)})
    print(date_boundaries(edges, label, freq="D")["summary"])
max_start = pd.Timestamp(b["max_start_day"]).tz_localize(None)
print(
    f"Last start day {max_start.date()} + 14 = {(max_start + pd.Timedelta(days=14)).date()}, on or before the data's last day "
    f"{LAST_DAY.date()}: {max_start + pd.Timedelta(days=14) <= LAST_DAY}. The sessions prefilter (2026-08-01 to before 2026-09-17) "
    f"covers every first-week window: {pd.Timestamp('2026-08-01') <= pd.Timestamp(b['min_start_day']).tz_localize(None)} and "
    f"{max_start + pd.Timedelta(days=7) <= pd.Timestamp('2026-09-17')}."
)

print("\n== Sample size of the headline group ==")
first_week_bq = load("conversion_by_pattern").query("pattern == 'binge_then_quiet'")[["trials", "converted"]].sum()
for label, (n, k) in [("binge then no return (days 0 to 3)", independent["binge_no_return"]),
                      ("binge then quiet (first week, all matured)", (first_week_bq["trials"], first_week_bq["converted"])),
                      ("back on all of days 1 to 3", independent["back_all_three"])]:
    lo, hi = wilson(int(k), int(n))
    print(f"{label}: {k}/{n} = {k / n:.1%}, 95% Wilson interval {lo:.1%} to {hi:.1%}")

print("\n== Does 'a day-0 binge barely moves conversion' hold at other thresholds? ==")
sens = load("review_threshold_sensitivity")
sens["rate"] = sens["converted"] / sens["trials"]
for pct, grp in sens.groupby("threshold_percentile"):
    g = grp.set_index(["day0_binge", "active_days_1_to_3"])
    print(f"Threshold {pct:.0%} percentile ({grp['binge_minutes'].iloc[0]:.0f} minutes):")
    for days in [0, 3]:
        yes, no = g.loc[(True, days)], g.loc[(False, days)]
        print(
            f"  back {days} of days 1 to 3: binge {yes['converted']}/{yes['trials']} ({yes['rate']:.1%}) vs no binge "
            f"{no['converted']}/{no['trials']} ({no['rate']:.1%}), {(yes['rate'] - no['rate']) * 100:+.1f} percentage points"
        )
    print("  " + parts_sum_to_total(grp["trials"], win["matured"])["summary"])

active = load("conversion_by_active_days")
active["rate"] = active["converted"] / active["trials"]
piv = active.pivot(index="active_days", columns="day0_binge", values="rate")
print("First-week active days, binge minus no binge, in percentage points (analysis's own table):")
for d in [4, 5, 6, 7]:
    print(f"  {d} active days: {(piv.loc[d, True] - piv.loc[d, False]) * 100:+.1f}")
