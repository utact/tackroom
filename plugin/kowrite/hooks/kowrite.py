"""Korean writing rules for Claude Code. Standard library only; no model calls.

The session guide explains the rules; hooks report violations and block selected actions.
Heuristic detection, hook reentry and fail-open errors limit enforcement.

Events:
  session  SessionStart  adds the guide; snapshots the work tree so Stop sees only what the session changed
  pre      PreToolUse    blocks `git commit` whose message has a tool mark or a mid-sentence wrap
  post     PostToolUse   checks an edited document or comment file; rechecks a commit the command created
  stop     Stop          checks every change since the session started; blocks once per finding

Markers, written in Markdown outside code:
  <!-- const: path:NAME -->123   the number right after the marker must equal the constant NAME in path
  <!-- tracks: path -->          report when path changed but this document did not
"""

import ast
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HANGUL = re.compile(r"[가-힣]")
DOC_SUFFIXES = {".md", ".markdown"}
COMMENT_PREFIX = {".py": ("#",), ".sh": ("#",), ".yml": ("#",), ".yaml": ("#",),
                  ".js": ("//", "*", "/*"), ".ts": ("//", "*", "/*"), ".java": ("//", "*", "/*"),
                  ".kt": ("//", "*", "/*"), ".go": ("//",), ".rs": ("//",), ".c": ("//", "*", "/*")}
SKIP_DIRS = {".git", "node_modules", "build", "dist", "vendor", "__pycache__", ".venv"}

# Tool and model marks. A human co-author is not a tool mark.
TOOLS = ("claude", "anthropic", "openai", "chatgpt", "codex", "copilot", "cursor", "gemini", "devin", "aider")
TOOL_MARKS = {
    "session-link": re.compile(r"claude\.ai/code|chatgpt\.com/codex", re.I),
    "session-trailer": re.compile(r"^\s*(?:" + "|".join(TOOLS) + r")[\w-]*-session:", re.I),
    "generated": re.compile(r"generated (?:with|by)\b.*\b(?:" + "|".join(TOOLS) + r")\b", re.I),
    "robot": re.compile("\N{ROBOT FACE}"),
    "tool-coauthor": re.compile(r"^\s*co-authored-by:.*\b(?:" + "|".join(TOOLS) + r")\b", re.I),
}

# Markdown joins consecutive lines into one paragraph, so a paragraph line must end its sentence.
SENTENCE_END = set(".!?:;…。") | set("다요까죠음함임됨")
CLOSERS = ")]\"'”’」』*_~`"
NOT_ENDS = ("마다", "보다", "에다", "다음", "처음", "마음")  # words and particles that resemble predicate endings
# Comments and commit messages keep their line breaks, and noun-final style ("만료 파일 삭제") is normal there.
# Only a comma or a particle/connective ending that cannot be a noun marks an open sentence.
OPEN_ENDINGS = set("고며면서는을를의에와과로가은도만한된할될게지데니여해이및")
OPEN_SUFFIXES = ("도록", "거나")  # the last syllable alone collides with nouns (기록, 목록)
# Particles that attach only to a syllable without a final consonant.
# 는 is not here: the verb ending 는 follows any stem (있는, 않는).
AFTER_OPEN_SYLLABLE = set("가를와")
AFTER_CLOSED_SYLLABLE = set("이은을과")  # attach only to a syllable with a final consonant
# Nouns whose last syllable collides with an ending and survives the final-consonant test.
NOUNS = frozenset("""추가 대가 참고 경고 최고 광고 창고 재고 문서 순서 화면 측면 이면 표면 전면
메시지 이미지 페이지 여지 유지 방지 금지 이해 피해 방해 제한 권한 기한 무한
속도 한도 정도 제도 온도 빈도 밀도 용도 의도 정의 회의 논의 주의 합의 문의 길이 높이 결과""".split())

