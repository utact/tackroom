"""Shared fixtures: import the hook as a module, run it as a process, and build throwaway git repositories."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "plugin" / "kowrite" / "hooks"
sys.path.insert(0, str(HOOKS))
import kowrite  # noqa: E402


def run(event_name, event, cwd):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    result = subprocess.run([sys.executable, str(HOOKS / "kowrite.py"), event_name], input=json.dumps(event),
                            capture_output=True, text=True, encoding="utf-8", cwd=cwd, env=env, timeout=60)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def feedback(output):
    return (output.get("hookSpecificOutput") or {}).get("additionalContext", "")


def denied(output):
    return (output.get("hookSpecificOutput") or {}).get("permissionDecision") == "deny"


class Repo(unittest.TestCase):
    """A fresh repository per test with one empty commit."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.name", "tester")
        self.git("config", "user.email", "tester@example.com")
        self.git("commit", "-q", "--allow-empty", "-m", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args, cwd=None):
        return subprocess.run(["git", *args], cwd=cwd or self.root, check=True, capture_output=True,
                              text=True, encoding="utf-8").stdout

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def hook(self, event_name, cwd=None, **event):
        event.setdefault("session_id", "s1")
        event.setdefault("cwd", str(cwd or self.root))
        return run(event_name, event, cwd or self.root)

    def edited(self, name):
        return feedback(self.hook("post", tool_name="Write", tool_input={"file_path": name}))

    def bash(self, command, tool_use_id="t1"):
        """Run a command the way Claude Code does: PreToolUse, the command itself, then PostToolUse."""
        pre = self.hook("pre", tool_name="Bash", tool_input={"command": command}, tool_use_id=tool_use_id)
        if denied(pre):
            return pre, {}
        subprocess.run(["bash", "-c", command], cwd=self.root, capture_output=True)
        return pre, self.hook("post", tool_name="Bash", tool_input={"command": command}, tool_use_id=tool_use_id)
