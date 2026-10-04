"""Technology and algorithm cards follow the template in docs/stacks/README.md.

Every card listed in the index exists, every file is listed, and each card has every section in order.
A card that skips a section, such as trade-offs, fails here instead of in review.
"""

import re
import unittest

from support import ROOT, kowrite

STACKS = ROOT / "docs" / "stacks"
ALGORITHMS = ROOT / "docs" / "algorithms"
COLLECTIONS = (STACKS, ALGORITHMS)
SECTIONS = ["요약", "문제 신호", "기준선의 한계", "원리", "가치", "트레이드오프와 리스크", "대안과 경계",
            "깊이 있는 활용", "임시방책의 신호", "실패 재현", "측정과 검증", "재검토 조건", "출처"]


def index(collection=STACKS):
    text = (collection / "README.md").read_text(encoding="utf-8")
    listing = re.search(r"^## 목록\n(.*?)(?=^## |\Z)", text, re.M | re.S).group(1)
    return sorted(re.findall(r"\]\(([\w-]+/[\w-]+\.md)\)", listing)), text


class StackCards(unittest.TestCase):

    def test_template_lists_every_section(self):
        _, text = index()
        template = text.split("## 조사 양식", 1)[1]
        self.assertEqual(re.findall(r"^\| ([^|]+?) \|", template, re.M)[1:], SECTIONS)

    def test_index_matches_files(self):
        for collection in COLLECTIONS:
            with self.subTest(collection=collection.name):
                listed, _ = index(collection)
                files = sorted(p.relative_to(collection).as_posix() for p in collection.rglob("*.md") if p.name != "README.md")
                self.assertEqual(listed, files)

    def test_every_card_has_every_section_in_order(self):
        for collection in COLLECTIONS:
            for name in index(collection)[0]:
                with self.subTest(collection=collection.name, card=name):
                    text = (collection / name).read_text(encoding="utf-8")
                    headings = re.findall(r"^## (.+)$", text, re.M)
                    self.assertEqual(headings, SECTIONS, name)
                    self.assertRegex(text.split("\n", 3)[2], r"^확인: \d{4}-\d{2}-\d{2}", name)
                    for section in re.split(r"^## .+$", text, flags=re.M)[1:]:
                        self.assertTrue(section.strip(), f"{name}: empty section")

    def test_cards_follow_kowrite(self):
        for collection in COLLECTIONS:
            for path in collection.rglob("*.md"):
                self.assertEqual(kowrite.check_wraps(path.name, path.read_text(encoding="utf-8")), [], str(path))


if __name__ == "__main__":
    unittest.main()
