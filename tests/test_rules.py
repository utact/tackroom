"""Rules, tested by dimension.

Each rule names its dimensions and the values of each dimension.
Cases are the cross product, and the expected result is stated per value, not per case.
A coverage test fails when a value in the hook (an ending, a noun, a tool, a mark) has no case.
"""

import itertools
import unittest

from support import Repo, kowrite

# ---------------------------------------------------------------- predicate grid
# Korean sentences end, and pause, on a predicate. The grid is predicate x form column.
# Each value has one entry per column in column order; '/' separates variants within an entry.
# Case sentences are written out by hand, and each variant must end with its form.

PREDICATES = ("되다", "않다", "없다", "이다", "있다", "하다")

FORM_COLUMNS = ("명사형 현재", "한다체 현재", "합니다체 현재", "명사형 과거", "한다체 과거", "합니다체 과거")
PREDICATE_FORMS = {
    "되다": ("됨", "된다", "됩니다", "되었음/됐음", "되었다/됐다", "되었습니다/됐습니다"),
    "않다": ("않음", "않는다", "않습니다", "않았음", "않았다", "않았습니다"),
    "없다": ("없음", "없다", "없습니다", "없었음", "없었다", "없었습니다"),
    "이다": ("임", "이다", "입니다", "이었음/였음", "이었다/였다", "이었습니다/였습니다"),
    "있다": ("있음", "있다", "있습니다", "있었음", "있었다", "있었습니다"),
    "하다": ("함", "한다", "합니다", "하였음/했음", "하였다/했다", "하였습니다/했습니다"),
}
SENTENCES = {
    "되다": ("색상 선택이 됨", "색상 선택이 된다", "색상 선택이 됩니다",
             "색상 선택이 되었음/색상 선택이 됐음", "색상 선택이 되었다/색상 선택이 됐다",
             "색상 선택이 되었습니다/색상 선택이 됐습니다"),
    "않다": ("색상을 변경하지 않음", "색상을 변경하지 않는다", "색상을 변경하지 않습니다",
             "색상을 변경하지 않았음", "색상을 변경하지 않았다", "색상을 변경하지 않았습니다"),
    "없다": ("선택한 색상이 없음", "선택한 색상이 없다", "선택한 색상이 없습니다",
             "선택한 색상이 없었음", "선택한 색상이 없었다", "선택한 색상이 없었습니다"),
    "이다": ("선택한 색상임", "선택한 색상이다", "선택한 색상입니다",
             "선택한 색상이었음/선택한 후보였음", "선택한 색상이었다/선택한 후보였다",
             "선택한 색상이었습니다/선택한 후보였습니다"),
    "있다": ("선택한 색상이 있음", "선택한 색상이 있다", "선택한 색상이 있습니다",
             "선택한 색상이 있었음", "선택한 색상이 있었다", "선택한 색상이 있었습니다"),
    "하다": ("색상 선택을 함", "색상 선택을 한다", "색상 선택을 합니다",
             "색상 선택을 하였음/색상 선택을 했음", "색상 선택을 하였다/색상 선택을 했다",
             "색상 선택을 하였습니다/색상 선택을 했습니다"),
}

# The same predicates stopped before the sentence ends: connectives and modifiers.
CONNECTIVE_COLUMNS = ("나열 고", "나열 며", "조건 면", "원인 어서", "배경 는데", "대조 지만", "목적 도록", "선택 거나",
                      "관형 현재", "관형 과거", "관형 미래")