LIST_ITEM = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
GUIDE = """[kowrite]
- 문장은 짧게 쓰되, 자연스러운 문단은 이어 써라. 줄을 바꿀 때는 문장 중간을 끊지 마라.
- 커밋 제목은 영어 유형과 선택적인 영어 스코프 뒤에 한국어 요약을 써라(`type(scope): 요약`). 본문은 빈 줄 뒤의 `- ` 목록으로 쓰고, 문장 또는 명사로 끝내라. 도구·모델 표기와 세션 링크를 넣지 마라.
- 문서에 코드 상수 값을 적으면 값 앞에 `<!-- const: 경로:상수명 -->`을 붙여라.
- 코드를 설명하는 문서에는 `<!-- tracks: 경로 -->`를 적어라.
- 사용자나 저장소에서만 통하는 표현은 통용 용어로 바꿔 쓰고, 마땅한 용어가 없으면 처음 쓰는 곳에 정의부터 적어라."""
MAX_BYTES = 256_000
MAX_LOG_BYTES = 1_000_000
MAX_UNTRACKED = 2_000
STATE_DAYS = 30


# ---------------------------------------------------------------- utilities

def git(root, *args, stdin=None):
    try:
        result = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, input=stdin,
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def read(path):
    try:
        return None if path.stat().st_size > MAX_BYTES else path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None


def state_dir(root):
    # Inside the git directory: never committed, never shown as untracked. None outside a repository.
    folder = git(root, "rev-parse", "--absolute-git-dir")
    return Path(folder.strip(), "kowrite") if folder else None


def state_file(root, kind, key):
    folder = state_dir(root)
    return folder / f"{kind}-{re.sub(r'[^0-9A-Za-z_-]', '', str(key or 'none'))}.json" if folder else None


def load(path, default):
    if path is None:
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save(path, data):
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def log(root, record):
    folder = state_dir(root)
    if folder is None:
        return
    try:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "events.jsonl"
        if target.exists() and target.stat().st_size > MAX_LOG_BYTES:
            target.replace(folder / "events.1.jsonl")
        record["ts"] = dt.datetime.now(dt.timezone.utc).isoformat()
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def finding(path, line, code, message, excerpt=""):
    return {"path": path, "line": line, "code": code, "message": message, "excerpt": excerpt}


def render(findings, limit=25):
    lines = [f"- {f['path']}:{f['line']} [{f['code']}] {f['message']}" for f in findings[:limit]]
    if len(findings) > limit:
        lines.append(f"- 외 {len(findings) - limit}건")
    return "\n".join(lines)


# ---------------------------------------------------------------- line wraps

def has_final_consonant(syllable):
    return (ord(syllable) - 0xAC00) % 28 != 0


def ends_sentence(text, following=""):
    """Markdown: does the line end its sentence? English-only paragraphs are not judged."""
    stripped = text.rstrip().rstrip(CLOSERS)
    if not (HANGUL.search(text) or HANGUL.search(following)) or not stripped:
        return True
    return stripped[-1] in SENTENCE_END and not stripped.endswith(NOT_ENDS)


def open_ending(text, following=""):
    """Comments and commits: does the line clearly stop in the middle of a sentence?"""
    stripped = text.rstrip()
    if not HANGUL.search(stripped):
        return False
    if stripped.endswith(","):
        return True
    word = stripped.split()[-1]
    if word.endswith(OPEN_SUFFIXES):
        return True
    last = word[-1]
    if last not in OPEN_ENDINGS or word in NOUNS:
        return False
    before = word[-2] if len(word) > 1 and HANGUL.match(word[-2]) else None
    if before is None:
        return True  # after Latin, digits or brackets (API가, 값(x)을), or a lone determiner (이)
    if last in AFTER_OPEN_SYLLABLE:
        return not has_final_consonant(before)
    if last in AFTER_CLOSED_SYLLABLE:
        return has_final_consonant(before)
    if last == "로":
        return not has_final_consonant(before) or (ord(before) - 0xAC00) % 28 == 8
    return True


