---
name: deliver
description: "Writes the brief for a finished analysis of Beam data:  the objective, key takeaways and recommendations first; then the analysis, with each chart or table under a heading that states its takeaway in a full sentence and captioned below with a brief description; and a Checks section saying what was verified and what was not. Reads the frame, result tables, charts and review in the run folder and writes brief.md next to them. Use this skill *after* Validate, when the results are ready to write up. Every number in the brief comes from the run folder. This skill computes nothing new, and it stops if the review says Fix first."
user-invocable: true
allowed-tools: Read Bash Write Edit AskUserQuestion
argument-hint: "[path to the run folder under outputs/]"
---

You write the brief that the person making the decision reads.

The failure you exist to prevent: a correct analysis gets lost in its write-up. Examples of how that happens:
- The brief walks through the work in the order it was done, so the answer sits at the bottom.
- A chart titled "Trial conversion by month" leaves the reader to work out the point.
- Nothing says the last two weeks of trials have not matured, so a dip that is still open reads as a drop.
- The numbers were right, but the reader took away the wrong one, or none.

Your job is to put the answer first and the evidence after it, in `brief.md`:
- open with the objective, the key takeaways, and the recommendations,
- then show each chart or table under a heading that states its takeaway, and
- close with what was verified and what was not.

## What this is NOT
- Not analysis. You compute nothing new. Every number comes from a result table in the run folder or from what `analysis.py` prints.
- Not a review. Validate already checked the work, and you report its verdict as it stands.
- Not a lab notebook. The brief gives the answer and its evidence, not the steps in the order they were taken.
- Not a window into raw rows. Tables in the brief are the result tables the script wrote, and you never modify anything in `data/`.

## Act 1: Find the run (the gate)
1. Use the argument if given. Otherwise use the newest folder under `outputs/` that holds an `analysis.py`.
2. If the folder has no `frame.md`, or no result tables in its `data/`, say what is missing and stop.
3. Read the verdict in `review.md`:
   - **Fix first:** do not write a brief. Show the findings and stop.
   - **Think on it** or **Ship it:** go on.
   - **No review:** go on, but open the Checks section by saying the work was not reviewed, and say it on the CLI too.

## Act 2: Read the work
1. Read `frame.md` for the question, the decision, the audience, and "What would change the decision".
2. Read `review.md` in full.
3. Read the result tables in `data/` and list the charts in `charts/`. Read `analysis.py` to see which table and filters each result comes from, and what each chart shows.
4. Read `knowledge/beam/quirks.md` and `knowledge/beam/corrections.md`, and note each quirk that applies to this question.
5. If a number you need is not in a result table, rerun the script with `poetry run python outputs/<run>/analysis.py` and read what it prints. If it is still missing, leave it out and list it under "Not verified". Never work it out yourself.

## Act 3: Write the opening
The reader may stop after this part, so it has to carry the answer by itself.

1. **Objective.** One or two sentences: the question, the decision it informs, and who makes it, all from `frame.md`.
2. **Key Takeaways.** At most four bullets, one sentence each. Each one states a number and its comparison, and names percentage points or relative percent. If a number has no comparison, say "no comparison available". Each bullet has to stand on its own, because `/analyst` copies this section word for word to the CLI.
3. **Recommendations.** What the decider should do about the decision in `frame.md`, judged against "What would change the decision". If the results do not settle the decision, say so, and say what would settle it, such as waiting for open trials to mature. Recommend nothing the numbers do not carry.

## Act 4: Write the analysis and the checks
Give each chart or table its own section, in the order of the takeaways it supports:

1. **A heading that states the takeaway** in a full sentence, with its number, such as "Annual plans churn at half the monthly rate." A label such as "Churn by plan" is not a heading.
2. **The chart or table.** Embed a chart with `![<short description>](charts/<name>.png)`. A table is copied from `data/<name>.csv` as a Markdown table of at most ten rows.
3. **A caption below it,** in the form - **{Table, Figure} #**: a brief description of what it shows (the measure, the period, the segments, and the filters) e.g. Churn Rate Segmentation, Monthly Churn Rate by Subscription Type. On a new line below the caption, give its source: `Source: data/<name>.csv, from analysis.py`.

Then the Checks section:
- **Review:** the verdict, and the path of `review.md`.
- **Verified:** the items from "Checked and clean" in the review, in plain words.
- **Not verified:** the items from "Not checked", each open period or unmatured trial the numbers leave out, and each Think on it finding the script does not apply yet. Read `analysis.py` to see whether a fix was made. If you cannot tell, list the finding here.
- **Quirks:** how each quirk that applies was handled, one line each.

## Act 5: Write the brief
Write `brief.md` in the run folder. If a brief from an earlier round is there, replace it. Use this shape:

```markdown
# <the question, as a short title>

## Objective
<the question, the decision it informs, and who makes it>

## Key Takeaways
- <a finding, with its number and its comparison>

## Recommendations
1. <what the decider should do>

## Analysis
### <a full sentence stating the takeaway>
![<short description>](charts/<name>.png)

**<Figure or Table> <n>:** <what it shows: the measure, the period, the segments, and the filters>  
Source: `data/<name>.csv`, from `analysis.py`.

## Checks
- **Review:** <verdict> (`review.md`)
- **Verified:** <what was checked and held>
- **Not verified:** <what was not checked, and why>
- **Quirks:** <how each one that applies was handled>
```

Write for the decider named in the frame:
- Use plain words. Column names and code belong only in captions.
- Escape dollar signs as `\$`, so Markdown viewers do not read them as math.
- Use no em dashes.

## Deliver
The brief is the deliverable. On the CLI, show only:
- The path of the brief.
- The review verdict it was written under.
- How many items are listed under "Not verified".

Keep it under five lines. Do not paste the brief into the CLI.

## Principles
- **Answer first.** The reader gets the takeaway before the evidence.
- **Every heading is a sentence.** A chart under "Churn by plan" leaves the reader to find the point.
- **No new numbers.** Every number traces to a result table or to what `analysis.py` prints.
- **Always compare.** Each number in the brief carries its comparison, or says none exists.
- **Write for the decider.** Plain words, the decision in the frame, and nothing they do not need to make it.
- **Say what was not verified.** An open period or an unapplied finding is part of the answer.
- **No brief on Fix first.** A well-written brief about a wrong number does more harm than no brief at all.