CONNECTIVE_FORMS = {
    "되다": ("되고", "되며", "되면", "되어서/돼서", "되는데", "되지만", "되도록", "되거나", "되는", "된", "될"),
    "않다": ("않고", "않으며", "않으면", "않아서", "않는데", "않지만", "않도록", "않거나", "않는", "않은", "않을"),
    "없다": ("없고", "없으며", "없으면", "없어서", "없는데", "없지만", "없도록", "없거나", "없는", "", "없을"),
    "이다": ("이고", "이며", "이면", "이어서/여서", "인데", "이지만", "", "이거나/거나", "인", "", "일"),
    "있다": ("있고", "있으며", "있으면", "있어서", "있는데", "있지만", "있도록", "있거나", "있는", "", "있을"),
    "하다": ("하고", "하며", "하면", "하여서/해서", "하는데", "하지만", "하도록", "하거나", "하는", "한", "할"),
}
CONNECTIVES = {
    "되다": ("색상 선택이 되고", "색상 선택이 되며", "색상 선택이 되면", "색상 선택이 되어서/색상 선택이 돼서",
             "색상 선택이 되는데", "색상 선택이 되지만", "색상 선택이 되도록", "색상 선택이 되거나",
             "색상 선택이 되는", "색상 선택이 된", "색상 선택이 될"),
    "않다": ("색상을 변경하지 않고", "색상을 변경하지 않으며", "색상을 변경하지 않으면", "색상을 변경하지 않아서",
             "색상을 변경하지 않는데", "색상을 변경하지 않지만", "색상을 변경하지 않도록", "색상을 변경하지 않거나",
             "색상을 변경하지 않는", "색상을 변경하지 않은", "색상을 변경하지 않을"),
    "없다": ("선택한 색상이 없고", "선택한 색상이 없으며", "선택한 색상이 없으면", "선택한 색상이 없어서",
             "선택한 색상이 없는데", "선택한 색상이 없지만", "선택한 색상이 없도록", "선택한 색상이 없거나",
             "선택한 색상이 없는", "", "선택한 색상이 없을"),
    "이다": ("선택한 색상이고", "선택한 색상이며", "선택한 색상이면", "선택한 색상이어서/선택한 후보여서",
             "선택한 색상인데", "선택한 색상이지만", "", "선택한 색상이거나/선택한 후보거나",
             "선택한 색상인", "", "선택한 색상일"),
    "있다": ("선택한 색상이 있고", "선택한 색상이 있으며", "선택한 색상이 있으면", "선택한 색상이 있어서",
             "선택한 색상이 있는데", "선택한 색상이 있지만", "선택한 색상이 있도록", "선택한 색상이 있거나",
             "선택한 색상이 있는", "", "선택한 색상이 있을"),
    "하다": ("색상 선택을 하고", "색상 선택을 하며", "색상 선택을 하면", "색상 선택을 하여서/색상 선택을 해서",
             "색상 선택을 하는데", "색상 선택을 하지만", "색상 선택을 하도록", "색상 선택을 하거나",
             "색상 선택을 하는", "색상 선택을 한", "색상 선택을 할"),
}
# Cells the comment rule leaves undetected on purpose, with the reason. The test pins this behavior.
KNOWN_GAPS = {
    ("이다", "관형 현재"): "인은 확인·원인·로그인 같은 명사와 겹친다.",
    ("이다", "관형 미래"): "일은 파일·요일 같은 명사와 겹친다.",
}


def grid(forms, sentences, columns):
    """Yield (predicate, column, sentence) for every variant, checking each sentence ends with its form."""
    for predicate in PREDICATES:
        assert len(forms[predicate]) == len(sentences[predicate]) == len(columns), predicate
        for column, form, sentence in zip(columns, forms[predicate], sentences[predicate]):
            assert bool(form) == bool(sentence), (predicate, column)
            for f, s in zip(form.split("/") if form else [], sentence.split("/") if sentence else []):
                assert s.endswith(f), (predicate, column, s, f)
                yield predicate, column, s