def item(content):
    """Split a list marker off. Returns (text, starts_block)."""
    marker = LIST_ITEM.match(content)
    return (content[marker.end():], True) if marker else (content, False)


def markdown_rows(text):
    """Yield (line number, prose or None, starts a block, hard break) for Markdown."""
    lines = text.splitlines()
    fence, in_list, front, prev_blank = None, False, bool(lines) and lines[0].strip() == "---", True
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if front:
            front = number == 1 or stripped not in ("---", "...")
            yield number, None, True, False
            continue
        opener = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            if opener and opener.group(1)[0] == fence[0] and len(opener.group(1)) >= len(fence):
                fence = None
            yield number, None, True, False
            continue
        if opener:
            fence = opener.group(1)
            yield number, None, True, False
            continue
        if not stripped:
            prev_blank = True
            yield number, None, True, False
            continue
        indented = line.startswith(("    ", "\t"))
        if indented and prev_blank and not in_list:
            yield number, None, True, False  # indented code block
            continue
        if not indented and prev_blank:
            in_list = False
        prev_blank = False
        content = re.sub(r"^(?:>\s?)+", "", stripped)
        if (not content or re.match(r"^(#{1,6}\s|\||<|\[[^\]]+\]:|([-*_=])(\s*\2){2,}\s*$)", content)):
            yield number, None, True, False
            continue
        content, starts = item(content)
        in_list = in_list or starts
        yield number, content, starts, line.endswith(("  ", "\\"))


