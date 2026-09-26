# Harness Engineering

## I. 왜 필요한가

### 1. model에서 agent까지

- model은 입력을 받아 출력만 생성한다.
- agent task는 환경을 관찰하고 행동해야 끝난다.
- harness는 도구 실행, 상태, context, 권한, 반복, 복구를 맡는 실행 계층이다.
- 같은 model도 harness 설계에 따라 성공과 실패 양상이 달라진다.
- harness engineering은 harness를 측정하고 바꾸며, 불필요해진 부분을 걷어내는 활동이다.

#### 1.1 harness가 결과를 바꾼다는 근거

- `[C-12]` model을 고정하고 harness만 바꿔도 결과가 크게 달라질 수 있다.
  - LangChain은 GPT-5.2-Codex를 고정한 채 Terminal Bench 2.0 점수를 52.8%에서 66.5%로 올렸다.
  - 바꾼 것은 system prompt, tool, middleware뿐이다.
  - 주요 변경은 자체 검증 강제, 환경 정보와 시간 예산 주입, 반복 수정 감지, reasoning 예산 배분이다.
  - vendor 자체 보고이고 benchmark도 하나라서 개선 폭은 일반화하지 않는다.
- 반대 방향 근거도 있다.
  - `[C-11]` tool, skill, agent를 추가하기만 해도 전에 풀던 task의 성능이 떨어질 수 있다.
  - `[C-10]` repository context file은 성공률을 대체로 높이지 못하면서 비용을 늘렸다.
- harness는 많을수록 좋은 것이 아니라, 효과를 측정해야 하는 설계 대상이다.

#### 1.2 용어

- `[C-01]` 아래 harness와 agent 정의는 여러 공식 문서와 연구를 종합한 것이다.
- **model**: 학습된 model과 추론 능력이다. 지속 상태, tool 실행, repository 환경은 포함하지 않는다.
  - API 제품 전체를 가리키는 말이 아니다.
- **agent**: 목표를 받아 여러 단계에 걸쳐 행동을 고르고, feedback을 이용해 task를 수행하는 system이다.
  - Anthropic은 model이 절차와 tool 사용을 스스로 정하는지로 agent와 workflow를 구분한다.
- **harness**: model 호출과 tool call을 잇는 loop를 중심으로 context, 상태, 안전장치, 조율, 확장 지점을 제공하는 실행 계층이다.
  - 범위는 vendor마다 다르다. Anthropic Managed Agents는 session, harness, sandbox를 따로 둔다.
- **harness engineering**: harness의 구성과 interface를 설계하고 측정하고 바꿔서 성공률, 안전, 비용, 지연, 운영성을 개선하는 활동이다.
- `[C-02]` `Agent = Model + Harness`는 쓸모 있는 분해지만 표준 정의는 아니다.
  - 최근 소스코드 연구와 실무 문헌이 이 식을 쓴다.
  - vendor 문서는 agent, harness, sandbox, session을 목적에 따라 다르게 나눈다.
  - 이 문서는 분석 모델로만 쓴다.

#### 1.3 harness가 갖춰야 할 네 가지

- `[C-03]` 목적은 지시를 더 얹는 것이 아니라 다음 네 가지를 갖추는 것이다.
  - **읽을 수 있게**: agent가 repository, UI, 로그, metric, 도메인 규칙에 접근해 해석할 수 있게 한다.
  - **실행할 수 있게**: tool, sandbox, credential 경계, 환경 설정으로 행동을 수행할 수 있게 한다.
  - **제한할 수 있게**: 권한, 정책, 승인, 보호된 전이, 실행 상한으로 행동 범위를 좁힌다.
  - **검증할 수 있게**: test, 정적 분석, 상태 확인, grader, eval로 결과와 regression을 측정한다.

### 2. harness의 구성

- harness는 instruction file 하나가 아니다.
- Barbaste et al.은 운영 중인 coding harness 11개의 소스코드를 분석해 반복되는 구성을 일곱 subsystem으로 정리했다.
- 현황을 설명하는 분류이지 규격은 아니다.
  - **agent loop**: model 호출, tool 호출, 관찰, 중단, 재시도를 맡는다.
  - **LLM integration**: provider API, prompt 조립, 응답 파싱, model 선택을 맡는다.
  - **tools & actions**: shell, 파일 편집, 검색, browser, MCP, 결과 정규화를 맡는다.
  - **memory & context**: session 기록, compaction, 검색, repository instruction을 맡는다.
  - **safety & permissions**: 승인, sandbox, 정책, credential 격리를 맡는다.
  - **orchestration**: subagent, 계획, 스케줄링, worktree, 복구를 맡는다.
  - **extensibility**: skill, plugin, hook, MCP, 설정을 맡는다.