class PredicateGrid(unittest.TestCase):

    def test_sentence_ends(self):
        """Every predicate in every form ends a sentence, with or without a period."""
        for predicate, column, sentence in grid(PREDICATE_FORMS, SENTENCES, FORM_COLUMNS):
            for line in (sentence, sentence + "."):
                label = f"{predicate} / {column} / {line}"
                self.assertEqual(kowrite.check_wraps("x.md", f"{line}\n이어지는 말이다.\n"), [], label)
                self.assertEqual(kowrite.check_wraps("x.py", f"# {line}\n# 이어지는 말이다.\n"), [], label)
                self.assertEqual(kowrite.check_commit(f"fix: 제목\n\n{line}\n이어지는 말이다."), [], label)

    def test_connectives_stay_open(self):
        """A connective or modifier followed by more text is a wrap, except the documented gaps in comments."""
        for predicate, column, sentence in grid(CONNECTIVE_FORMS, CONNECTIVES, CONNECTIVE_COLUMNS):
            label = f"{predicate} / {column} / {sentence}"
            self.assertTrue(kowrite.check_wraps("x.md", f"{sentence}\n이어지는 말이다.\n"), label)
            expected = (predicate, column) not in KNOWN_GAPS
            self.assertEqual(bool(kowrite.check_wraps("x.py", f"# {sentence}\n# 이어지는 말이다.\n")), expected, label)
            self.assertEqual(bool(kowrite.check_commit(f"fix: 제목\n\n{sentence}\n이어지는 말이다.")), expected, label)

    def test_coverage(self):
        self.assertEqual(set(PREDICATE_FORMS), set(PREDICATES))
        self.assertEqual(set(CONNECTIVE_FORMS), set(PREDICATES))
        self.assertTrue(set(KNOWN_GAPS) <= {(p, c) for p in PREDICATES for c in CONNECTIVE_COLUMNS})
        for column in range(len(CONNECTIVE_COLUMNS)):
            self.assertTrue(any(CONNECTIVE_FORMS[p][column] for p in PREDICATES), CONNECTIVE_COLUMNS[column])


# ---------------------------------------------------------------- Markdown wraps
# A Markdown paragraph line must end its sentence, because Markdown joins it with the next line.
# carrier x line ending x hard break x next line; a finding is expected iff the ending is open and the next line joins.
# Predicate endings are covered by the grid above; this axis covers punctuation and what is not a predicate.

MD_CARRIERS = {  # (prefix of the checked line, prefix of a joining next line)
    "paragraph": ("", ""),
    "list item": ("- ", "  "),
    "ordered item": ("1. ", "   "),
    "nested item": ("  - ", "    "),
    "blockquote": ("> ", "> "),
    "quoted item": ("> - ", ">   "),
}
MD_ENDINGS = {  # line ending -> is the sentence still open?
    **{f"terminal {mark}": (f"설명을 마쳤다{mark}", False) for mark in (".", "!", "?", ":", ";", "…", "。")},
    "question 까": ("설명을 마쳤을까", False),
    "polite 요": ("설명을 마쳤어요", False),
    "confirming 죠": ("설명을 마쳤죠", False),
    "closer after terminal": ("설명을 마쳤다.)", False),
    "quote after terminal": ("설명을 마쳤다.”", False),
    "no hangul": ("See the reference", False),  # open when the next line is Korean; see test_cross_product
    "comma": ("설명을 마치고,", True),
    "particle": ("이 설명은 길어서 중간에서", True),
    **{f"particle ending in 다 {w}": (f"차단은 {w}", True) for w in ("세션마다", "이전보다", "여기에다")},
    "noun": ("성능 평가", True),
    "inline code": ("설정은 `config.json`", True),
    "link": ("자세한 내용은 [문서](a.md)", True),
    "english word": ("값은 JSON", True),
}
MD_HARD_BREAKS = {"none": "", "two spaces": "  ", "backslash": "\\"}
MD_NEXT = {  # next line -> does it join the paragraph?
    "continuation": (None, True),
    "english continuation": ("and continues here.", True),
    "blank": ("", False),
    "heading": ("## 제목", False),
    "list item": ("- 다음 항목", False),
    "ordered item": ("2. 다음 항목", False),
    "table": ("| 칸 | 칸 |", False),
    "fence": ("```", False),
    "tilde fence": ("~~~", False),
    "html comment": ("<!-- 주석 -->", False),
    "thematic break": ("***", False),
    "setext underline": ("===", False),
    "footnote": ("[^1]: 각주", False),
    "end of file": (False, False),
}


