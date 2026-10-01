"""State kept under the git directory: it must stay bounded and never appear in the work tree."""

import os
import time

from support import Repo, kowrite


class State(Repo):

    def test_log_rotates(self):
        folder = kowrite.state_dir(self.root)
        folder.mkdir(parents=True)
        (folder / "events.jsonl").write_text("x" * (kowrite.MAX_LOG_BYTES + 1), encoding="utf-8")
        kowrite.log(self.root, {"action": "test"})
        self.assertEqual((folder / "events.1.jsonl").stat().st_size, kowrite.MAX_LOG_BYTES + 1)
        self.assertLess((folder / "events.jsonl").stat().st_size, 200)

    def test_old_session_state_is_pruned(self):
        folder = kowrite.state_dir(self.root)
        folder.mkdir(parents=True)
        old, recent = folder / "base-old.json", folder / "base-recent.json"
        for path in (old, recent):
            path.write_text("{}", encoding="utf-8")
        stale = time.time() - (kowrite.STATE_DAYS + 1) * 86400
        os.utime(old, (stale, stale))
        self.hook("session")
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())

    def test_work_tree_stays_clean(self):
        self.hook("session")
        self.bash("git commit --allow-empty -m 'chore: 빈 커밋'")
        self.hook("stop")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_outside_a_repository_nothing_is_written(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.root / ".git").rename(self.root / "git-moved")
        self.hook("session", cwd=outside)
        self.hook("pre", cwd=outside, tool_input={"command": "git commit -m 'x'"})
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["git-moved", "outside"])
        self.assertEqual(list(outside.iterdir()), [])