#### 2.1 누가 무엇을 바꿀 수 있는가

- **model provider**는 weights, 추론 서비스, model 수준 정책을 바꾼다.
- **agent runtime**에서는 agent loop, tool protocol, 기본 context 관리, 기본 권한을 바꾼다.
- **프로젝트 harness**에서는 repository instruction, skill, 프로젝트 tool, hook, 권한 규칙, 작업 상태를 바꾼다.
- **배포 환경**에서는 pre-commit, CI, required check, 배포 정책, 운영 모니터링을 바꾼다.
- 네 영역은 포함 관계가 아니라 변경 권한으로 나눈 것이다.
- closed product를 쓰는 팀은 주로 프로젝트 harness와 배포 환경을 수정한다.
- SDK나 open-source runtime을 쓰는 팀은 agent runtime까지 수정할 수 있다.
- 이 경계는 제품과 조직에 따라 달라진다.

---

## II. 통제

### 3. control의 역할과 판단의 흐름

- control은 파일이나 tool 이름이 아니라 특정 시점에 하는 역할로 분류한다.
- 같은 test도 편집 직후에는 Sensor이고, required check로 걸리면 Gate가 된다.
- 역할을 나누는 이유는 보장 수준을 정확히 말하기 위해서다.
  - local hook은 우회할 수 있다.
  - loop 안의 test는 agent가 결과를 무시할 수 있다.
  - merge를 실제로 막는 것은 required check뿐이다.
- 역할은 네 가지로 나눈다.
  - **Guide**: 행동 전에 정보나 지시를 주어 선택을 유도한다. 강제하지는 않는다. `AGENTS.md`, skill, 예시가 여기에 속한다.
  - **Gate**: 보호할 전이 직전에 허용 여부를 결정한다. 권한 거부, required CI check, 실행 상한이 여기에 속한다. `[C-04]`
  - **Sensor**: 상태, 행동, 결과를 관찰해 판정 근거를 만든다. test, linter, trace, 보안 스캔이 여기에 속한다.
  - **Transformer**: 산출물이나 상태를 직접 바꾼다. formatter, codemod, 생성 파일, checkpoint 기록이 여기에 속한다.
- Guide와 Sensor는 Böckeler의 분류에서 가져왔다.
- Gate와 Transformer를 따로 나눈 것은 이 문서의 분석용 구분이며 표준 분류는 아니다.

#### 3.1 실행 중 통제와 개선의 관계

| 단계 | 흐름 |
|---|---|
| 행동 준비 | Guide → agent → Gate → effect |
| 작업 중 확인 | Sensor → verification → agent feedback |
| 개선 주기 | 사람의 개입 → eval → harness 변경 |

- **행동 준비**
  - Guide가 규칙과 예시를 context에 넣는다.
  - agent가 행동을 제안한다.
  - Gate가 전이 직전에 허용 여부를 정한다.
  - 허용된 경우에만 상태가 바뀐다.
- **작업 중 확인**
  - Sensor가 바뀐 상태와 행동, 결과를 수집한다.
  - verification이 test나 model-based grader로 기준을 만족하는지 판단한다.
  - 판단 결과는 agent의 다음 행동에 반영된다.
- **개선 주기**
  - 사람이 승인, 수정, 거부하고 그 이유를 남긴다.
  - eval이 이 신호로 case와 grader를 보정하고 반복 측정한다.
  - 측정 결과에 따라 Guide, Sensor, Gate를 조정한다.