def markdown_case(carrier, ending, hard, following):
    head, joined = MD_CARRIERS[carrier]
    text, _ = MD_ENDINGS[ending]
    nxt, _ = MD_NEXT[following]
    lines = [head + text + MD_HARD_BREAKS[hard]]
    if nxt is None:
        lines.append(joined + "이어지는 말이다.")
    elif nxt is not False:
        lines.append(nxt)
    return "\n".join(lines) + "\n"


class MarkdownWraps(unittest.TestCase):

    def test_cross_product(self):
        failures = []
        for carrier, ending, hard, following in itertools.product(MD_CARRIERS, MD_ENDINGS, MD_HARD_BREAKS, MD_NEXT):
            # An English line is judged only when it runs into Korean text.
            is_open = MD_ENDINGS[ending][1] or (ending == "no hangul" and following == "continuation")
            expected = is_open and MD_NEXT[following][1] and hard == "none"
            text = markdown_case(carrier, ending, hard, following)
            actual = bool(kowrite.check_wraps("x.md", text))
            if actual != expected:
                failures.append(f"{carrier} / {ending} / {hard} / {following}: expected {expected}\n{text}")
        self.assertEqual(failures, [], "\n".join(failures[:10]))

    def test_code_is_not_prose(self):
        for text in ("```\n이 코드는 길어서\n줄을 바꿨다\n```\n", "~~~~\n```\n이 코드는\n줄을 바꿨다\n~~~~\n",
                     "앞 문단이다.\n\n    이 코드는 들여써서\n    줄을 바꿨다\n",
                     "---\ntitle: 앞머리의 제목과\ntags: 태그\n---\n"):
            self.assertEqual(kowrite.check_wraps("x.md", text), [], text)

    def test_indented_paragraph_inside_list_is_prose(self):
        text = "- 항목이다.\n\n    항목의 둘째 문단이 길어서\n    줄을 바꿨다.\n"
        self.assertEqual([f["line"] for f in kowrite.check_wraps("x.md", text)], [3])
        text = "- 항목이다.\n\n문단이 목록을 닫는다.\n\n    코드는 들여써서\n    줄을 바꿨다\n"
        self.assertEqual(kowrite.check_wraps("x.md", text), [], "a paragraph closes the list")

    def test_coverage(self):
        ends = {e[-1] for e, _ in MD_ENDINGS.values()} | {s[-1] for _, _, s in grid(PREDICATE_FORMS, SENTENCES, FORM_COLUMNS)}
        self.assertEqual(kowrite.SENTENCE_END - ends, set(), "every sentence end needs a case")
        self.assertTrue(all(any(e.endswith(w) for e, _ in MD_ENDINGS.values()) for w in kowrite.NOT_ENDS))
        self.assertEqual({v for _, v in MD_ENDINGS.values()}, {True, False})
        self.assertEqual({v for _, v in MD_NEXT.values()}, {True, False})


# ---------------------------------------------------------------- comment and commit wraps
# Comments keep their line breaks, so only an ending that cannot close a sentence is a wrap.
# language x ending x next line. Predicate endings are covered by the grid above.

