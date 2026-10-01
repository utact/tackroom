# Tackroom

AI와 개발할 때 필요한 판단 절차와 검사를 제공하는 Claude Code 플러그인 모음이다.
활성화된 프로젝트에서 일반적인 개발 요청에 맞춰 Skill이 선택되고 필요한 자료를 참조한다.

| 플러그인 | 하는 일 |
|---|---|
| [techjudge](plugin/techjudge/skills/tech-judgment/SKILL.md) | 현재 기능에 맞는 기술 후보를 발견하고 비교·적용·검증으로 연결한다. 주니어 개발자의 학습도 도입 이유로 다룬다. |
| [harness](plugin/harness/skills/harness-engineering/SKILL.md) | AI의 반복 실수와 실행 환경을 진단하고 지침·도구·훅·피드백·평가를 설계한다. |
| [kowrite](plugin/kowrite/README.md) | 한국어 문서·주석·커밋 규칙과 문서·코드의 연결을 훅으로 검사한다. |

세 플러그인은 독립적으로 선택할 수 있다.
Skill은 구현되어 있지만, 다양한 프로젝트에서 기본 모델보다 효과적인지는 별도 행동 평가가 필요하다.

## 사용하는 방식

사용자는 평소처럼 개발을 요청한다.
예를 들어 파일 변환 기능을 만들면 `techjudge`가 작업 분배·재처리의 적용 기회를 찾고 관련 기술을 비교한다.
선택한 기술의 종료·재시도 동작은 실제 코드와 테스트로 확인한다.
AI가 테스트 실패를 반복해서 무시한다면 `harness`가 실패 기록과 실행 흐름을 읽고 필요한 피드백이나 검사 위치를 검토한다.

기술 카드 선택이나 별도 학습 과제 준비는 사용자의 선행 작업이 아니다.
작은 규모에서도 기술을 경험할 수 있으며, 기존 선택과 프로젝트 제약을 존중한다.
사용자는 선택 이유, 추가 부담, 바뀐 코드와 검증 결과를 개발 대화에서 확인한다.
학습·포트폴리오 프로젝트에서는 구현과 재현 방법, 검증 결과를 남겨 기술을 적용하고 설명할 수 있는 근거로 쌓는다.
명시 호출 없이도 선택될 수 있지만, 설치만으로 모든 요청에서의 발동을 보장하지는 않는다.

## 설치

이 저장소를 받은 뒤 Claude Code에서 마켓플레이스를 추가한다.
아래 절대 경로는 실제로 받은 위치로 바꾼다.

```text
/plugin marketplace add /absolute/path/to/tackroom
/plugin install techjudge@tackroom
/plugin install harness@tackroom
/plugin install kowrite@tackroom
```

필요한 플러그인만 설치하고 적용 범위를 선택한다.
사용자 범위는 여러 프로젝트에, 프로젝트 공유 범위는 해당 리포지터리에, 로컬 범위는 해당 리포지터리에서 자신에게 적용한다.
범위와 설치 상태는 호스트의 플러그인 관리 화면에서 확인한다.

직접 호출해서 점검할 수도 있다.

```text
/techjudge:tech-judgment
/harness:harness-engineering
```

## 자료와 기여

- [기술 카드](docs/stacks/README.md): 원리·적용 조건·반례·검증 방법.
- [하네스 엔지니어링](docs/harness-engineering.md): 다양한 프로젝트에서 AI 작업 환경을 개선할 때의 판단 기준.
- [스킬 구조와 검증](docs/skill-strategy.md): 두 Skill의 역할, 배포 참조와 평가 설계.

공개하는 자산은 판단 절차, 기술 근거와 재현 가능한 검증 사례다.
기여할 때는 설명을 뒷받침하는 출처·버전이나, 요청·환경·예상과 실제 결과를 함께 남긴다.
기술 요약의 양과 설치 수만으로 효과를 주장하지 않는다.
사용·수정·배포 조건은 [LICENSE](LICENSE)에 있다.

## 개발과 검사

Python 3.8 이상을 사용한다. kowrite의 통합 테스트에는 Git과 Bash가 필요하며 Windows에서는 Git Bash를 사용한다.
`docs/`를 수정한 뒤 배포 참조를 동기화한다.

```text
python scripts/sync_references.py
python scripts/sync_references.py --check
python -m unittest discover -s tests
claude plugin validate .
claude plugin validate plugin/techjudge
claude plugin validate plugin/harness
claude plugin validate plugin/kowrite
```

패키지 검사는 참조의 존재·동기화·이동 가능성을 확인한다.
기술 주장의 사실 확인과 모델 행동 평가는 별도의 검증이다.

| 테스트 | 확인하는 것 |
|---|---|
| `test_plugins.py` | 독립 패키지의 참조 링크, 원본·배포본 동기화, 마켓플레이스 경로 |
| `test_stacks.py` | 기술 카드의 목록·필수 절·작성 형식 |
| `test_rules.py` | 한국어 문장·커밋·상수 연결 규칙 |
| `test_state.py` | 훅의 세션 상태와 변경 추적 |
| `test_regressions.py` | 실제 발견한 실패의 재현과 재발 방지 |
| `test_metrics.py` | 문서·주석 표본에서 검사기의 오탐과 탐지율 |
