# GitHub Actions

확인: 2026-09-27, github/docs 저장소(main)의 Actions 문서 기준.

## 요약

GitHub Actions는 저장소 사건(push, PR, 일정, 수동 실행)에 반응해 YAML로 정의한 작업을 러너에서 실행하는 CI/CD 서비스다.
빌드, 테스트, 이미지 생성, 배포를 코드로 정의해 모든 변경이 같은 검증을 통과하게 한다.
CI는 가장 강한 Gate다. 동시에 비밀과 배포 권한을 가진 자동화이므로, **공급망 공격의 입구**이기도 하다.

## 문제 신호

- 테스트를 개발자 PC에서만 돌리고, 병합 후에 깨진 것을 안다.
- 배포가 사람이 명령을 치는 절차라서 사람마다 결과가 다르다.
- 병합 전에 반드시 통과해야 할 검사(테스트, 린트, 보안 검사)를 강제하고 싶다.
- 클라우드 배포 자격 증명을 CI에 오래 두고 있다.

## 기준선의 한계

- 로컬 검사는 건너뛸 수 있다. git 훅도 `--no-verify`로 우회된다(이 저장소의 하네스 문서).
- 수동 배포는 절차 누락과 사람마다 다른 환경을 만든다.
- 배포 스크립트가 개인 PC의 자격 증명에 의존한다.

## 원리

- **사건 → 워크플로 → 잡 → 단계.** 사건이 워크플로를 시작하고, 잡은 러너 하나에서 단계들을 순서대로 실행한다. 잡끼리는 의존성(`needs`)으로 잇는다.
- **`GITHUB_TOKEN`.** 워크플로마다 저장소에 대한 설치 토큰이 주어진다. 문서는 이 토큰에 필요한 최소 권한만 주라고 권한다(`permissions` 키).
- **비밀.** 저장소·조직·환경 단위로 비밀을 두고 실행 중에 주입한다. 문서는 저장소 쓰기 권한이 있는 사용자는 모든 비밀을 읽을 수 있다고 경고한다.
- **액션은 남의 코드다.** `uses: owner/action@v4`는 남의 코드를 우리 비밀을 가진 러너에서 실행한다. 태그는 옮겨질 수 있어, 전체 커밋 SHA 고정이 유일한 불변 사용법이다.
- **스크립트 주입.** PR 제목, 브랜치 이름 같은 `github` 문맥 값을 `run:`에 `${{ }}`로 바로 넣으면 명령이 실행된다. `zzz";echo${IFS}"hello";#`도 유효한 브랜치 이름이다.
- **`pull_request_target`.** 이 사건은 기본 저장소의 토큰과 비밀을 가진 채, 기본 브랜치의 워크플로를 실행한다. 여기서 포크의 코드를 체크아웃해 실행하면 외부인이 비밀을 가진 환경에서 코드를 실행하게 된다.
- **OIDC.** 클라우드와 신뢰 관계를 맺으면 워크플로가 실행마다 짧게 사는 토큰을 받는다. 문서는 클라우드 자격 증명을 오래 사는 비밀로 복제하지 않아도 된다는 점을 이점으로 든다.
- **동시성.** `concurrency` 그룹으로 같은 그룹의 실행을 하나로 제한한다. 기본적으로 대기 중인 새 실행이 이전 대기 실행을 취소한다.
- **캐시.** 의존성 캐시는 7일 넘게 접근하지 않으면 지워지고, 저장소당 기본 총량은 10GB다.

## 가치

GitHub Actions의 가치는 **"병합되는 모든 변경이 같은 검사를 통과했다"를 보장하는 것**이다.

- 브랜치 보호의 필수 검사와 결합하면 우회하기 어려운 Gate가 된다.
- 배포가 코드와 로그로 남아 누가 언제 무엇을 배포했는지 추적된다.
- 저장소와 같은 곳에 있어 설정과 권한 관리가 한곳이다.