OPEN_EXAMPLES = {  # one real word per ending; the coverage test requires every ending in the hook
    "고": "읽고", "며": "읽으며", "면": "없으면", "서": "읽어서", "는": "캐시는", "을": "파일을", "를": "캐시를",
    "의": "요청의", "에": "파일에", "와": "캐시와", "과": "파일과", "로": "캐시로", "가": "캐시가", "은": "파일은",
    "도": "캐시도", "만": "파일만", "한": "필요한", "된": "저장된", "할": "삭제할", "될": "사용될", "게": "빠르게",
    "지": "않는지", "데": "있는데", "니": "없으니", "여": "위하여", "해": "위해", "이": "파일이", "및": "캐시 및",
    "도록": "쓰도록", "거나": "읽거나",
}
# Nouns ending in one of the endings. Written here, not read from the hook, so removing one from the hook fails.
NOUNS = """추가 대가 참고 경고 최고 광고 창고 재고 문서 순서 화면 측면 이면 표면 전면
메시지 이미지 페이지 여지 유지 방지 금지 이해 피해 방해 제한 권한 기한 무한
속도 한도 정도 제도 온도 빈도 밀도 용도 의도 정의 회의 논의 주의 합의 문의 길이 높이 결과""".split()
# A particle after the wrong kind of syllable is not a particle: 평가 is a noun, 차이 is a noun.
PARTICLE_MISMATCH = {"가": "평가", "를": "평를", "와": "평와", "이": "차이", "은": "캐은", "을": "마을", "과": "효과",
                     "로": "경로"}
COMMENT_ENDINGS = {
    **{f"open {e}": (f"오래된 {w}", True) for e, w in OPEN_EXAMPLES.items()},
    "comma": ("캐시를 비우고,", True),
    "ㄹ final before 로": ("파일로", True),
    "는 after a final consonant": ("값이 있는", True),
    **{f"particle after non-hangul {w}": (f"응답의 {w}", True) for w in ("API가", "JSON을", "status(200)이", "v2로")},
    "lone determiner": ("값을 비교할 때 이", True),
    **{f"noun {n}": (f"요청 {n}", False) for n in NOUNS},
    **{f"particle mismatch {e}": (f"요청 {w}", False) for e, w in PARTICLE_MISMATCH.items()},
    "noun style": ("만료 파일 삭제", False),
    "no hangul": ("see below", False),
}
COMMENT_STYLES = {".py": ("# ", "# "), ".py docstring": ('"""', ""), ".sh": ("# ", "# "), ".yml": ("# ", "# "),
                  ".yaml": ("# ", "# "), ".js": ("// ", "// "), ".ts": (" * ", " * "), ".java": ("// ", "// "),
                  ".kt": ("// ", "// "), ".go": ("// ", "// "), ".rs": ("// ", "// "), ".c": ("/* ", " * ")}
COMMENT_NEXT = {"continuation": True, "code": False, "blank comment": False, "list item": False, "end of file": False}


def comment_case(style, ending, following):
    head, more = COMMENT_STYLES[style]
    text, _ = COMMENT_ENDINGS[ending]
    if style == ".py docstring":
        tail = {"continuation": "이어지는 말이다.\n\"\"\"", "code": '"""', "blank comment": '\n"""',
                "list item": '- 항목\n"""', "end of file": '"""'}[following]
        return f'{head}{text}\n{tail}\nx = 1\n'
    tail = {"continuation": more + "이어지는 말이다.", "code": "x = 1", "blank comment": more.rstrip(),
            "list item": more + "- 항목", "end of file": None}[following]
    return head + text + ("\n" + tail if tail is not None else "") + "\n"


