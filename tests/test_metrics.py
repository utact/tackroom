"""Metrics on corpora, not on hand-picked cases.

False positive rate: findings on text written correctly (the repository's own documents, tests/corpus/comments.txt).
Recall: the same sentences broken at every word boundary; each break is a wrap by construction.
Markdown joins lines, so its recall must be 1.0. Comments are checked conservatively, so their recall has a floor.
Raise a floor when the hook improves; never lower it to make a change pass.
"""

import re
import sys
import unittest

from support import ROOT, kowrite

COMMENT_RECALL_FLOOR = 0.66  # measured 69/103 on 2026-09-27
DOCS = [ROOT / "README.md", ROOT / "docs" / "harness-engineering.md"]


def comment_blocks():
    text = (ROOT / "tests" / "corpus" / "comments.txt").read_text(encoding="utf-8")
    blocks = [block.splitlines() for block in text.split("\n\n")]
    return [[line for line in block if not line.startswith("# ")] for block in blocks]


def sentences(lines):
    """Sentences from prose lines; a line may hold several."""
    found = []
    for line in lines:
        if re.match(r"^\s*([-*+|#>`<]|\d+\.|\[)", line):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line.strip()):
            if len(sentence.split()) > 1 and kowrite.HANGUL.search(sentence) and sentence[-1] in ".!?다":
                found.append(sentence)
    return found


def breaks(sentence):
    """Every split of a sentence at a word boundary, as (left, right)."""
    words = sentence.split()
    return [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]


def category(left):
    word = left.split()[-1]
    if word.endswith(","):
        return "comma"
    return "open ending" if word[-1] in kowrite.OPEN_ENDINGS or word.endswith(kowrite.OPEN_SUFFIXES) else "other"


class Metrics(unittest.TestCase):

    def report(self, name, hits, total):
        rate = hits / total if total else 1.0
        print(f"\n  {name}: {hits}/{total} = {rate:.3f}", file=sys.stderr, end="")
        return rate

    def test_false_positive_rate_on_clean_text(self):
        findings, lines = [], 0
        for doc in DOCS:
            text = doc.read_text(encoding="utf-8")
            lines += len(text.splitlines())
            findings += kowrite.check_wraps(doc.name, text)
        for block in comment_blocks():
            text = "\n".join("# " + line for line in block) + "\n"
            lines += len(block)
            findings += kowrite.check_wraps("c.py", text)
        self.report("false positives per line", len(findings), lines)
        self.assertEqual(findings, [])

    def test_markdown_recall(self):
        cases = [(s, l, r) for doc in DOCS for s in sentences(doc.read_text(encoding="utf-8").splitlines())
                 for l, r in breaks(s)]
        missed = [(l, r) for _, l, r in cases if not kowrite.check_wraps("x.md", f"{l}\n{r}\n")]
        self.report("markdown recall", len(cases) - len(missed), len(cases))
        self.assertGreater(len(cases), 50)
        self.assertEqual(missed, [])

    def test_comment_recall(self):
        by_category = {}
        for block in comment_blocks():
            for sentence in sentences(block):
                for left, right in breaks(sentence):
                    hit = bool(kowrite.check_wraps("c.py", f"# {left}\n# {right}\n"))
                    by_category.setdefault(category(left), []).append(hit)
        total = [hit for hits in by_category.values() for hit in hits]
        rates = {name: self.report(f"comment recall, break after {name}", sum(hits), len(hits))
                 for name, hits in sorted(by_category.items())}
        overall = self.report("comment recall", sum(total), len(total))
        self.assertGreaterEqual(overall, COMMENT_RECALL_FLOOR)
        self.assertGreaterEqual(rates.get("open ending", 1.0), 0.9)


if __name__ == "__main__":
    unittest.main()
