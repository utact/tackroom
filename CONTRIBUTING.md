# 기여 관례

개발 환경과 검사, 브랜치·커밋·병합 형식을 정한다.
이 관례를 정하기 전의 커밋은 고치지 않는다.

## 개발 환경

Python 3.8 이상이 필요하다.
kowrite 통합 테스트에는 Git과 Bash가 필요하며, Windows에서는 Git Bash를 쓴다.

```sh
python scripts/sync_references.py
python -m unittest discover -s tests
claude plugin validate .
claude plugin validate plugin/techjudge
claude plugin validate plugin/harness
claude plugin validate plugin/kowrite
```

| 테스트 | 확인 대상 |
| --- | --- |
| `test_plugins.py` | 패키지 참조·동기화·배포 경로 |
| `test_stacks.py` | 기술 카드의 목록·절·형식 |
| `test_rules.py` | 문장·커밋·상수 연결 규칙 |
| `test_state.py` | 세션 상태·변경 추적 |
| `test_regressions.py` | 발견한 실패의 재현 |
| `test_metrics.py` | 검사기의 오탐·탐지율 |

## 근거와 보고

- 설명에는 뒷받침하는 출처와 버전을 붙인다.
- 문제를 보고할 때는 요청, 환경, 예상 결과, 실제 결과를 적는다.

## 브랜치

`main`이 기본 브랜치다.
다른 사람의 작업과 겹치지 않으면 `main`에 직접 커밋한다.
작업이 겹치거나 검토가 필요하면 `main`에서 브랜치를 만든다.

```text
<type>/<요약>
```

- `type`은 커밋의 `type`과 같은 목록에서 고른다. 여러 종류가 섞이면 주된 결과를 기준으로 한다.
- 요약은 영어 소문자와 숫자를 하이픈으로 잇는다. 예: `feat/techjudge-harness-plugins`, `fix/kowrite-python-alias`.
- 도구나 세션이 붙인 이름(`claude/...` 등)은 병합 전에 이 형식으로 바꾼다.
- 병합한 브랜치는 지운다.

## 커밋

```text
<type>: <제목>

- <무엇을 왜 바꿨는지>
```

| type | 쓰는 경우 |
|---|---|
| `feat` | 플러그인·Skill·훅의 새 기능, 동작을 바꾸는 지침 |
| `fix` | 결함 수정 |
| `docs` | 조사 자료와 설명 문서 |
| `refactor` | 동작을 유지하는 구조 변경 |
| `test` | 테스트만 추가·수정 |
| `chore` | 빌드·설정·저장소 관리 |

- 제목은 한국어로 쓰고 명사형으로 끝낸다(`수정`, `추가`, `보완`). 마침표를 찍지 않는다.
- 한 커밋에는 한 가지 작업을 담는다. 명사를 나열할 때는 `,`나 `·`를 쓰고, 두 동작을 이을 때는 "~하고"로 쓴다. `&`는 쓰지 않는다.
- 제목에 작업 세 개 이상을 이어야 한다면 커밋을 나눈다.
- 본문은 제목 다음 빈 줄 뒤에 `- ` 목록으로 쓰고, 각 항목은 "~다."로 끝낸다.
- 도구·모델 표기(`Co-Authored-By` 등)와 세션 링크를 넣지 않는다. kowrite가 커밋 직전에 막는다.
- 각 커밋에서 테스트가 통과해야 한다. `docs/`를 바꾸면 생성된 플러그인 참조도 같은 커밋에 넣는다.
- 플러그인 동작이 바뀌면 `plugin.json`의 버전을 올린다. `fix`는 패치, `feat`는 마이너 자리다.

## 병합

`main`에는 병합 커밋(`--no-ff`)으로 합쳐 브랜치 단위의 작업 경계를 남긴다.
병합 커밋도 커밋 형식을 따른다.

```text
<type>: <브랜치가 이룬 결과>

<type>/<요약> 브랜치를 병합한다.

- <포함한 주요 변경>
```

- 병합 전에 브랜치에서 테스트와 `python scripts/sync_references.py --check`를 통과시킨다.
- 공개된 `main`의 히스토리는 다시 쓰지 않는다.