- 판정과 사람의 개입은 재현 가능한 신호로 기록해야 개선 주기로 넘길 수 있다.
- Gate는 보호할 전이에만 둔다.
- verification은 개별 결과를 보고, eval은 여러 작업과 시행을 비교한다.
- 사람의 개입은 검토할 신호일 뿐 자동으로 정답이 되지는 않는다.
- 같은 도구도 위치에 따라 역할이 달라진다.
  - `ruff check`는 편집 직후 위반을 관찰해 결과를 돌려주므로 Sensor다.
  - `ruff format`은 편집 직후 파일을 직접 바꾸므로 Transformer다.
  - agent loop 안의 `pytest`는 결과가 다음 행동으로 이어지므로 Sensor다.
  - required merge check로 걸린 `pytest`는 merge를 막으므로 Gate다.
  - `AGENTS.md`는 지시하지만 준수를 강제하지 않으므로 Guide다.

### 4. 판정 방식과 보장 수준

- `[C-05]` code-based와 model-based는 판정 방식이고, Guide, Gate, Sensor, Transformer는 역할이다.
- 둘은 다른 축이므로 한 분류에 섞지 않는다.
- 빠르다거나 결정적이라는 성질은 경향일 뿐 정의 조건이 아니다.
- **code-based** 판정은 명시된 조건이나 프로그램을 실행해 판단한다.
  - schema 검증, unit test, 정적 분석, 상태 확인이 여기에 속한다.
  - 재현성이 높지만, 예상하지 못한 유효한 변형에는 약할 수 있다.
- **model-based** 판정은 model 추론으로 rubric이나 자연어 기준을 판단한다.
  - code review, UI 품질 평가, 문서 일관성 검토가 여기에 속한다.
  - 의미를 다룰 수 있지만 보정, 편차, 비용 문제가 따른다.

#### 4.1 보장 수준은 실패의 영향에 맞춘다

- **credential 노출, 운영 데이터 삭제**에는 credential 격리, sandbox, 명시적 거부, 감사 Sensor를 함께 둔다.
  - 분류기나 지시 하나가 빠지는 것도 허용하기 어렵기 때문이다.
- **형식, schema, 의존성 규칙**에는 code-based Sensor를 두고, 필요하면 Gate로 올린다.
  - 조건으로 표현할 수 있고 오류 메시지를 구체적으로 만들 수 있기 때문이다.
- **아키텍처 적합성, UX 품질**에는 model-based grader를 쓰고 사람의 보정과 표본 검사를 더한다.
  - 열린 기준이라 고정된 조건만으로 판단하기 어렵기 때문이다.
- **자동 formatting**은 Transformer로 고치고 diff를 확인한다.
  - 교정과 판정을 나누고 변경 내용을 볼 수 있어야 하기 때문이다.
- Anthropic eval 가이드도 grader를 code-based, model-based, human으로 나누고, model-based grader를 사람 판단에 맞춰 보정하라고 권한다.

### 5. 배치 위치

- `[C-06]` control은 판정에 필요한 정보가 생긴 뒤, 보호할 전이가 일어나기 전에 둔다.
- 싸고 feedback이 구체적인 검사는 agent loop 가까이에 둔다.
- 환경 통합이 필요한 검사는 CI나 배포 단계에 둔다.

| 시점 | 역할 |
|---|---|
| context | Guide |
| tool 실행 전 | Gate |
| tool 실행 | — |
| tool 실행 후 | Sensor, Transformer |
| commit | Sensor |
| merge·배포 | Gate |
| 운영 | Sensor |

- 시점별로 두는 control은 다음과 같다.
  - context에는 repository instruction, skill, task 명세, checkpoint 복원을 둔다.
  - tool 실행 전에는 권한 규칙, `PreToolUse`, 승인, 상한 확인을 둔다.
  - tool 실행 단계에서는 편집, shell, API 호출이 실제로 일어난다.
  - tool 실행 후에는 `PostToolUse`, formatter, 빠른 lint와 test, checkpoint 기록을 둔다.
  - commit에는 pre-commit, secret 스캔, 계약 검사를 둔다.
  - merge와 배포에는 CI, required check, 배포 승인을 둔다.
  - 운영 중에는 로그, metric, canary, rollback 신호를 본다.
- 특정 제품의 이벤트 목록은 아니다.
- Claude Code의 `PreToolUse`는 tool 호출 전에 실행되어 호출을 막을 수 있다.
- `PostToolUse`는 성공한 호출 뒤에 실행된다.
- local pre-commit은 우회할 수 있으므로 Sensor로 분류한다.
- 이미 실행된 행동은 `PostToolUse`로 되돌릴 수 없다.
  - `PostToolUse`는 관찰과 후속 수정에만 쓴다.
  - 위험한 행동은 `PreToolUse`, 권한, sandbox, credential 경계에서 막는다.