class CommentWraps(unittest.TestCase):

    def test_cross_product(self):
        failures = []
        for style, ending, following in itertools.product(COMMENT_STYLES, COMMENT_ENDINGS, COMMENT_NEXT):
            expected = COMMENT_ENDINGS[ending][1] and COMMENT_NEXT[following]
            text = comment_case(style, ending, following)
            actual = bool(kowrite.check_wraps("x" + style.split()[0], text))
            if actual != expected:
                failures.append(f"{style} / {ending} / {following}: expected {expected}\n{text}")
        self.assertEqual(failures, [], "\n".join(failures[:10]))

    def test_commit_body_uses_the_comment_rule(self):
        for ending, (text, expected) in COMMENT_ENDINGS.items():
            found = kowrite.check_commit(f"fix: 제목\n\n{text}\n이어지는 말이다.")
            self.assertEqual(bool(found), expected, ending)

    def test_doctest_is_not_prose(self):
        text = 'def f():\n    """캐시를 비운다.\n\n    >>> f(캐시를\n    ... 비우고)\n    """\n'
        self.assertEqual(kowrite.check_wraps("x.py", text), [])

    def test_commit_subject_is_one_line(self):
        self.assertEqual(kowrite.check_commit("fix: 캐시를 비우고,\n본문이 바로 이어진다.\n"), [])

    def test_coverage(self):
        self.assertEqual(set(OPEN_EXAMPLES), kowrite.OPEN_ENDINGS | set(kowrite.OPEN_SUFFIXES),
                         "every ending needs a real word")
        for ending, word in OPEN_EXAMPLES.items():
            self.assertTrue(word.endswith(ending) and kowrite.open_ending(word), word)
        self.assertTrue(set(kowrite.NOUNS) <= set(NOUNS), "every noun exception needs a case")
        self.assertEqual(set(PARTICLE_MISMATCH),
                         kowrite.AFTER_OPEN_SYLLABLE | kowrite.AFTER_CLOSED_SYLLABLE | {"로"})
        self.assertEqual({s.split()[0] for s in COMMENT_STYLES}, set(kowrite.COMMENT_PREFIX))


# ---------------------------------------------------------------- commit marks
# mark kind x position in the message; human text with the same words must pass.

TOOLS = ("claude", "anthropic", "openai", "chatgpt", "codex", "copilot", "cursor", "gemini", "devin", "aider")
MARKS = {
    "session-link": ["See https://claude.ai/code/session_01ABC", "https://chatgpt.com/codex/tasks/task_1"],
    "session-trailer": [f"{t.title()}-Session: https://example.com/s/1" for t in TOOLS],
    "generated": [f"Generated with {t.title()}" for t in TOOLS] + ["generated by [Claude Code](x)"],
    "robot": ["\N{ROBOT FACE} Generated"],
    "tool-coauthor": [f"Co-authored-by: {t.title()} <bot@{t}.com>" for t in TOOLS]
                     + ["Co-Authored-By: Someone <noreply@anthropic.com>"],
}
HUMAN = ["Co-authored-by: Kim Minji <minji@example.com>", "세션 만료 시간을 늘렸다.", "session: 로그인 세션 수정",
         "Generated with protoc 3.21", "claude.ai 문서를 참고했다."]
POSITIONS = {"subject": lambda l: f"{l}\n", "body": lambda l: f"fix: 제목\n\n{l}\n",
             "trailer block": lambda l: f"fix: 제목\n\n본문이다.\n\n{l}\n"}


class CommitMarks(unittest.TestCase):

    def test_marks_by_position(self):
        for (kind, lines), position in itertools.product(MARKS.items(), POSITIONS):
            for line in lines:
                codes = [f["message"] for f in kowrite.check_commit(POSITIONS[position](line))]
                self.assertTrue(any(f"({kind})" in c for c in codes), f"{kind} / {position}: {line}")

    def test_human_text_passes(self):
        for line, position in itertools.product(HUMAN, POSITIONS):
            self.assertEqual(kowrite.check_commit(POSITIONS[position](line)), [], f"{position}: {line}")

    def test_coverage(self):
        self.assertEqual(set(MARKS), set(kowrite.TOOL_MARKS))
        for kind, lines in MARKS.items():
            self.assertTrue(all(kowrite.TOOL_MARKS[kind].search(line) for line in lines), kind)
        self.assertTrue(set(kowrite.TOOLS) <= set(TOOLS), "every tool needs cases")


# ---------------------------------------------------------------- commit command detection
# invocation form x separator before it; `commit` as an argument or a different subcommand must not match.

FORMS = ["git commit -m 'x'", "/usr/bin/git commit -m 'x'", "git.exe commit -m 'x'", "GIT_EDITOR=true git commit",
         "git -C ../repo commit -m 'x'", 'git -C "my repo" commit', "git -c user.name=me commit -m 'x'",
         "git --no-pager commit", "git --git-dir=.git --work-tree=. commit", "git commit --amend --no-edit"]