- **학습 실험.** 테스트와 시험 환경 배포를 자동화한다. 두 실행을 겹치게 해 동시성 정책을 확인하고, 제한된 토큰 권한으로 실패하는 단계를 관찰해 러너·권한·배포 순서를 설명한다.

## 트레이드오프와 리스크

- **공급망 위험.** 서드파티 액션, 러너 이미지, 의존성 설치가 모두 외부 코드다. 태그로 참조한 액션이 바뀌면 우리 비밀을 가진 러너에서 새 코드가 돈다.
- **권한 과다.** 기본 토큰 권한이 넓거나 비밀을 모든 워크플로에 열어 두면, 워크플로 하나의 취약점이 저장소 전체와 배포 대상의 위험이 된다.
- **포크 PR과 비밀.** 외부 기여를 받으면서 비밀이 필요한 검사를 돌리는 설계가 어렵다. `pull_request_target`의 잘못된 사용이 대표적 사고 경로다.
- **느린 CI는 우회를 부른다.** CI가 느리면 개발자가 검사를 건너뛰거나 묶어서 병합한다.
- **불안정한 테스트.** 간헐 실패가 쌓이면 재실행이 습관이 되고, 진짜 실패를 놓친다.
- **비용과 한도.** 러너 시간, 캐시 한도, 동시 실행 한도가 있다. 캐시가 한도를 넘으면 퇴출이 잦아진다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| GitLab CI, Jenkins 등 | 저장소가 다른 플랫폼에 있거나, 온프레미스 제어가 필요하다. |
| 자체 호스팅 러너 | 특수 하드웨어(GPU), 사내망 접근, 비용 절감이 필요하다. 러너 격리와 보안은 우리 책임이 된다. |
| GitOps 배포(Argo CD 등) | 배포를 CI에서 밀어 넣는(push) 대신, 클러스터가 저장소의 원하는 상태를 끌어온다(pull). 배포 자격 증명이 CI에 없다. |

## 깊이 있는 활용

- **토큰 권한을 최소로.** 워크플로 최상단에 `permissions: contents: read`를 두고, 필요한 잡에서만 권한을 올린다.
- **액션은 SHA로 고정하고 자동 갱신한다.** 전체 커밋 SHA로 고정하고, 주석으로 버전을 남기고, Dependabot이 갱신 PR을 만들게 한다. 조직 정책으로 SHA 고정을 강제할 수 있다.
- **입력은 환경 변수로 넘긴다.** `${{ github.event.pull_request.title }}`을 `run:`에 직접 넣지 말고 `env:`로 넘긴 뒤 스크립트에서 따옴표로 감싼 변수로 쓴다.
- **클라우드 배포는 OIDC로.** 오래 사는 액세스 키 대신 OIDC 신뢰 관계로 짧은 토큰을 받고, 클라우드 쪽 신뢰 조건에 저장소·브랜치·환경을 걸어 범위를 좁힌다.
- **환경 보호 규칙으로 배포를 막는다.** 운영 배포 잡은 `environment: production`을 참조하게 하고, 필수 승인자와 브랜치 제한을 건다. 환경 비밀은 보호 규칙을 통과한 잡만 읽는다.
- **배포는 동시성 그룹으로 직렬화한다.** 같은 환경의 배포가 겹치지 않게 그룹을 두고, 취소 대신 대기가 필요하면 대기 옵션을 쓴다. PR 검사는 새 커밋이 오면 이전 실행을 취소한다.
- **캐시 키를 잠금 파일 해시로.** `hashFiles('**/gradle.lockfile')` 같은 키로 의존성이 바뀔 때만 캐시를 새로 만든다. Docker 빌드는 GitHub Actions 캐시 백엔드로 층을 재사용한다.
- **빠른 검사와 느린 검사를 나눈다.** 린트와 단위 테스트는 모든 PR에서 먼저, 통합 테스트와 부하 회귀는 병렬로 또는 병합 큐에서 돌린다.
- **간헐 실패를 추적한다.** 재실행으로 통과한 실패를 기록하고, 간헐 실패 테스트를 고친다. 비활성화로 덮지 않는다.

