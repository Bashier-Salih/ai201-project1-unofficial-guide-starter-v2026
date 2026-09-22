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

This is a question-answering system over the `campus_life` corpus: 88 short
student-written posts about one university's dining halls, residences, courses
and administrative deadlines — the things people find out from each other
rather than from an official page. You ask it a specific question and it
answers from those posts, naming the file it used, so you can go and check.

It handles questions with a definite answer somewhere in the documents: what a
dryer costs in Morrow House, how many hours a week BIOL 160 takes outside
class, what the printing quota is, when the add/drop window closes. It does not
handle questions of taste ("which dining hall is best"), and it is built to
refuse rather than improvise when the documents don't cover something — ask it
the capital of Mongolia, or about a course that doesn't exist here, and it says
it doesn't have enough information instead of guessing.

The hard part of this particular corpus is that it is written from templates.
Seven residence laundry posts share whole sentences byte for byte, eight dining
halls are described in the same shape, and each of eight courses has a matching
workload and exam post. So the real problem is not finding text about laundry —
it is coming back with the right *building's* laundry. Most of the design
decisions below exist for that reason.

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

**A cost I expected and didn't get.** Splitting makes more chunks compete for
the same question, so I went looking for one that got worse.
`"What is the exam format for PHYS 130?"` looked like the casualty — it ranks a
chunk from the hub document first (0.328) rather than the dedicated assessment
file (0.407). But reading the chunk rather than its filename, rank 1 is
`Assessment: three midterms, no final, plus a lab practical. Not curved, but the
lowest midterm is dropped.` That is a better answer to the question than the
assessment file's own top chunk, which only covers the practical's weighting.
Ranking by source file would have called this a regression; ranking by content
says the split got it right. All five test questions retrieve a chunk
containing their `expects` string at rank 1.

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

**Question:** What is the dryer cost in Morrow House?

**Answer:**

```
$ python app.py ask "What is the dryer cost in Morrow House?"

  (best distance 0.276, cutoff 0.5)

The dryer cost in Morrow House is $1.25.

Source: housing_morrow_house.txt (also found in housing_morrow_house_laundry.txt)

Sources retrieved: housing_aldridge_hall_laundry.txt, housing_innisfree_hall_laundry.txt,
housing_morrow_house.txt, housing_morrow_house_laundry.txt, housing_old_brewhouse_laundry.txt
```

The "sources retrieved" line is the part worth looking at. Three of the five
chunks sent to the model were the wrong building, carrying $1.50, $1.50 and
$1.75 as dryer prices. The answer picked $1.25 and named a Morrow House file.

### Is the grounding instruction strict enough?

`GROUNDING_INSTRUCTION` in `generate.py` already says: use only the documents
provided, admit when they don't cover it, name the file. The question is
whether that survives a corpus where seven laundry files share sentences byte
for byte. I wrote six probes designed to break it rather than to pass:

| Probe | Trap | Result |
|---|---|---|
| Dryer cost in Morrow House | 3 wrong halls with 3 other prices in context | correct |
| Dryer cost in Tamsin Court | Tamsin is in-unit; no price exists, siblings have one | refused to invent |
| Air conditioning in Morrow House | Morrow never mentions it; Innisfree's "no air conditioning" is in context | refused |
| Wash price in Old Brewhouse | $1.50 is also Morrow's price | cited Old Brewhouse |
| Cheaper: Morrow or Innisfree | invites blending two halls | both correct |
| Best laundry time in Fenwick Court | sentence is byte-identical in 7 files | cited Fenwick |

No drift. The instruction is strict enough, and I'm recording that as a tested
finding rather than an assumption — the interesting result was that the model
refused twice when refusing was harder than answering.

**Two rules I added anyway.** The air-conditioning probe exposed a small defect:
the model refused correctly but still printed `(housing_morrow_house.txt)`,
citing a source for an answer it had not given. So:

```
- Several documents here describe different buildings, halls or courses in
  near-identical wording. Only answer from a document that names the specific
  one the question asks about. A matching sentence about a different building
  or course is not an answer to this question.
- When you don't have enough information, say so without naming a file. There
  is no source to cite for an answer you did not give.
```

The second fixes the observed defect. The first is preventive — no probe
triggered a wrong-building answer, but the whole corpus is built from
templates, so it's the failure most likely to appear on a question I didn't
think to try. I re-ran all six probes after the change; all still pass, and the
air-conditioning refusal now names no file.

**My relevance cutoff:** `THRESHOLD = 0.50`, down from the shipped 0.6.

**Top-k:** left at 5. All five test questions retrieve a chunk containing their
`expects` string at rank 1, so raising it would only add noise; lowering it to 1
would still pass, but with no margin for a question phrased less precisely.

**The ten required rows.** Five questions my corpus covers, five from
`OUT_OF_SCOPE`:

| Question | In corpus? | Best distance |
|---|---|---|
| How many hours a week outside class does BIOL 160 take? | yes | 0.2650 |
| How many pages of printing does each student get per semester? | yes | 0.2699 |
| What is the dryer cost in Morrow House? | yes | 0.2755 |
| What is the exam format for PHYS 130? | yes | 0.3279 |
| How much does a meal cost in cash at Kestrel Commons? | yes | 0.3333 |
| What is the capital of Mongolia? | no | 0.7873 |
| Who won the 1994 World Cup? | no | 0.8474 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8487 |
| How do I write a for loop in Rust? | no | 0.8598 |
| How do I change the oil in a diesel engine? | no | 0.9228 |

