# 하네스 엔지니어링

2026-09-26에 확인한 내용이다. Claude Code의 훅 이름과 동작은 버전마다 바뀔 수 있다.

## 정의

- **하네스**는 모델 호출과 도구 실행을 잇는 실행 계층이다. 컨텍스트, 도구, 권한, 상태, 검사, 반복 제어를 맡는다.
- **하네스 엔지니어링**은 하네스를 바꿔 성공률·안전·비용·지연을 개선하고, 효과를 측정하고, 쓸모없어진 부분을 걷어내는 일이다.
- 하네스는 많을수록 좋지 않다. 도구와 지침을 추가하기만 해도 성능이 떨어진 보고가 있다[^1]. 저장소 지침 파일은 성공률을 거의 올리지 못하면서 비용을 20% 넘게 늘렸다[^2].

## 역할

역할은 파일 종류가 아니라 언제 무엇을 하는지로 정한다. 같은 `pytest`도 편집 직후에 돌리면 Sensor이고, merge 조건으로 걸면 Gate다.

| 역할 | 하는 일 | 예 | 강제력 |
|---|---|---|---|
| **Guide** | 행동 전에 정보와 지시를 준다. | `CLAUDE.md`, 스킬, 예시 | 없다. 모델이 무시할 수 있다. |
| **Sensor** | 결과를 관찰해 피드백한다. | 테스트, 린터, `PostToolUse` 검사 | 없다. 에이전트가 결과를 무시할 수 있다. |
| **Gate** | 보호할 전이 직전에 막는다. | `PreToolUse` 거부, 권한 규칙, 필수 CI 검사 | 있다. 로컬 훅은 우회할 수 있다. |
| **Transformer** | 산출물을 직접 고친다. | 포매터, 코드 변환 도구 | 있다. 결과를 diff로 확인해야 한다. |

판정 방식은 역할과 별개의 축이다.

- 코드 판정은 조건으로 쓸 수 있는 기준에 먼저 쓴다. 싸고 재현된다.
- 모델 판정은 의미와 문체처럼 열린 기준에만 쓴다. 모델은 자기 결과를 더 좋게 평가하므로 사람 판정과 맞춰 보정한다[^3].
- 사람의 개입은 판정 신호로 쓴다. 자동으로 정답이 되지는 않는다.

## 배치

판정에 필요한 정보가 생긴 뒤, 보호할 전이가 일어나기 전에 둔다. 싸고 구체적인 검사일수록 에이전트 루프 가까이 둔다.

| 시점 | Claude Code 연결 | 둘 것 |
|---|---|---|
| 세션 시작 | `SessionStart`, `CLAUDE.md` | 짧은 Guide |
| 도구 실행 전 | `PreToolUse`, 권한 규칙 | 커밋·삭제·배포를 막는 Gate |
| 도구 실행 후 | `PostToolUse` | Sensor, Transformer |
| 응답 종료 전 | `Stop` | 완료 조건을 확인하는 Gate |
| 커밋 | git `pre-commit`, `commit-msg` | 로컬 Gate |
| merge·배포 | CI 필수 검사, 브랜치 보호 | 우회하기 어려운 Gate |

- `PostToolUse`는 이미 일어난 행동을 되돌리지 못한다. 위험한 행동은 `PreToolUse`나 권한에서 막는다.
- `Stop` 훅은 `stop_hook_active`를 확인해 반복 차단을 막는다.
- git 로컬 훅은 `--no-verify`로 우회된다. 로컬 차단을 원격 차단으로 취급하지 않는다.

## 상황별 확인

아래 상황에 해당하지 않으면 기본 설정을 그대로 쓴다.

| 상황 | 필요한 것 |
|---|---|
| 에이전트가 조용히 틀린 결과를 낸다. | Sensor 또는 채점기 |
| 실수 하나가 삭제·배포·외부 발송으로 이어진다. | Gate, 권한, 샌드박스 |
| 다음 세션이 작업을 이어받아야 한다. | 세션 밖 상태 기록과 복원 |
| 같은 작업이 반복된다. | 재현 사례와 평가 |
| 사람 없이 오래 실행된다. | 반복·시간·비용 상한, 반복 수정 감지 |
| 외부 문서나 도구 출력을 읽는다. | 데이터 취급 원칙과 권한 경계 |

## 장치를 추가하기 전에 답할 질문

1. 관찰한 결과와 기대한 결과는 각각 무엇인가?
2. 과제, 초기 상태, 모델, 설정을 고정하면 재현되는가?
3. 원인은 모델, 컨텍스트, 도구, 권한, 환경, 설정 중 어디에 있는가? 설정 한 줄로 끝나면 하네스를 만들지 않는다.
4. 강제가 필요한가? 필요하면 Guide로는 부족하다.
5. 코드로 판정할 수 있는가? 안 되면 모델, 그래도 안 되면 사람이 판정한다.
6. 필요한 정보가 생기고 전이가 일어나기 전의 어느 시점에 두는가?
7. 실패하면 위치, 근거, 고칠 방법을 짧게 돌려주는가?
8. 검사 자체가 실패하면 통과시키는가, 막는가?
9. 하네스 없는 조건과 같은 과제로 비교했는가? 모델명, 날짜, 버전을 남겼는가?
10. 어떤 조건에서 제거하는가? 모델이 바뀌면 다시 측정하고, 효과가 없으면 뺀다.

## 측정

- 검증은 결과 하나를 기준에 비춰 보는 일이다. 평가는 여러 과제와 시행을 조건별로 비교하는 일이다.
- 하네스 자체 검사를 통과했다고 정답으로 보지 않는다. 채점은 하네스와 분리한다.
- 확률적으로 동작하는 시스템을 한 번의 실행으로 일반화하지 않는다.
- 비용은 총액이 아니라 검증을 통과한 결과 하나당 비용으로 보고, 하네스가 쓰는 모델 비용도 포함한다.
- 모델을 고정하고 하네스만 바꿔도 결과가 크게 달라질 수 있다[^4]. 모델이 바뀌면 기존 하네스가 부담만 남길 수도 있다.

## 참고

[^1]: [Ke et al., "EvoHarnessBench", arXiv:2609.04280](https://arxiv.org/abs/2609.04280). [Yao et al., "Harness-Bench", arXiv:2605.27922](https://arxiv.org/abs/2605.27922).
[^2]: [Gloaguen et al., "Evaluating AGENTS.md", arXiv:2602.11988](https://arxiv.org/abs/2602.11988).
[^3]: [Panickssery et al., "LLM Evaluators Recognize and Favor Their Own Generations", NeurIPS 2024](https://arxiv.org/abs/2404.13076).
[^4]: [LangChain, "Improving Deep Agents with harness engineering", LangChain Blog](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering).

- [Anthropic, "Demystifying evals for AI agents", Anthropic Engineering](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Anthropic, "Hooks reference", Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [Birgitta Böckeler, "Harness engineering for coding agent users", martinfowler.com](https://martinfowler.com/articles/harness-engineering.html)
- [OpenAI, "Harness engineering", OpenAI](https://openai.com/index/harness-engineering/)