- 배치를 정할 때는 다음을 판단한다.
  - **무엇을 보호하는가**: 파일 쓰기, shell 실행, commit, merge, 배포처럼 전이를 명시한다.
  - **판정 정보는 언제 생기는가**: tool 인자가 필요하면 tool 요청 이후, 실행 이전에 둔다.
  - **실패는 누가 고치는가**: agent가 고친다면 짧고 구조화된 결과를 loop로 돌려준다. 사람이 고친다면 원인 정보와 담당자를 남긴다.
  - **control 자체가 실패하면 어떻게 하는가**: timeout, crash, 경로 불일치, 서비스 장애 때 통과시킬지 막을지 미리 정한다.

---

## III. 운영

### 6. 긴 작업을 돌릴 때

- 긴 작업에서는 개별 검사 말고도 따로 챙길 책임이 생긴다.
- 실행 제한, 작업 재개, 입력의 신뢰 구분, 비용과 이상 징후 관찰이 여기에 해당한다.

#### 실행 상한

- agent loop subsystem이 맡는다.
- 다음 호출을 막는 상한은 Gate이고, 반복 감지는 Sensor다.
- 반복 횟수, 실행 시간, token, 비용, tool 호출 수에 상한을 둔다.
- 상한에 닿으면 산출물, 끝낸 단계, 남은 문제, 멈춘 이유를 돌려준다.
- 부분 실패를 완료처럼 보이게 하지 않는다.
- 같은 수정과 같은 오류가 반복되면 따로 감지한다.

#### 상태와 복구

- memory & context, orchestration subsystem이 맡는다.
- 기록은 Transformer, 복원은 Guide가 한다.
- 계획, 진행 상태, 결정 기록을 session 밖에 남긴다.
- 재시작할 때 이 기록을 읽어 이어간다.
- 중간에 session을 끊었다 다시 열어도 끝낸 일을 반복하지 않으면 제대로 된 것이다.
- 오래된 checkpoint는 만료시킨다.

#### 신뢰 경계

- safety & permissions subsystem이 맡는다.
- 주로 Gate가 막고, 문구는 보조 Guide로만 쓴다.
- repository instruction과 system prompt는 따를 지시로 본다.
- 웹 페이지, 이슈, 외부 문서, tool 출력은 데이터로 본다.
- 데이터 속 지시가 권한을 넓히거나, secret을 옮기거나, 외부 effect를 일으키지 못하게 한다.
- "외부 지시를 따르지 말라"는 문구는 Guide일 뿐이므로 권한과 sandbox로 함께 막는다.

#### 관찰과 비용

- 모든 subsystem에 걸친다.
- 주로 Sensor이며, 경보가 실행을 멈추면 Gate가 된다.
- tool 호출, 판정, 재시도, 승인, escalation을 trace로 남긴다.
- 그러면 재실행 없이 실패 지점을 추적할 수 있다.
- 비용은 하루 총액이 아니라 검증을 통과한 결과 하나당 비용으로 본다.
- 같은 오류의 반복, 비용 급증, 처음 보는 외부 도메인 접근에는 경보를 건다.

- `[C-13]` 실행 상한, escalation, 복구는 model이 아니라 harness가 맡는다.
- `[C-14]` 지시와 데이터의 분리는 문구가 아니라 권한 경계로 구현한다.

#### 6.1 escalation

- 상한에 닿았거나 사람의 판단이 필요한 지점에서 escalation하는 것은 정상 동작이다.
- 담당자가 바로 결정할 수 있도록 다음을 함께 넘긴다.
  - 결정해야 할 사항을 적는다.
  - 권장안을 제시한다.
  - 이미 시도한 대안을 밝힌다.
  - 기다리는 동안 드는 비용을 알린다.
  - 응답이 없을 때의 안전한 기본 동작을 정해 둔다.

#### 6.2 상한 값은 trace로 정한다

