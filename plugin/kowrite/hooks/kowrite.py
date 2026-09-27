"""Korean writing rules for Claude Code. Standard library only; no model calls.

The session guide prevents the problems; the other hooks guarantee the rules when the guide is ignored.

Events:
  session  SessionStart  adds the guide; records HEAD so Stop also sees work committed during the session
  pre      PreToolUse    blocks `git commit` whose message has a tool trailer or a mid-sentence wrap
  post     PostToolUse   checks an edited document or comment file; rechecks a commit the gate could not parse
  stop     Stop          checks every change since the session started; blocks once

Markers, written in Markdown:
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
from pathlib import Path

HANGUL = re.compile(r"[가-힣]")
DOC_SUFFIXES = {".md", ".markdown"}
COMMENT_PREFIX = {".py": ("#",), ".sh": ("#",), ".yml": ("#",), ".yaml": ("#",),
                  ".js": ("//", "*", "/*"), ".ts": ("//", "*", "/*"), ".java": ("//", "*", "/*"),
                  ".kt": ("//", "*", "/*"), ".go": ("//",), ".rs": ("//",), ".c": ("//", "*", "/*")}
SKIP_DIRS = {".git", "node_modules", "build", "dist", "vendor", "__pycache__", ".venv"}
TRAILER = re.compile(r"^\s*(co-authored-by:|generated with|🤖)|claude\.ai/code/session|\[claude code\]\(", re.I)
# A line ending in a comma, particle or connective ending has not finished its sentence.
# Noun-final comment style ("만료 파일 삭제") ends in none of these and is left alone.
OPEN_ENDING = re.compile(r"(?:,|[가-힣](?<=[고며면서는을를의에와과로가은도만한된할될게지데니여해이및]))$")
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
GUIDE = """[kowrite]
- 문장은 짧게 쓰고, 한 문장이 끝나면 줄을 바꿔라.
- 커밋 메시지에 도구·모델 표기를 넣지 마라.
- 문서에 코드 상수 값을 적으면 값 앞에 `<!-- const: 경로:상수명 -->`을 붙여라.
- 코드를 설명하는 문서에는 `<!-- tracks: 경로 -->`를 적어라."""
MAX_BYTES = 256_000


# ---------------------------------------------------------------- utilities

def git(root, *args):
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def read(path):
    try:
        return None if path.stat().st_size > MAX_BYTES else path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return None


def state_dir(root):
    # Inside .git: never committed, never shown as untracked.
    return Path(root, ".git", "kowrite")


def log(root, record):
    try:
        folder = state_dir(root)
        folder.mkdir(parents=True, exist_ok=True)
        record["ts"] = dt.datetime.now(dt.timezone.utc).isoformat()
        with (folder / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def finding(path, line, code, message):
    return {"path": path, "line": line, "code": code, "message": message}


def render(findings, limit=25):
    lines = [f"- {f['path']}:{f['line']} [{f['code']}] {f['message']}" for f in findings[:limit]]
    if len(findings) > limit:
        lines.append(f"- 외 {len(findings) - limit}건")
    return "\n".join(lines)


def is_structural(stripped):
    return (not stripped or stripped.startswith(("#", "-", "*", "+", ">", "|", "<!--"))
            or re.match(r"^\d+[.)]\s", stripped) is not None)


def mid_sentence(line, following):
    if not following or line.endswith("  "):
        return False
    stripped, nxt = line.strip(), following.strip()
    return (bool(HANGUL.search(stripped)) and not is_structural(stripped) and not is_structural(nxt)
            and OPEN_ENDING.search(stripped) is not None)


# ---------------------------------------------------------------- line wraps

def prose_lines(path, text):
    """Yield (line number, text or None) for Markdown outside code blocks, or for code comments."""
    suffix = Path(path).suffix.lower()
    if suffix in DOC_SUFFIXES:
        fence = False
        for number, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith(("```", "~~~")):
                fence = not fence
                yield number, None
            else:
                yield number, None if fence or line.startswith(("    ", "\t")) else line
    elif suffix in COMMENT_PREFIX:
        prefixes = COMMENT_PREFIX[suffix]
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            marker = None if stripped.startswith("#!") else next((p for p in prefixes if stripped.startswith(p)), None)
            yield number, stripped[len(marker):].strip() if marker else None


def check_wraps(path, text):
    rows = list(prose_lines(path, text))
    return [finding(path, number, "ko-wrap", "문장 중간에서 줄을 바꿨다. 문장 단위로 줄을 바꿔라.")
            for index, (number, line) in enumerate(rows)
            if line and mid_sentence(line, rows[index + 1][1] if index + 1 < len(rows) else None)]


# ---------------------------------------------------------------- markers

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
        return (value, None) if isinstance(value, (int, float)) else (None, f"{symbol}이 숫자가 아니다.")
    matches = re.findall(rf"\b{re.escape(symbol)}\b\s*(?::[^=\n]+)?=\s*([+-]?[\d_]+(?:\.\d+)?)", text)
    if len(matches) != 1:
        return None, f"{source}에서 {symbol}의 정의를 하나로 특정할 수 없다."
    return float(matches[0].replace("_", "")), None


def check_const_markers(root, path, text):
    found = []
    for match in re.finditer(r"<!--\s*const:\s*([^\s:]+):(\w+)\s*-->\s*([+-]?\d[\d_,]*(?:\.\d+)?)?", text):
        number = text.count("\n", 0, match.start()) + 1
        source, symbol, documented = match.groups()
        if documented is None:
            found.append(finding(path, number, "const-marker", "const 마커 바로 뒤에 숫자가 없다."))
            continue
        value, error = constant_value(root, source, symbol)
        if error:
            found.append(finding(path, number, "const-marker", error))
        elif float(documented.replace(",", "").replace("_", "")) != float(value):
            found.append(finding(path, number, "const-mismatch",
                                 f"문서는 {documented}, 코드 {source}:{symbol}은 {value}다. 같은 값으로 맞춰라."))
    return found


def check_tracks(doc, text, changed):
    found = []
    for match in re.finditer(r"<!--\s*tracks:\s*([^\s>]+)\s*-->", text):
        if match.group(1) in changed and doc not in changed:
            found.append(finding(doc, text.count("\n", 0, match.start()) + 1, "stale-doc",
                                 f"{match.group(1)}이 바뀌었지만 이 문서는 그대로다. 설명이 맞는지 확인하라."))
    return found


def documents(root):
    for parent, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if Path(name).suffix.lower() in DOC_SUFFIXES:
                yield Path(parent, name).relative_to(root).as_posix()


# ---------------------------------------------------------------- commits

def is_commit(command):
    return re.search(r"\bgit\b[^;&|\n]*\bcommit\b", command) is not None


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


def check_commit(message):
    found = []
    lines = message.strip("\n").splitlines()
    for number, line in enumerate(lines, 1):
        if TRAILER.search(line):
            found.append(finding("commit", number, "commit-trailer", "도구·모델 표기가 있다. 이 줄을 지워라."))
    body = lines[1:]
    for index, line in enumerate(body):
        if mid_sentence(line, body[index + 1] if index + 1 < len(body) else ""):
            found.append(finding("commit", index + 2, "commit-wrap",
                                 "문장 중간에서 줄을 바꿨다. 문장 단위로 줄을 바꿔라."))
    return found


# ---------------------------------------------------------------- events

def on_session(event, root):
    output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": GUIDE}}
    if git(root, "rev-parse", "--git-dir") is None:
        return output, None
    path = state_dir(root) / f"base-{re.sub(r'[^0-9A-Za-z_-]', '', str(event.get('session_id', 'none')))}"
    if not path.exists():  # keep the first base across /clear and compaction
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((git(root, "rev-parse", "HEAD") or EMPTY_TREE).strip(), encoding="utf-8")
        except OSError:
            pass
    return output, None


def on_pre(event, root):
    command = (event.get("tool_input") or {}).get("command", "")
    if not is_commit(command):
        return {}, None
    message = commit_message(command, root)
    if message is None:
        return {}, {"action": "unparsed", "command": command[:300]}  # PostToolUse checks the result
    found = check_commit(message)
    if not found:
        return {}, {"action": "pass", "gate": "commit"}
    reason = "[kowrite] 커밋 메시지를 고친 뒤 다시 커밋하라.\n" + render(found)
    return ({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                    "permissionDecisionReason": reason}},
            {"action": "deny", "gate": "commit", "findings": found})


def on_post(event, root):
    tool_input = event.get("tool_input") or {}
    if event.get("tool_name") in {"Bash", "PowerShell"}:
        if not is_commit(tool_input.get("command", "")) or git(root, "rev-parse", "--verify", "HEAD") is None:
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


def on_stop(event, root):
    if git(root, "rev-parse", "--git-dir") is None:
        return {}, None
    session = state_dir(root) / f"base-{re.sub(r'[^0-9A-Za-z_-]', '', str(event.get('session_id', 'none')))}"
    base = (read(session) or "HEAD").strip()
    changed = set()
    for args in (("diff", base, "--name-only"), ("ls-files", "--others", "--exclude-standard")):
        changed.update(n.strip() for n in (git(root, *args) or "").splitlines() if n.strip())
    found = []
    for name in sorted(changed):
        if Path(name).suffix.lower() in COMMENT_PREFIX:
            found += check_wraps(name, read(Path(root, name)) or "")
    for doc in documents(root):
        text = read(Path(root, doc)) or ""
        if doc in changed:
            found += check_wraps(doc, text) + check_const_markers(root, doc, text)
        elif set(re.findall(r"<!--\s*const:\s*([^\s:]+):", text)) & changed:
            found += check_const_markers(root, doc, text)
        found += check_tracks(doc, text, changed)
    if not found:
        return {}, None
    if event.get("stop_hook_active"):
        # One correction round only. What remains is recorded, not enforced.
        return {}, {"action": "unresolved", "findings": found}
    reason = "[kowrite] 끝내기 전에 아래를 고쳐라. 지적이 틀렸다면 고치지 말고 이유를 한 줄로 남겨라.\n" + render(found)
    return {"decision": "block", "reason": reason}, {"action": "block", "findings": found}


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