## 임시방책의 신호

- `uses: some/action@main`처럼 가변 참조를 쓴다.
- 모든 워크플로에 `permissions: write-all`이나 기본 넓은 권한을 둔다.
- 클라우드 액세스 키를 저장소 비밀에 몇 년째 둔다.
- 외부 PR에서 비밀이 필요해지자 `pull_request_target`으로 바꾸고 PR 코드를 체크아웃한다.
- CI가 느리자 필수 검사를 해제한다.
- 실패한 잡을 원인 확인 없이 재실행한다.

## 실패 재현

- **스크립트 주입.** 시험 저장소에서 `${{ github.event.pull_request.title }}`을 `run:`에 넣은 워크플로에 명령이 섞인 제목의 PR을 열어 실행되는 것을 확인한다. 환경 변수 방식으로 바꿔 막히는지 본다.
- **태그 이동.** 시험용 액션의 태그를 다른 커밋으로 옮기고, 태그 참조 워크플로는 새 코드를, SHA 참조 워크플로는 옛 코드를 실행하는 것을 본다.
- **동시 배포.** 동시성 그룹 없이 배포 워크플로를 연달아 두 번 실행해 겹치는 것을 보고, 그룹을 넣어 반복한다.

## 측정과 검증

- **CI 소요 시간.** PR당 첫 피드백까지 시간과 전체 소요 시간의 p50·p90을 추적한다.
- **실패 원인 분포.** 실패를 코드 결함, 간헐 실패, 인프라 문제로 나눠 센다. 간헐 실패율을 줄이는 것이 목표다.
- **보안 상태.** SHA로 고정되지 않은 액션 수, 쓰기 권한이 있는 워크플로 수, 오래 사는 클라우드 자격 증명 수를 센다. OpenSSF Scorecard 같은 도구로 점검한다.
- **캐시 적중.** 캐시 적중률과 퇴출 빈도를 본다.

## 재검토 조건

- 러너 비용이나 한도가 병목이다. 자체 호스팅 러너나 작업 분할을 검토한다.
- 배포 대상이 늘어 push 방식 배포의 자격 증명 관리가 부담이다. GitOps를 검토한다.

## 출처

- GitHub 문서, [Security hardening / secure use](https://github.com/github/docs/blob/main/content/actions/reference/security/secure-use.md): 최소 권한, 쓰기 권한자의 비밀 접근, 전체 커밋 SHA 고정.
- GitHub 문서, [Script injections](https://github.com/github/docs/blob/main/content/actions/concepts/security/script-injections.md): 신뢰할 수 없는 문맥 값, 브랜치 이름 예시.
- GitHub 문서, [Securely using pull_request_target](https://github.com/github/docs/blob/main/content/actions/reference/security/securely-using-pull_request_target.md): 높은 신뢰 수준과 포크 코드 실행의 위험.
- GitHub 문서, [OpenID Connect](https://github.com/github/docs/blob/main/content/actions/concepts/security/openid-connect.md): 짧게 사는 토큰, 장기 비밀 제거.
- GitHub 문서, [Concurrency](https://github.com/github/docs/blob/main/content/actions/concepts/workflows-and-actions/concurrency.md), [Dependency caching](https://github.com/github/docs/blob/main/content/actions/reference/workflows-and-actions/dependency-caching.md), [Deployment environments](https://github.com/github/docs/blob/main/content/actions/concepts/workflows-and-actions/deployment-environments.md): 동시성 기본 동작, 캐시 7일·10GB, 환경 보호 규칙.
- 이 저장소의 [하네스 엔지니어링](../../harness-engineering.md): git 로컬 훅 우회와 원격 Gate.