- "재시도 3회"나 "30분" 같은 고정 기본값은 쓰지 않는다.
- 적정 상한은 작업 길이, 한 번 시도하는 비용, 외부 effect 여부에 따라 다르다.
- 관찰한 분포로 정하고 그 근거를 기록한다.
- **단계당 재시도**는 n번째 재시도의 성공 비율과 재시도 1회 비용을 보고 정한다.
  - 너무 낮으면 고칠 수 있는 실패를 포기한다.
  - 너무 높으면 같은 실패에 비용을 계속 쓴다.
- **실행 시간**은 정상 완료 작업의 소요 시간 분포를 보고 정한다.
  - 너무 낮으면 정상적인 긴 작업이 끊긴다.
  - 너무 높으면 멈춘 agent를 늦게 발견한다.
- **token과 비용**은 검증 통과 결과당 비용과 작업의 가치를 보고 정한다.
  - 너무 낮으면 품질이 떨어진다.
  - 너무 높으면 폭주하는 loop를 막지 못한다.
- **tool 호출 수**는 작업 유형별 정상 호출 수를 보고 정한다.
  - 너무 낮으면 탐색이 필요한 작업을 막는다.
  - 너무 높으면 도구 남용을 늦게 발견한다.

---

## IV. 측정과 변경

### 7. verification과 eval

- verification과 eval은 결과를 누가 받는지가 아니라 절차로 구분한다.
- model-based verification은 Sensor가 모은 산출물, 상태, trace를 rubric에 비춰 판정한다.
- 그 판정은 agent의 다음 행동이나 Gate의 허용 판단에 쓰일 수 있다.
- model의 판정만으로 강제력이 생기지는 않는다.
- 사람의 승인, 수정, 거부와 그 이유는 실패 case를 찾고 grader를 보정하는 신호가 된다.
- 이 신호를 검토해 eval에 반영한 뒤 변경 전후를 비교한다.
- `[C-07]` 용어는 Anthropic eval 가이드를 따른다.
  - **verification**: 산출물, 상태, 행동, 주장이 기준을 만족하는지 확인하는 작업이다. test 실행, API 상태 확인, schema 검증이 여기에 속한다.
  - **grader**: 결과나 transcript에 점수나 판정을 매기는 로직이다. unit test, 정적 분석기, LLM rubric, 사람 리뷰가 여기에 속한다.
  - **eval**: AI system에 task를 주고 grader로 성공과 행동을 측정하는 절차다. task, 시행 횟수, grader, 지표를 조합해 구성한다.
  - **evaluation harness**: task를 실행하고 trace와 결과를 기록하며 채점과 집계를 맡는 인프라다. benchmark runner, regression suite runner가 여기에 속한다.
  - **agent harness**: model이 입력을 처리하고 tool을 호출해 결과를 돌려주게 하는 runtime이다. Claude Code, Codex CLI, 자체 agent runtime이 여기에 속한다.
- 같은 test도 맥락에 따라 다르게 쓰인다.
  - 작업 중에는 `pytest` 결과가 agent의 다음 편집을 이끄는 Sensor다.
  - eval 안에서는 같은 test가 각 시행을 채점하는 code-based grader다.

#### 7.1 model-based grader는 보정이 핵심이다

- `[C-08]` LLM 평가자가 자기가 만든 결과를 더 높게 평가하는 경향이 실험으로 확인됐다.
- 생성자와 평가자의 context를 나누는 방법이 쓰이지만, 이 실험이 그 효과를 보인 것은 아니다.
- rubric을 명시하고, 사람이 판정한 표본과 맞춰 보고, 불일치를 추적한다.
- 운영 원칙은 다음과 같다.
  - agent의 완료 선언보다 환경의 실제 상태를 확인한다.
  - 객관적인 조건이 있으면 code-based grader부터 쓴다.
  - model-based 점수와 전문가 판단이 얼마나 일치하는지 주기적으로 확인한다.
  - 확률적인 동작을 한 번의 실행으로 일반화하지 않는다.

### 8. 추가·변경·제거

