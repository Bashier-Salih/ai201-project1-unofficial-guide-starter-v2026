# The Unofficial Guide

Bashier Salih - I picked the campus life corpus.

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

## Chunking Strategy

**Chunk size:** 450 characters — a ceiling, not a target. Real chunks average 167.
**Overlap:** none.

I split on paragraph breaks and prepend each document's title line to every
chunk. `chunker.py::split_documents`.

**What the starter did first.** `python app.py index` reported:

```
chunked  88 chunks, 317 characters on average (shortest 178, longest 549), produced by chunker.py::fallback_split
```

88 documents, 88 chunks. The starter cuts at 800 characters and my longest
document is 549, so it never split anything — one post was already one chunk.
That also means the starter's `CHUNK_OVERLAP = 120` was dead code on this
corpus: nothing split, so nothing overlapped.

**Why I split anyway.** Every document here is a heading plus one to four
paragraphs — median two, and they cover different things. `course_biol_160.txt`
has one paragraph on lecture format and assessment, one on weekly hours, one on
exam pacing. `dining_halden_hall.txt` has one on wait times and food, one on
hours and price. Keeping all of that in a single embedding gives a vector that
matches every question about BIOL 160 a little and no question well. Splitting
per paragraph gives one topic per chunk. That took 88 chunks to 182.

**Why the title line is prepended — this is the part that matters.** I measured
the paragraphs before writing anything, and 26 of the 183 name neither their
course nor their building:

```
Expect 4 hours a week outside class.              (course_econ_101.txt)
Expect 5 to 6 hours a week outside class.         (course_stat_150.txt)
Expect 8 to 10 hours a week outside class.        (course_cs_210.txt)
The bad: the elevator is out roughly one week per semester.   (housing_aldridge_hall.txt)
```

Split naively, those are unattributable and near-identical to seven siblings
each. My corpus is built from templates — seven laundry files share whole
sentences byte for byte, all eight dining follow-ups say "go before 11:45" — so
a chunk with the building name stripped out is not just less useful, it is
actively confusable with the wrong building. Prepending the heading is what
makes a paragraph-sized chunk safe to retrieve.

It works. `retrieve "What is the dryer cost in Morrow House?"` puts the two
Morrow House chunks at 0.276 and 0.299, with the nearest wrong hall at 0.463 —
a 0.16 gap between right building and wrong building.

**Why no overlap.** Overlap exists to repair a fact severed by an arbitrary
cut. My cuts are paragraph boundaries, which are where the author already
stopped a thought, so there is nothing to repair. The title prefix carries the
context an overlap window would otherwise have to drag along. I left
`CHUNK_OVERLAP = 120` in `config.py` because `fallback_split` still reads it
and I want the original baseline intact for comparison in unit 2.

**What I got wrong on the way.** My first version joined the title to the body
with an em-dash, which produced `CS 340 Databases — assessment — Start the term
project…` on the several documents whose headings already contain a dash. It
read as one run-on sentence. I switched the separator to a newline.

**A cost I accepted.** Splitting makes more chunks compete, and one question got
slightly worse for it: `"What is the exam format for PHYS 130?"` now ranks the
hub document's intro paragraph first (0.328), ahead of the actual assessment
file (0.407). The answer is still in the retrieved set — ranks 2, 3 and 5 all
carry it — but only because `TOP_K = 5`. With `TOP_K = 1` the paragraph split
would have made that question worse than the 800-character baseline did.

## Sample Chunks

All five produced by `chunker.py::split_documents`, printed by
`python app.py chunks -n 5`. The first line of each chunk is the prepended
title line; everything after it is one paragraph of the source document.

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline
You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_cs_340_exams.txt#1` — produced by: `chunker.py::split_documents`

```
CS 340 Databases — assessment
Start the term project in week three, not week eight; everyone learns this the hard way.
```

**Chunk 3** — source: `course_phys_130_workload.txt#1` — produced by: `chunker.py::split_documents`

```
Workload for PHYS 130 Mechanics
It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `health_center.txt#0` — produced by: `chunker.py::split_documents`

```
The health centre
Walk-in hours are 8am to 11am; everything after that is by appointment and appointments run about a week out. If something is urgent, go at 8am and wait rather than booking.
```

**Chunk 5** — source: `housing_morrow_house.txt#2` — produced by: `chunker.py::split_documents`

```
Morrow House — what it's actually like
The bad: known damp problem on the ground floor; two rooms were taken offline in 2024.
```

**Reading them against the test.** Could someone answer a question using only
this, without reading what came before or after? Yes for all five, and chunks 2,
3 and 5 are the ones that prove the design. Their bodies alone — "Start the term
project in week three", "It's front-loaded", "The bad: known damp problem" —
name no course and no building. They would be fragments. The title line is what
makes them answerable.

Chunk 5 also shows the honest limit. It is 86 characters of body, which is short,
and it tells you Morrow House has a damp problem without telling you anything
else about Morrow House. That is the right trade here: a question about damp gets
a clean match instead of a paragraph about damp buried in a paragraph about
laundry, noise and construction dates.

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**

**Answer:**

```
```

**My relevance cutoff:**

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
|  |  |  |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