def comment_rows(path, text):
    """Yield (line number, prose or None, starts a block, hard break) for code comments and docstrings."""
    suffix = Path(path).suffix.lower()
    prefixes = COMMENT_PREFIX[suffix]
    docstrings = set()
    if suffix == ".py":
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            tree = None
        for node in ast.walk(tree) if tree else ():
            body = getattr(node, "body", None)
            if (isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and body
                    and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                docstrings.update(range(body[0].lineno, body[0].end_lineno + 1))
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if number in docstrings:
            content = re.sub(r'^[rRuUbB]*("""|\'\'\')|("""|\'\'\')$', "", stripped).strip()
            if content.startswith((">>>", "...")):
                content = ""
        else:
            marker = None if stripped.startswith("#!") else next((p for p in prefixes if stripped.startswith(p)), None)
            content = stripped[len(marker):].strip() if marker else None
        if not content:
            yield number, None, True, False
            continue
        content, starts = item(content)
        yield number, content, starts, False


def wraps(rows, is_open):
    rows = list(rows)
    for (number, text, _, hard), (_, following, starts, _) in zip(rows, rows[1:]):
        if text and following and not starts and not hard and is_open(text, following):
            yield number, text


def check_wraps(path, text):
    suffix = Path(path).suffix.lower()
    if suffix in DOC_SUFFIXES:
        found = wraps(markdown_rows(text), lambda line, following: not ends_sentence(line, following))
    elif suffix in COMMENT_PREFIX:
        found = wraps(comment_rows(path, text), open_ending)
    else:
        return []
    return [finding(path, number, "ko-wrap", "문장 중간에서 줄을 바꿨다. 줄바꿈을 없애거나 문장이 끝난 뒤에 바꿔라.", line.strip())
            for number, line in found]


# ---------------------------------------------------------------- markers

def without_code(text):
    """Blank out fenced blocks and inline code, keeping offsets, so examples are not read as markers."""
    lines, fence = [], None
    for line in text.split("\n"):
        opener = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence or opener:
            if fence and opener and opener.group(1)[0] == fence[0] and len(opener.group(1)) >= len(fence):
                fence = None
            elif not fence:
                fence = opener.group(1)
            lines.append(" " * len(line))
        else:
            lines.append(re.sub(r"(`+)(.+?)\1", lambda m: " " * len(m.group(0)), line))
    return "\n".join(lines)


CONST_MARKER = re.compile(r"<!--\s*const:\s*([^\s:]+):(\w+)\s*-->\s*([+-]?\d[\d_,]*(?:\.\d+)?)?")
TRACKS_MARKER = re.compile(r"<!--\s*tracks:\s*([^\s>]+)\s*-->")


def constant_value(root, source, symbol):
    text = read(Path(root, source))
    if text is None:
        return None, f"{source}를 읽을 수 없다."
    if source.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return None, f"{source}를 파싱할 수 없다."
        values = [node.value for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
                  and any(isinstance(t, ast.Name) and t.id == symbol
                          for t in (node.targets if isinstance(node, ast.Assign) else [node.target]))]
        if len(values) != 1:
            return None, f"{source}에서 {symbol}의 정의를 하나로 특정할 수 없다."
        try:
            value = ast.literal_eval(values[0])
        except ValueError:
            return None, f"{symbol}이 리터럴이 아니다."
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, f"{symbol}이 숫자가 아니다."
        return value, None
    matches = re.findall(rf"\b{re.escape(symbol)}\b\s*(?::[^=\n]+)?=\s*([+-]?[\d_]+(?:\.\d+)?)", text)
    if len(matches) != 1:
        return None, f"{source}에서 {symbol}의 정의를 하나로 특정할 수 없다."
    return float(matches[0].replace("_", "")), None


def check_const_markers(root, path, text):
    found = []
    for match in CONST_MARKER.finditer(without_code(text)):
        number = text.count("\n", 0, match.start()) + 1
        source, symbol, documented = match.groups()
        if documented is None:
            found.append(finding(path, number, "const-marker", "const 마커 바로 뒤에 숫자가 없다.", match.group(0)))
            continue
        value, error = constant_value(root, source, symbol)
        if error:
            found.append(finding(path, number, "const-marker", error, match.group(0)))
        elif float(documented.replace(",", "").replace("_", "")) != float(value):
            found.append(finding(path, number, "const-mismatch",
                                 f"문서는 {documented}, 코드 {source}:{symbol}은 {value}다. 같은 값으로 맞춰라.",
                                 match.group(0)))
    return found


def check_tracks(doc, text, changed):
    found = []
    for match in TRACKS_MARKER.finditer(without_code(text)):
        if match.group(1) in changed and doc not in changed:
            found.append(finding(doc, text.count("\n", 0, match.start()) + 1, "stale-doc",
                                 f"{match.group(1)}이 바뀌었지만 이 문서는 그대로다. 설명이 맞는지 확인하라.",
                                 match.group(0)))
    return found


def documents(root):
    for parent, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if Path(name).suffix.lower() in DOC_SUFFIXES:
                yield Path(parent, name).relative_to(root).as_posix()


# ---------------------------------------------------------------- commits

GIT_OPTION = r"(?:-[Cc]\s+(?:\"[^\"]*\"|'[^']*'|\S+)|--(?:git-dir|work-tree|namespace)(?:=|\s+)\S+|--[\w-]+|-p)"
COMMIT = re.compile(r"(?:^|[;&|(\n`]|\$\()\s*(?:\w+=\S*\s+)*(?:\S*/)?git(?:\.exe)?(?:\s+" + GIT_OPTION + r")*\s+commit(?![\w-])")


def is_commit(command):
    """True when a command segment runs `git commit`, not when `commit` is only an argument."""
    return COMMIT.search(command) is not None


def commit_message(command, root):
    heredoc = re.search(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\s*\1\b", command, re.S)
    if heredoc:
        return heredoc.group(2)
    herestring = re.search(r"@'\r?\n(.*?)\r?\n'@", command, re.S)
    if herestring:
        return herestring.group(1)
    parts = re.findall(r"(?:\s-[a-zA-Z]*m|--message)(?:\s+|=)(\"(?:[^\"\\]|\\.)*\"|'[^']*')", command)
    if parts:
        return "\n\n".join(p[1:-1].replace('\\"', '"').replace("\\n", "\n") for p in parts)
    file_arg = re.search(r"(?:-F|--file)(?:\s+|=)(\S+)", command)
    return read(Path(root, file_arg.group(1).strip("'\""))) if file_arg else None


def commit_rows(lines):
    for number, line in enumerate(lines, 1):
        if not line.strip():
            yield number, None, True, False
        else:
            content, starts = item(line.strip())
            yield number, content, starts, False


def check_commit(message):
    found = []
    lines = message.strip("\n").splitlines()
    for number, line in enumerate(lines, 1):
        for name, pattern in TOOL_MARKS.items():
            if pattern.search(line):
                found.append(finding("commit", number, "commit-trailer",
                                     f"도구·모델 표기({name})가 있다. 이 줄을 지워라.", line.strip()))
                break
    rows = list(commit_rows(lines))[1:]  # the subject is one line by definition
    for number, line in wraps(rows, open_ending):
        found.append(finding("commit", number, "commit-wrap", "문장 중간에서 줄을 바꿨다. 문장 단위로 줄을 바꿔라.",
                             line.strip()))
    return found


# ---------------------------------------------------------------- events

def snapshot(root):
    """The work tree when the session starts: tracked state as a commit, untracked files by content hash."""
    base = ((git(root, "stash", "create") or "").strip() or (git(root, "rev-parse", "HEAD") or "").strip()
            or EMPTY_TREE)
    return {"base": base, "untracked": untracked(root)}


def untracked(root):
    names = [n for n in (git(root, "ls-files", "--others", "--exclude-standard", "-z") or "").split("\0") if n]
    names = names[:MAX_UNTRACKED]
    hashes = (git(root, "hash-object", "--stdin-paths", stdin="\n".join(names) + "\n") or "").split() if names else []
    return dict(zip(names, hashes)) if len(hashes) == len(names) else {name: "" for name in names}


def changed_since(root, start):
    changed = {n.strip() for n in (git(root, "diff", "--name-only", "--relative", start["base"]) or "").splitlines()
               if n.strip()}
    before = start.get("untracked", {})
    changed.update(name for name, digest in untracked(root).items() if not digest or before.get(name) != digest)
    return changed


def prune(root):
    limit = time.time() - STATE_DAYS * 86400
    for path in state_dir(root).glob("*-*.json"):
        try:
            if path.stat().st_mtime < limit:
                path.unlink()
        except OSError:
            pass


def on_session(event, root):
    output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": GUIDE}}
    if git(root, "rev-parse", "--git-dir") is None:
        return output, None
    prune(root)
    path = state_file(root, "base", event.get("session_id"))
    if not path.exists():  # keep the first snapshot across /clear and compaction
        save(path, snapshot(root))
    return output, None


def on_pre(event, root):
    command = (event.get("tool_input") or {}).get("command", "")
    if not is_commit(command):
        return {}, None
    message = commit_message(command, root)
    found = check_commit(message) if message is not None else []
    if found:
        reason = "[kowrite] 커밋 메시지를 고친 뒤 다시 커밋하라.\n" + render(found)
        return ({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                        "permissionDecisionReason": reason}},
                {"action": "deny", "gate": "commit", "findings": found})
    # PostToolUse checks the commit only if this command actually moved HEAD.
    head = (git(root, "rev-parse", "--verify", "-q", "HEAD") or "").strip()
    save(state_file(root, "head", event.get("tool_use_id") or event.get("session_id")), {"head": head})
    if message is None:
        return {}, {"action": "unparsed", "command": command[:300]}
    return {}, {"action": "pass", "gate": "commit"}


def on_post(event, root):
    tool_input = event.get("tool_input") or {}
    if event.get("tool_name") in {"Bash", "PowerShell"}:
        if not is_commit(tool_input.get("command", "")):
            return {}, None
        marker = state_file(root, "head", event.get("tool_use_id") or event.get("session_id"))
        before = load(marker, None)
        try:
            marker.unlink()
        except (OSError, AttributeError):
            pass
        head = (git(root, "rev-parse", "--verify", "-q", "HEAD") or "").strip()
        if before is None or not head or before.get("head") == head:
            return {}, None
        found = check_commit(git(root, "log", "-1", "--format=%B") or "")
        intro = "[kowrite] 방금 만든 커밋의 메시지에 문제가 있다. `git commit --amend`로 메시지만 고쳐라.\n"
    else:
        name = tool_input.get("file_path") or ""
        path = Path(name if os.path.isabs(name) else Path(root, name)).resolve()
        try:
            relative = path.relative_to(Path(root).resolve()).as_posix()
        except ValueError:
            return {}, None
        suffix = path.suffix.lower()
        text = read(path) if suffix in DOC_SUFFIXES or suffix in COMMENT_PREFIX else None
        if text is None:
            return {}, None
        found = check_wraps(relative, text)
        if suffix in DOC_SUFFIXES:
            found += check_const_markers(root, relative, text)
        intro = "[kowrite] 방금 편집한 파일에 문제가 있다. 해당 줄을 고쳐라.\n"
    if not found:
        return {}, None
    return ({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": intro + render(found)}},
            {"action": "feedback", "findings": found})


def fingerprint(f):
    # Line numbers shift with edits; the same text with the same problem is the same finding.
    return "\t".join((f["path"], f["code"], f["message"], f["excerpt"]))


def on_stop(event, root):
    if git(root, "rev-parse", "--git-dir") is None:
        return {}, None
    session = event.get("session_id")
    start = load(state_file(root, "base", session), None) or {"base": "HEAD", "untracked": {}}
    changed = changed_since(root, start)
    found = []
    for name in sorted(changed):
        if Path(name).suffix.lower() in COMMENT_PREFIX:
            found += check_wraps(name, read(Path(root, name)) or "")
    for doc in documents(root):
        text = read(Path(root, doc)) or ""
        if doc in changed:
            found += check_wraps(doc, text) + check_const_markers(root, doc, text)
        elif {m.group(1) for m in CONST_MARKER.finditer(without_code(text))} & changed:
            found += check_const_markers(root, doc, text)
        found += check_tracks(doc, text, changed)
    if not found:
        return {}, None
    if event.get("stop_hook_active"):
        # One correction round only. What remains is recorded, not enforced.
        return {}, {"action": "unresolved", "findings": found}
    ledger = state_file(root, "blocked", session)
    seen = set(load(ledger, []))
    fresh = [f for f in found if fingerprint(f) not in seen]
    if not fresh:
        # Already reported in this session: the agent fixed it, explained it, or the user let it stand.
        return {}, {"action": "repeat", "findings": found}
    save(ledger, sorted(seen | {fingerprint(f) for f in fresh}))
    reason = "[kowrite] 끝내기 전에 아래를 고쳐라. 지적이 틀렸다면 고치지 말고 이유를 한 줄로 남겨라.\n" + render(fresh)
    return {"decision": "block", "reason": reason}, {"action": "block", "findings": fresh}


HANDLERS = {"session": on_session, "pre": on_pre, "post": on_post, "stop": on_stop}


def main(argv):
    if len(argv) != 2 or argv[1] not in HANDLERS:
        return 0
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        event = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    except (ValueError, UnicodeError):
        event = {}
    root = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    try:
        output, record = HANDLERS[argv[1]](event, root)
    except Exception as error:  # a broken check must not break the session
        output, record = {}, {"action": "error", "error": f"{type(error).__name__}: {error}"}
    if record is not None:
        record["event"] = argv[1]
        log(root, record)
    if output:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
