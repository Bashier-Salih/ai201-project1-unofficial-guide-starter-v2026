"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

# A first block this short, with no sentence-ending punctuation, is a heading
# rather than prose. Every one of the 88 campus_life documents opens with one.
TITLE_MAX_CHARS = 80

# Paragraphs below this merge into their neighbour. The shortest body paragraph
# in campus_life is 36 characters ("Expect 4 hours a week outside class."), and
# a chunk that small carries too little signal to embed usefully on its own.
MIN_BODY_CHARS = 40

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _blocks(text: str) -> list[str]:
    """Paragraphs, blank-line separated, stripped and with empties dropped."""
    return [b.strip() for b in _PARAGRAPH_BREAK.split(text.strip()) if b.strip()]


def _is_title(block: str) -> bool:
    """A short opening block with no terminal punctuation is a heading."""
    return len(block) <= TITLE_MAX_CHARS and not block.rstrip().endswith((".", "!", "?"))


def _merge_short(paragraphs: list[str], floor: int) -> list[str]:
    """
    Fold paragraphs shorter than `floor` into a neighbour.

    Forward by preference, so a stub heads the thought it introduces; the last
    paragraph has nothing ahead of it, so it folds backwards instead. This is
    the guard against the degenerate tail fragment fixed-width windows produce
    — the 2-character chunk the brief points at on advice_threads.
    """
    merged: list[str] = []
    carry = ""
    for para in paragraphs:
        candidate = f"{carry} {para}".strip() if carry else para
        if len(candidate) < floor:
            carry = candidate
            continue
        merged.append(candidate)
        carry = ""
    if carry:
        if merged:
            merged[-1] = f"{merged[-1]} {carry}"
        else:
            merged.append(carry)
    return merged


def _fit(text: str, budget: int) -> list[str]:
    """
    Break `text` to fit `budget`, cutting at sentence ends where possible.

    Nothing in campus_life reaches the budget, so this is a ceiling that does
    not fire on this corpus. It matters for any document whose paragraphs run
    longer, and it guarantees that when a cut does happen it lands between
    sentences rather than mid-word.
    """
    if len(text) <= budget:
        return [text]

    parts: list[str] = []
    current = ""
    for sentence in _SENTENCE_BREAK.split(text):
        candidate = f"{current} {sentence}".strip() if current else sentence
        if current and len(candidate) > budget:
            parts.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        parts.append(current)

    # A single sentence longer than the budget still has to come apart; do it
    # at a word boundary rather than mid-word.
    sized: list[str] = []
    for part in parts:
        while len(part) > budget:
            cut = part.rfind(" ", 0, budget)
            if cut <= 0:
                cut = budget
            sized.append(part[:cut].strip())
            part = part[cut:].strip()
        if part:
            sized.append(part)
    return sized


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    One chunk per paragraph, with the document's title line prepended.

    Why this shape, for this corpus: every campus_life document is a heading
    plus one to four paragraphs (median two), and those paragraphs are
    topically distinct — course format, then workload, then advice; dining wait
    times, then hours and cost. Keeping a whole post as one chunk, which is
    what an 800-character window did, blends those topics into one embedding
    that matches every question about the post a little and none of them well.

    But splitting alone makes things worse, because 26 of the 183 body
    paragraphs name neither their course nor their building: "Expect 4 hours a
    week outside class." is indistinguishable from the seven other workload
    paragraphs shaped exactly like it. Prepending the title line is what makes
    a paragraph-sized chunk safe to retrieve — it is the difference between a
    chunk that answers "how many hours is ECON 101" and one that merely looks
    like it does.

    `config.CHUNK_SIZE` acts as a ceiling here rather than a target, and there
    is no overlap: cuts land on paragraph boundaries, so there is no arbitrary
    split for an overlap window to repair.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        blocks = _blocks(doc.text)
        if not blocks:
            continue

        if len(blocks) > 1 and _is_title(blocks[0]):
            title, body = blocks[0], blocks[1:]
        else:
            title, body = "", blocks

        # Newline rather than a dash: several titles already contain an em-dash
        # ("CS 340 Databases — assessment"), and chaining another onto it reads
        # as one run-on sentence.
        prefix = f"{title}\n" if title else ""
        budget = max(config.CHUNK_SIZE - len(prefix), 1)

        pieces = [
            prefix + part
            for para in _merge_short(body, MIN_BODY_CHARS)
            for part in _fit(para, budget)
        ]
        if not pieces:
            pieces = [title or doc.text.strip()]

        for index, text in enumerate(pieces):
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
