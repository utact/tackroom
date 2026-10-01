"""Distribution integrity: docs drift, isolated references, marketplace discovery."""

import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from contextlib import redirect_stdout
from urllib.parse import unquote, urlsplit

from support import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
import sync_references as sync


class PluginDistribution(unittest.TestCase):
    def test_committed_references_match_sources(self):
        self.assertEqual(sync.differences(ROOT, sync.build(ROOT)), [])

    def test_marketplace_discovers_independent_plugins(self):
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        entries = marketplace["plugins"]
        names = [entry["name"] for entry in entries]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {path.parent.parent.name for path in (ROOT / "plugin").glob("*/.claude-plugin/plugin.json")})
        for entry in entries:
            plugin = (ROOT / entry["source"]).resolve()
            self.assertIn(ROOT.resolve(), plugin.parents)
            manifest = json.loads((plugin / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], entry["name"])

    def test_skills_remain_readable_without_repository(self):
        for name in sync.PACKAGES:
            with self.subTest(plugin=name), tempfile.TemporaryDirectory() as directory:
                plugin = Path(directory) / name
                shutil.copytree(ROOT / "plugin" / name, plugin)
                skills = list(plugin.glob("skills/*/SKILL.md"))
                self.assertTrue(skills)
                visited = set()
                pending = list(skills)
                while pending:
                    path = pending.pop().resolve()
                    if path in visited:
                        continue
                    visited.add(path)
                    self.assertIn(plugin.resolve(), path.parents)
                    self.assertTrue(path.is_file(), str(path))
                    content = path.read_text(encoding="utf-8")
                    for target in re.findall(r"\]\(([^)\s]+)\)", content):
                        parts = urlsplit(target)
                        if parts.scheme or parts.netloc or not parts.path:
                            continue
                        pending.append(path.parent / unquote(parts.path))
                # Every Markdown reference must be reachable from a Skill entry point.
                self.assertEqual(visited, {p.resolve() for p in plugin.rglob("*.md")})

    def test_source_hashes_and_preserved_card_bodies(self):
        for directory in sync.PACKAGES.values():
            metadata = json.loads((ROOT / directory / "sources.json").read_text(encoding="utf-8"))
            for target, record in metadata["files"].items():
                source = sync.read(ROOT, Path(record["source"]))
                self.assertEqual(record["sha256"], hashlib.sha256(source.encode("utf-8")).hexdigest())
                if target != "index.md":
                    body = sync.read(ROOT, directory / target).split("\n\n", 1)[1]
                    self.assertEqual(body, source)

    def test_changed_missing_and_stale_outputs_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = sync.PACKAGES["harness"] / "harness-engineering.md"
            expected = {relative: "expected\n"}
            self.assertEqual(sync.differences(root, expected), [("missing", relative)])
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_text("outdated\n", encoding="utf-8")
            stale = relative.parent / "stale.md"
            (root / stale).write_text("obsolete", encoding="utf-8")
            self.assertEqual(sync.differences(root, expected), [("changed", relative), ("unexpected", stale)])
            self.assertEqual(path.read_text(encoding="utf-8"), "outdated\n")

    def test_source_changes_propagate_and_unlisted_cards_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "docs", root / "docs")
            initial = sync.build(root)
            source = root / "docs/stacks/api/locking.md"
            original = source.read_text(encoding="utf-8")
            source.write_text(original + "\nSource revision.\n", encoding="utf-8")
            updated = sync.build(root)
            changed = {path for path in initial if initial[path] != updated[path]}
            self.assertEqual(changed, {
                sync.PACKAGES["techjudge"] / "stacks/api/locking.md",
                sync.PACKAGES["techjudge"] / "sources.json",
            })
            self.assertTrue(source.read_text(encoding="utf-8").endswith("Source revision.\n"))
            source.with_name("unlisted.md").write_text("Unlisted card", encoding="utf-8")
            with self.assertRaises(ValueError):
                sync.build(root)

    def test_sync_check_rejects_broken_links_before_writing(self):
        for link in ("missing.md", "../../../../../../README.md"):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(ROOT / "docs", root / "docs")
                source = root / "docs/stacks/ops/github-actions.md"
                with source.open("a", encoding="utf-8") as stream:
                    stream.write("\n[Broken reference]({})\n".format(link))
                output = io.StringIO()
                with patch.object(sync, "ROOT", root), redirect_stdout(output):
                    self.assertEqual(sync.main(["--check"]), 1)
                    self.assertEqual(sync.main([]), 1)
                self.assertIn("Reference generation failed:", output.getvalue())
                self.assertFalse((root / "plugin").exists())

    def test_source_hash_is_portable_across_line_endings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "docs", root / "docs")
            expected = sync.build(root)
            source = root / "docs/harness-engineering.md"
            source.write_bytes(source.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(sync.build(root), expected)


if __name__ == "__main__":
    unittest.main()