SEPARATORS = {"start": "{}", "and": "git add . && {}", "semicolon": "cd a; {}", "or": "false || {}",
              "pipe": "echo | {}", "newline": "git add .\n{}", "subshell": "({})", "substitution": "x=$({})"}
NOT_COMMITS = ["git log --grep commit", "git show commit", "echo 'git commit'", 'grep -r "git commit" .',
               "git commit-tree HEAD^{tree}", "git rev-parse HEAD", "gitcommit", "git log --format=%s -- commit.md"]


class CommitCommands(unittest.TestCase):

    def test_forms_by_separator(self):
        for form, (name, template) in itertools.product(FORMS, SEPARATORS.items()):
            self.assertTrue(kowrite.is_commit(template.format(form)), f"{name}: {form}")

    def test_not_commits(self):
        for command, (name, template) in itertools.product(NOT_COMMITS, SEPARATORS.items()):
            self.assertFalse(kowrite.is_commit(template.format(command)), f"{name}: {command}")

    def test_message_sources(self):
        cases = {"-m": "git commit -m 'fix: 제목'", "-am": "git commit -am \"fix: 제목\"",
                 "--message=": "git commit --message='fix: 제목'",
                 "heredoc": "git commit -F - <<'EOF'\nfix: 제목\nEOF",
                 "powershell": "git commit -F - @'\nfix: 제목\n'@"}
        for name, command in cases.items():
            self.assertEqual(kowrite.commit_message(command, "."), "fix: 제목", name)
        self.assertEqual(kowrite.commit_message("git commit -m 'a' -m 'b'", "."), "a\n\nb")


# ---------------------------------------------------------------- const markers
# marker location x source language x value state.

LOCATIONS = {"text": ("{}", True), "inline code": ("`{}`", False), "backtick fence": ("```\n{}\n```", False),
             "tilde fence": ("~~~\n{}\n~~~", False), "list item": ("- {}", True), "table cell": ("| {} |", True)}
SOURCES = {"py": ("c.py", "LIMIT = {}\n"), "py annotated": ("c.py", "LIMIT: int = {}\n"),
           "java": ("C.java", "static final int LIMIT = {};\n"), "kotlin": ("C.kt", "const val LIMIT = {}\n"),
           "go": ("c.go", "const LIMIT = {}\n"), "ts": ("c.ts", "export const LIMIT: number = {};\n")}
VALUES = {  # documented, defined -> expected code
    "equal": ("256", "256", None), "equal with comma": ("256,000", "256_000", None),
    "equal float": ("0.5", "0.5", None), "mismatch": ("128", "256", "const-mismatch"),
    "missing number": ("", "256", "const-marker"),
}


class ConstMarkers(Repo):

    def test_cross_product(self):
        for (loc, (template, active)), (lang, (name, source)), (state, (doc, code, expected)) in itertools.product(
                LOCATIONS.items(), SOURCES.items(), VALUES.items()):
            self.write(name, source.format(code))
            text = template.format(f"<!-- const: {name}:LIMIT -->{doc}") + "\n"
            codes = [f["code"] for f in kowrite.check_const_markers(self.root, "d.md", text)]
            self.assertEqual(codes, [expected] if expected and active else [], f"{loc} / {lang} / {state}")

    def test_unresolvable_definitions(self):
        cases = {"no file": ("none.py", None), "not a literal": ("c.py", "LIMIT = 2 * 128\n"),
                 "boolean": ("c.py", "LIMIT = True\n"), "string": ("c.py", "LIMIT = '256'\n"),
                 "two definitions": ("c.py", "LIMIT = 1\nLIMIT = 2\n"), "syntax error": ("c.py", "LIMIT = (\n")}
        for name, (path, source) in cases.items():
            if source is not None:
                self.write(path, source)
            codes = [f["code"] for f in kowrite.check_const_markers(self.root, "d.md", f"<!-- const: {path}:LIMIT -->1")]
            self.assertEqual(codes, ["const-marker"], name)


if __name__ == "__main__":
    unittest.main()
