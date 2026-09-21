# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** Four of my five questions aim at corpus sections built
from near-identical templates — seven laundry files that share whole sentences
verbatim, eight dining pairs, eight course workload files. A retriever that
grabs the right *topic* but the wrong *building or course* is the live failure
mode here, and I expect it to happen at least once. The fifth question
(printing quota) is a singleton with no near-duplicate competition, so I'd be
surprised to miss that one. Hence 4 of 5, not 5 of 5 — and not 3, because if
two of the near-duplicate questions miss, that's a pattern rather than bad luck
and I'd want it to count as a failure.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** All five, because this isn't a judgment call the model
makes — the source filename rides along as chunk metadata from ingest, so
naming it is plumbing, not inference. If even one answer comes back without a
source, something is broken in how metadata survives the retrieval step, and
that would be broken for all five rather than four. A target of 4 of 5 would
let a real plumbing bug pass.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** Four of the five out-of-scope questions are from
genuinely unrelated domains — Mongolia, diesel engines, the World Cup, Rust —
and nothing in a campus-life corpus should sit near them. The fifth is the
ibuprofen dosage question, and my corpus contains `health_center.txt`, which
covers walk-in hours and counselling intake. That one shares vocabulary with
the corpus even though the corpus can't answer it, so I expect it to be the
closest of the five and the one most likely to get through the gate. 4 of 5
names that specific risk; 5 of 5 would be claiming a clean gap I have reason
to think isn't there.

---

## 4. Chunks are whole documents, never fragments

All 5 sampled chunks are complete documents: each starts with its document's
title line and ends at a sentence boundary, with nothing cut mid-sentence and
no document appearing across two chunks.

**Why this target:** I measured my corpus before setting this. All 88
documents are between 183 and 554 characters, and `CHUNK_SIZE` is 800 — so no
document should ever split, and `CHUNK_OVERLAP = 120` never has anything to
overlap. The count confirms it: 88 documents produce exactly 88 chunks. Given
that, "4 of 5 read as a complete thought" would be too loose — a single
fragment would mean the chunker is splitting something it has no reason to
split, so the honest target is 5 of 5. The criterion is really a check that my
chunk size is doing nothing, which is the correct behaviour for documents this
short, rather than a check that it's splitting well.

---

## 5. Sources are correct, not merely present

For at least 4 of my 5 test questions, the source the answer names is the
document that actually contains the answer — not a near-identical neighbour
from the same template.

**Why this target:** Criterion 2 only asks that *a* source gets named, and my
corpus makes that a weak guarantee. Seven laundry files contain the sentence
"Best time to do laundry here is Tuesday or Wednesday morning" byte for byte;
all eight dining follow-ups say "go before 11:45." A system can cite Aldridge
Hall while answering about Morrow House and look completely correct. I chose
questions whose answers are unique strings — `1.25` appears only in the two
Morrow House files, `12.50` only in Kestrel Commons — precisely so that a
wrong-neighbour citation is detectable rather than invisible. 4 of 5 rather
than 5 of 5 for the same reason as criterion 1: four of these questions sit in
near-duplicate territory and I expect one to go wrong. This is the criterion I
care most about, because it's the failure that would be easiest to miss if I
weren't checking for it.



---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