- `[C-09]` harness는 쌓기만 하는 대상이 아니다.
- 실패가 생기면 재현 case와 후보 수정을 만든다.
- model, 작업, 환경이 바뀌면 ablation과 regression eval을 거쳐 control을 약화하거나 제거한다.
- 변경은 다음 순서로 진행한다.
  1. **관찰**: 실패, 비용, 지연, trace를 수집한다.
  2. **재현**: 재현 가능한 task나 regression case를 만든다.
  3. **진단**: model, tool, context, 정책, 환경 중 어디가 원인인지 가려낸다.
  4. **변경**: 필요한 범위에만 control을 추가하거나 수정한다.
  5. **평가**: 성공률, regression, 비용, 지연을 비교한다.
  6. **유지·제거**: 효과가 있으면 유지하고 없으면 되돌린다.

#### 8.1 실패 하나에 장치 하나는 경험칙이다

- Hashimoto의 실패 주도 원칙은 재발을 막으려는 태도를 설명한다.
- 실제로는 실패 하나에 control이 여러 개 필요하기도 하고, control 하나가 여러 실패를 줄이기도 한다.
- 예를 들어 credential 노출은 credential 격리, 거부 정책, sandbox, secret 스캔을 함께 요구한다.
- model이 바뀐 뒤에는 기존 우회책이 부담만 남길 수 있다.

#### 8.2 instruction file은 짧게 쓴다

- `[C-10]` Gloaguen et al.의 실험에서 repository context file은 성공률을 대체로 높이지 못했고 추론 비용을 평균 20% 넘게 늘렸다.
- 같은 연구는 표준에서 벗어난 코딩 관행을 알릴 때는 context file이 유용하다고 본다.
- OpenAI는 긴 `AGENTS.md` 하나로 시도했다가 실패한 뒤, 약 100줄짜리 목차와 구조화된 `docs/`로 옮겼다.

#### 8.3 구성요소가 많다고 나은 것은 아니다

- `[C-11]` EvoHarnessBench는 tool, skill, agent를 추가하기만 해도 전에 풀던 task의 성능이 떨어지는 현상을 보고했다.
- Harness-Bench와 The Scaffold Effect는 harness와 model의 조합이 완료율, 실패 양상, token 비용, 지연에 영향을 준다고 보고했다.
- 다만 모든 비교에서 성공률 차이가 큰 것은 아니다.

#### 8.4 harness는 잘못된 목표를 고치지 않는다

- 수용 기준이 틀리면 Sensor와 Gate는 틀린 결과를 그대로 통과시킨다.
- control을 붙이기 전에 무엇이 성공인지 검증 가능한 기준으로 적는다.
- grader도 확실히 맞는 표본과 틀린 표본으로 먼저 확인한다.
- 변경할 때는 다음을 기록하고 비교한다.
  - **대상과 조건**: 대상 실패, task 집합, model, harness 버전, 환경, 상한을 적는다. 변경 후에는 성공률, regression, token, 지연, tool 오류, 사람 개입을 비교해 유지, 수정, 범위 축소, 제거 중 하나를 고른다.
  - **기대 효과**: 기대한 작동 방식과 예상 개선 폭을 적는다. 실제 trace에서 기대대로 작동하지 않았다면, 즉 원인 설명이 틀렸다면 변경을 유지하지 않는다.
  - **담당과 만료**: control의 담당자와 만료 조건을 적는다. model 교체, tool 변경, 작업 분포 변화가 생기면 한 번에 한 구성요소씩 ablation한다.

---

## V. 적용

### 9. 설계 절차

#### 9.1 이 작업에 harness 변경이 필요한가

- 모든 작업에 무거운 control이 필요한 것은 아니다.
- 아래 질문에 하나도 해당하지 않는 일회성·탐색성 작업이라면 기본 설정 이상의 변경은 비용만 늘린다.
  - agent가 조용히 틀린 결과를 낼 때 알아채야 한다면 Sensor나 grader를 둔다. (3장, 7장)
  - 다음 session에서 상태나 맥락을 이어야 한다면 상태와 복구를 설계한다. (6장)
  - 실수 하나가 배포, 외부 발송, 삭제 같은 외부 effect를 만든다면 Gate, 권한, sandbox를 둔다. (3장, 5장)
  - 같은 작업이 반복된다면 재현 case와 eval을 만든다. (8장)
  - 사람 없이 오래 실행된다면 실행 상한과 관찰을 둔다. (6장)

#### 9.2 control을 추가할 때