Two tight groups, 0.265–0.333 and 0.787–0.923, with a 0.454-wide gap between
them. By that table alone almost any cutoff from 0.4 to 0.75 works, and I nearly
stopped there.

**Why I didn't trust that gap.** The five out-of-scope questions are about
Mongolia, the World Cup, ibuprofen, Rust and diesel engines. Nothing in a
campus-life corpus is near any of them, so the gap measures the distance between
my corpus and *unrelated subjects* — not between questions it answers and
questions it doesn't. The cutoff's real job is the second one. So I wrote
sixteen more questions in campus vocabulary, half genuinely covered and half
not, and the picture changed:

| Distance | Covered? | Question |
|---|---|---|
| 0.1734 | yes | Is Morrow House laundry expensive? |
| 0.3041 | yes | What time does the library close? |
| 0.3789 | yes | Is BIOL 160 a lot of work? |
| 0.4447 | yes | Which dining hall should I avoid at lunch? |
| 0.4724 | yes | Is there air conditioning in the dorms? |
| **0.4955** | **no** | What are the gym opening hours? |
| 0.5258 | yes | What happens if I withdraw from a course? |
| 0.5271 | yes | Can I drop a class after the midterm? |
| **0.5303** | **no** | Does CHEM 101 have a lab? |
| 0.5368 | yes | How do I print something on campus? |
| **0.5478** | **no** | Which dorm has the best wifi? |
| **0.5538** | **no** | How much does a parking permit cost? |
| **0.5845** | **no** | What is the tuition for out-of-state students? |
| 0.5911 | yes | Where should I eat late at night? |
| **0.6021** | **no** | Is there a shuttle to the airport? |
| **0.6575** | **no** | How do I appeal a parking ticket? |

**There is no clean gap.** Covered and uncovered questions interleave from
0.4955 to 0.5911. Every cutoff in that band is a trade, not a discovery:

| Cutoff | Refuses covered questions | Accepts uncovered ones |
|---|---|---|
| 0.45 | 5 | 0 |
| **0.50** | **4** | **1** |
| 0.55 | 1 | 3 |
| 0.60 (shipped) | 0 | 5 |

**Why 0.50.** The shipped 0.6 lets through five questions the corpus cannot
answer, and the worst of them is `Does CHEM 101 have a lab?` at 0.5303 — CHEM
101 does not exist in my corpus, and the nearest chunk is CS 210's assessment
file. That hands the model material about a different course and asks it a
confident question. Getting a plausible answer about the wrong course is exactly
the failure that is hard to notice afterwards, which is the reason for having a
gate in code rather than asking the model to be careful.

0.50 costs four refusals of questions I do cover, and I looked at each one
rather than counting them. `Where should I eat late at night?` (0.5911) retrieved
Halden Hall, which closes at 7:00pm — retrieval had already failed there, so
refusing is the better outcome. `How do I print something on campus?` (0.5368)
is only half-covered: the corpus gives the quota, not the procedure. The two
real losses are `Can I drop a class after the midterm?` (0.5271) and `What
happens if I withdraw from a course?` (0.5258), both of which have a document
that answers them directly. I am accepting those two refusals to keep CHEM 101
out.

Against the graded criteria the margin is comfortable either way: all five test
questions sit 0.17 below the cutoff, and all five `OUT_OF_SCOPE` questions sit
0.29 above it.

## How I Used AI

I used Claude throughout this project, including to write code and draft parts
of this README. Two moments where what came back changed what I did:

**1. It killed a test question I thought was good.** I had written "What is the
best time to do laundry in Morrow House?" as one of my five — it names a
building, names an attribute, and the answer is right there in
`housing_morrow_house_laundry.txt`. I asked Claude whether it was a good
question. Instead of answering, it grepped the corpus and came back with the
seven laundry files side by side: every one of them contains the sentence "Best
time to do laundry here is Tuesday or Wednesday morning" byte for byte. The
question would return "Tuesday or Wednesday morning" and pass my `expects`
check even if retrieval had fetched Aldridge Hall. It could not fail, so it
measured nothing. I replaced it with dryer cost, where `1.25` appears in
exactly two files and both are Morrow House. That check — *what would a wrong
retrieval produce?* — is what I applied to the other four questions, and it's
also where criterion 5 came from.

**2. It gave me a confident wrong claim, and I committed it before catching
it.** After I replaced the chunker, Claude reported that the PHYS 130 question
had regressed: rank 1 now came from `course_phys_130.txt` rather than the
dedicated `course_phys_130_exams.txt`, which looked like the paragraph split
burying the right document. It wrote that into the README as a cost I'd
accepted, with the specific claim that at `TOP_K = 1` the question would have
been worse than the 800-character baseline. That got committed. It was wrong.
Reading the chunk instead of its filename, rank 1 is `Assessment: three
midterms, no final, plus a lab practical. Not curved, but the lowest midterm is
dropped.` — the full answer, and a better one than the assessment file's own
top chunk, which only covers the practical's weighting. The whole claim came
from ranking sources by filename rather than reading what was in them. I
reversed the commit and rewrote the section.

The second one is the lesson I'd keep. The error was plausible, specific,
internally consistent, and cited real distances — 0.328 and 0.407, both
accurate. Nothing about it looked like a guess. It was only wrong about the one
thing neither of the numbers showed, which was what the chunk actually said.
That is the same failure mode this whole project is built to defend against:
`GROUNDING_INSTRUCTION` exists because a model will name a source and still not
be telling you what that source says. I got a live demonstration of it in my
own README.

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
