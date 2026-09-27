"""Observed failures, kept verbatim.

Each case is the exact input that exposed a defect, with the date and what was observed.
Do not generalize these cases; add a new one each time a defect is found.
"""

import json
import subprocess
import unittest

from support import HOOKS, ROOT, Repo, denied, feedback, kowrite


class Regressions(Repo):

    def test_2026_09_27_readme_example_marker_read_as_marker(self):
        """Editing README reported `README.md:13 [const-marker] const 마커 바로 뒤에 숫자가 없다`."""
        self.write("README.md", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(self.edited("README.md"), "")
        self.write("x.md", "| 문서의 수치는 `<!-- const: 경로:상수 -->숫자`로 코드 상수와 묶는다. | 세션 시작 |\n")
        self.assertEqual(self.edited("x.md"), "")

    def test_2026_09_27_hangul_file_name_skipped_by_stop(self):
        """Stop caught a.md but not 한글문서.md: git printed the path as "\\355\\225..."."""
        self.hook("session")
        self.write("한글문서.md", "# 제목\n\n이 문장은 길어서 중간에서\n줄을 바꿨다.\n")
        self.write("a.md", "이 문장은 길어서 중간에서\n줄을 바꿨다.\n")
        reason = self.hook("stop").get("reason", "")
        self.assertIn("a.md:1", reason)
        self.assertIn("한글문서.md:3", reason)

    def test_2026_09_27_hangul_file_name_tracked(self):
        """The same quoting hid a tracked Hangul file that the session modified."""
        self.write("문서/설명.md", "설명이다.\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "doc")
        self.hook("session")
        self.write("문서/설명.md", "설명을 고쳤는데 중간에서\n줄을 바꿨다.\n")
        self.assertIn("문서/설명.md:1", self.hook("stop").get("reason", ""))

    def test_2026_09_27_human_co_author_denied(self):
        """A human co-author was denied as a tool mark."""
        pre = self.hook("pre", tool_input={"command": 'git commit -m "feat: 추가" -m "Co-authored-by: Kim <kim@example.com>"'})
        self.assertFalse(denied(pre))

    def test_2026_09_27_session_link_in_commit(self):
        """The rule exists for this: a session link and a tool co-author were written into a commit."""
        message = ("feat: 올바른 개행 처리\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                   "Claude-Session: https://claude.ai/code/session_012BhqD7n2C1xUuARipFF1Fq")
        found = kowrite.check_commit(message)
        self.assertEqual([f["line"] for f in found], [3, 4])

    def test_2026_09_27_non_commit_command_asked_to_amend_user_commit(self):
        """`git log --grep commit` made PostToolUse tell the agent to amend the user's older commit."""
        self.git("commit", "-q", "--allow-empty", "-m", "old: 사용자 커밋\nCo-authored-by: Kim <k@x>")
        pre, post = self.bash("git log --grep commit")
        self.assertEqual(feedback(post), "")

    def test_2026_09_27_failed_commit_rechecked_previous_commit(self):
        """A commit that failed (nothing to commit) left HEAD alone but was still checked as "just made"."""
        self.git("commit", "-q", "--allow-empty", "-m", "old\n\nClaude-Session: https://claude.ai/code/session_x")
        pre, post = self.bash("git commit -m 'fix: 변경 없음'")
        self.assertEqual(feedback(post), "")

    def test_2026_09_27_list_item_wrap_missed(self):
        """A wrap inside a list item was not detected."""
        self.write("b.md", "- 목록 항목은 길어서 중간에서\n  줄을 바꿨다.\n")
        self.assertIn("b.md:1 [ko-wrap]", self.edited("b.md"))

    def test_2026_09_27_noun_line_in_markdown(self):
        """Reported as a false positive, but Markdown renders it "성능 평가 결과를 정리했다.": a real wrap."""
        self.write("c.md", "성능 평가\n결과를 정리했다.\n")
        self.assertIn("c.md:1 [ko-wrap]", self.edited("c.md"))

    def test_2026_09_27_noun_style_comment_flagged(self):
        """The same noun line is a false positive in comments, which keep their line breaks."""
        self.write("c.py", "# 성능 평가\n# 결과를 정리한다.\nx = 1\n")
        self.assertEqual(self.edited("c.py"), "")

    def test_2026_09_27_stop_blocked_every_turn(self):
        """README claimed one block per session; stop_hook_active resets each turn, so it blocked every turn."""
        self.hook("session")
        self.write("a.md", "이 문장은 길어서 중간에서\n줄을 바꿨다.\n")
        self.assertEqual(self.hook("stop").get("decision"), "block")
        self.assertEqual(self.hook("stop", stop_hook_active=True), {})
        self.assertEqual(self.hook("stop"), {}, "next turn, same finding")
        self.write("b.md", "새 문서도 길어서 중간에서\n줄을 바꿨다.\n")
        self.assertIn("b.md:1", self.hook("stop").get("reason", ""), "a new finding still blocks")

    def test_2026_09_27_user_changes_before_session_blamed(self):
        """Stop diffed against HEAD, so the user's uncommitted edits made before the session were blamed."""
        self.write("user.md", "사용자가 세션 전에 쓰던\n문서다.\n")
        self.git("add", "user.md")
        self.git("commit", "-q", "-m", "user")
        self.write("user.md", "사용자가 세션 전에 고치던\n문서다.\n")
        self.write("draft.md", "추적하지 않는 초안도\n있다.\n")
        self.hook("session")
        self.assertEqual(self.hook("stop"), {})
        self.write("draft.md", "세션에서 초안을 고쳤고\n줄을 바꿨다.\n")
        self.assertIn("draft.md:1", self.hook("stop").get("reason", ""))

    def test_2026_09_27_project_in_subdirectory(self):
        """With the project in a subdirectory, git paths were repository-relative and never matched."""
        sub = self.root / "app"
        self.write("app/a.md", "하위 폴더 문서다.\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "app")
        self.hook("session", cwd=sub)
        self.write("app/a.md", "하위 폴더 문서도 길어서\n줄을 바꿨다.\n")
        self.assertIn("a.md:1", self.hook("stop", cwd=sub).get("reason", ""))

    def test_2026_09_27_tilde_fence_closed_by_backticks(self):
        """A ~~~ fence toggled on ```, so prose after the block was read as code and vice versa."""
        self.write("f.md", "~~~\n```\n~~~\n문장이 코드 뒤에서\n줄을 바꿨다.\n")
        self.assertIn("f.md:4 [ko-wrap]", self.edited("f.md"))

    def test_2026_09_27_hooks_call_python_by_one_name(self):
        """hooks.json ran `python`, which many macOS and Linux systems do not have."""
        config = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))
        commands = [h["command"] for groups in config["hooks"].values() for group in groups for h in group["hooks"]]
        self.assertTrue(all(c.startswith('bash "${CLAUDE_PLUGIN_ROOT}/hooks/run" ') for c in commands), commands)
        result = subprocess.run(["bash", str(HOOKS / "run"), "session"], input="{}", capture_output=True,
                                text=True, encoding="utf-8")
        self.assertIn("[kowrite]", result.stdout)


if __name__ == "__main__":
    unittest.main()