- 분류보다 실패와 보호할 전이를 먼저 구체화한다.
- 아래 질문에 답하지 못하면 control을 추가하지 않는다.
  1. **실패는 무엇인가**: 관찰한 결과와 기대한 결과를 나눠 적는다.
  2. **재현되는가**: task, 초기 상태, 환경, model, 상한을 고정한다.
  3. **원인은 어느 subsystem인가**: model, context, tool, 상태, 권한, 조율, 환경 중 하나 이상을 지목한다.
  4. **무엇을 보호하거나 측정하는가**: 산출물, 상태, 행동, 전이, 동작 중 무엇인지 적는다.
  5. **어떤 역할이 필요한가**: Guide, Gate, Sensor, Transformer 중 실제 효과를 기준으로 고른다.
  6. **어떻게 판정하는가**: code-based, model-based, 사람 중 기준에 맞는 방식을 고른다.
  7. **어디에 두는가**: 필요한 정보가 생긴 뒤이면서 보호할 전이 이전인 지점을 찾는다.
  8. **실패하면 무엇을 돌려주는가**: 판정, 근거, 수정 방법, 담당, 재시도 정책을 정한다.
  9. **효과를 어떻게 비교하는가**: 기준선, 반복 시행, 성공률, 비용, 지연, regression 지표를 정한다.
  10. **언제 제거하는가**: 담당자, 점검 시점, model이나 tool 변경 조건, ablation 방법을 적어 둔다.

---

## 부록 A. 주장과 근거

- 본문의 `[C-xx]` 표시는 아래 항목과 이어진다.
- 공식 문서는 제품 동작의 근거일 뿐 효과를 증명하지 않는다.
- 사례는 해당 환경의 기록일 뿐 인과를 입증하지 않는다.
- "이 문서의 구분"은 참고 자료를 바탕으로 이 문서가 세운 분류라는 뜻이다.

**C-01** harness는 model과 환경을 잇는 runtime과 설정이다.
- 근거는 Anthropic eval 가이드, Managed Agents, Barbaste et al.이다.
- 공식 문서와 연구(preprint)를 이 문서가 종합했다.
- vendor마다 session, sandbox, tool을 harness 안팎에 다르게 둔다는 한계가 있다.

**C-02** `Agent = Model + Harness`는 분석용 분해다.
- 근거는 Barbaste et al. 초록의 첫 문장과 LangChain 등의 실무 용례다.
- 연구(preprint)와 실무 용례에 기댄 주장이다.
- Anthropic은 자율성으로 agent를 정의하고, Managed Agents는 구성요소를 더 잘게 나눈다.

**C-03** harness engineering은 읽기, 실행, 제한, 검증을 설계한다.
- 근거는 OpenAI 사례와 Barbaste et al.의 7개 subsystem 분석이다.
- 공식 사례와 연구(preprint)를 이 문서가 종합했다.
- OpenAI 사례는 특정 조직과 신규 제품의 조건이며, 원문도 일반화를 경계한다.

**C-04** Gate는 보호할 전이 직전에 허용 여부를 결정한다.
- 근거는 Claude Code `PreToolUse` 명세와 required check의 동작이다.
- 제품 명세를 바탕으로 한 이 문서의 구분이다.
- Gate가 누락되거나 timeout, 장애가 나면 위반이 통과할 수 있다.

**C-05** 역할과 판정 방식은 다른 축이다.
- 근거는 Böckeler의 분류와 Anthropic grader 분류의 비교다.
- 이 문서의 구분이며 표준 분류가 아니다.

**C-06** control은 정보가 생긴 뒤, 전이 전에 둔다.
- 근거는 Claude Code hook 명세다.
- 제품 명세를 바탕으로 한 이 문서의 구분이다.
- 제품마다 이벤트와 CI 구성이 다르다.

**C-07** eval은 절차로 정의한다.
- 근거는 Anthropic eval 가이드다.
- 조직마다 verification, test, eval의 범위를 다르게 쓴다.

**C-08** LLM 평가자는 자기 결과를 선호하므로 보정이 필요하다.
- 근거는 Panickssery et al.(peer-reviewed)과 Anthropic의 보정 권고다.
- 권고 부분은 이 문서가 종합했다.
- 편향의 크기와 방향은 model, 작업, prompt에 따라 다르다.
- context 분리의 효과는 이 실험이 직접 보이지 않았다.

**C-09** harness 변경에는 제거도 포함된다.
- 근거는 Anthropic Managed Agents의 낡은 가정 사례다.
- 공식 사례를 이 문서가 종합했다.
- 구성요소끼리 상호작용하므로 하나씩 ablation해야 한다.

**C-10** repository instruction은 최소 요구사항과 안내에 집중한다.
- 근거는 Gloaguen et al.(preprint)과 OpenAI의 짧은 목차 및 `docs/` 구조다.
- 실험한 task와 agent에 한정된 결과다.
- 같은 연구에는 비표준 관행을 알리는 데 유용하다는 결과도 있다.

**C-11** harness 확장은 regression을 일으킬 수 있다.
- 근거는 EvoHarnessBench와 Harness-Bench(모두 preprint)다.
- 실제 운영 환경으로 일반화하려면 추가 검증이 필요하다.

**C-12** model을 고정하고 harness만 바꿔도 결과가 크게 달라질 수 있다.
- 근거는 LangChain 사례다. GPT-5.2-Codex를 고정하고 Terminal Bench 2.0에서 52.8%를 66.5%로 올렸다.
- vendor가 자체 보고한 실무 사례다.
- 자사 agent와 단일 benchmark 결과이므로 개선 폭을 일반화할 수 없다.

**C-13** 실행 상한, escalation, 복구는 harness가 맡는다.
- 근거는 Barbaste et al.의 agent loop와 orchestration 구성, LangChain의 loop 감지 middleware다.
- 연구(preprint)와 실무 사례를 이 문서가 종합했다.
- 구체적인 상한과 복구 방식은 작업과 runtime에 따라 다르다.

**C-14** 지시와 데이터의 분리는 권한 경계로 구현한다.
- 근거는 Claude Code의 권한 규칙과 sandbox 동작이다.
- 제품 명세를 이 문서가 종합했다.
- 허용된 범위 안의 오용은 막지 못한다. prompt injection을 완전히 막는다는 주장이 아니다.

## 부록 B. 참고 자료

### 공식 문서

- [Anthropic, "Demystifying evals for AI agents" (2026-01-09)](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Anthropic, "Building effective agents"](https://www.anthropic.com/engineering/building-effective-agents)
- [Anthropic, "Scaling Managed Agents: Decoupling the brain from the hands" (2026-04-08)](https://www.anthropic.com/engineering/managed-agents)
- [Claude Code Docs, "Hooks reference"](https://code.claude.com/docs/en/hooks)
- [Claude Code Docs, "How Claude remembers your project"](https://code.claude.com/docs/en/memory)
- [Claude Code Docs, "Configure permissions"](https://code.claude.com/docs/en/permissions)
- [OpenAI, "Harness engineering: leveraging Codex in an agent-first world" (2026-02-11)](https://openai.com/index/harness-engineering/)

### 연구

- [Barbaste, Darrigol, Vu & Wiltberger, "Harness Engineering: Anatomy, Architecture, and Evolution of Coding Agents", arXiv:2609.00006 (2026, preprint)](https://arxiv.org/abs/2609.00006)
- [Yao et al., "Harness-Bench", arXiv:2605.27922 (2026, preprint)](https://arxiv.org/abs/2605.27922)
- [Vats & Golev, "The Scaffold Effect in Coding Agents", arXiv:2607.22585 (2026, preprint)](https://arxiv.org/abs/2607.22585)
- [Ke et al., "EvoHarnessBench", arXiv:2609.04280 (2026, preprint)](https://arxiv.org/abs/2609.04280)
- [Gloaguen et al., "Evaluating AGENTS.md", arXiv:2602.11988 (2026, preprint)](https://arxiv.org/abs/2602.11988)
- [Panickssery, Bowman & Feng, "LLM Evaluators Recognize and Favor Their Own Generations", NeurIPS 2024](https://arxiv.org/abs/2404.13076)

### 실무 문헌

- [LangChain, "Improving Deep Agents with harness engineering" (2026-02-17)](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering)
- [Mitchell Hashimoto, "My AI Adoption Journey" (2026-02-05)](https://mitchellh.com/writing/my-ai-adoption-journey)
- [Birgitta Böckeler, "Harness engineering for coding agent users" (martinfowler.com)](https://martinfowler.com/articles/harness-engineering.html)