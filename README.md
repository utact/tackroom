<p align="center">
  <img src="assets/readme-header.png" alt="Tackroom — 코드, 기술 자료, 노트를 정돈한 개발 작업대" width="100%">
</p>

<h1 align="center">Tackroom</h1>

<p align="center">
  <strong>AI가 현재 작업에서 쓸 기술과 원리를 더 넓게 찾도록 돕습니다.</strong><br>
  Claude Code에서 독립적으로 골라 쓰는 개발 플러그인 모음.
</p>

<p align="center">
  <a href="https://github.com/utact/tackroom/actions/workflows/test.yml"><img src="https://github.com/utact/tackroom/actions/workflows/test.yml/badge.svg" alt="테스트 상태"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0f766e" alt="MIT 라이선스"></a>
  <a href="CONTRIBUTING.md#requirements"><img src="https://img.shields.io/badge/Python-3.8%2B-3776ab" alt="Python 3.8 이상"></a>
</p>

<p align="center">
  <a href="#plugins">Plugins</a> ·
  <a href="#installation">Installation</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="#contributing">Contributing</a>
</p>

## Plugins

| 플러그인 | 주요 역할 |
| --- | --- |
| [techjudge](plugin/techjudge/skills/tech-judgment/SKILL.md) | 기술·원리의 활용 기회 탐색과 적용 |
| [harness](plugin/harness/skills/harness-engineering/SKILL.md) | AI 작업 실패의 원인 진단과 개선 |
| [kowrite](plugin/kowrite/README.md) | 문서 변경 누락 검사와 한국어 작성 지침 |

techjudge와 harness는 관련 요청에서 AI가 선택할 수 있는 Skill이며, 명령으로도 호출할 수 있다.

### techjudge

현재 기능에 맞는 기술 스택·오픈소스·수학적 원리의 활용 기회를 찾는다.

- 출처·적용 조건·대안·반례를 정리한 자료로 기존 방식과 후보를 비교하고, 프로젝트 제약과 추가 부담을 함께 따진다.
- 작은 프로젝트의 학습 기회도 고려하며, 선택한 방법을 구현과 검증으로 잇는다.

예를 들어 [목록 이동의 순서 키](docs/algorithms/systems/fractional-indexing.md), [배경의 생성 규칙](docs/algorithms/generation/procedural-illustration.md)을 검토한다.

`/techjudge:tech-judgment`로 직접 호출할 수 있다.

### harness

AI의 반복 실수에서 정보·도구 실행·결과 판정 중 고칠 곳을 찾는다.

- 안내·관찰·차단·자동 수정의 역할을 구분해 원인에 맞는 방법을 고른다.
- 검사 실패를 수정·재검사로 잇고, 사용자 결정이 필요한 경우를 구분한다.

`/harness:harness-engineering`로 직접 호출할 수 있다.

### kowrite

문서가 코드의 변경을 따라가도록 마커와 훅으로 검사한다.

- 마커로 문서의 수치와 코드 상수를 연결해 값의 불일치를 검사한다.
- 설명 대상 코드를 마커로 지정해, 코드만 바뀐 경우 문서 검토를 요구한다.
- 사용자나 저장소에서만 통하는 표현은 통용 용어로 바꾸거나 처음에 정의하도록 세션 지침으로 안내한다.

문장 중간 개행과 커밋의 도구 표기도 검사한다. 자세한 범위는 [kowrite 안내](plugin/kowrite/README.md)에 있다.

## Installation

```text
/plugin marketplace add utact/tackroom
/plugin install techjudge@tackroom
/plugin install harness@tackroom
/plugin install kowrite@tackroom
```

설치할 때 적용 범위를 고른다.

- **사용자 범위**: 모든 프로젝트에 적용한다.
- **프로젝트 공유 범위**: 이 저장소의 협업자와 함께 쓴다.
- **로컬 범위**: 이 저장소에서 자신에게만 적용한다.

## Documentation

- [기술 스택·설계 패턴](docs/stacks/README.md): 현재 기능에서 비교할 기술과 학습 실험
- [수학·알고리즘·표현 기법](docs/algorithms/README.md): 원리의 성립 조건, 활용 예시와 반례
- [하네스 엔지니어링](docs/harness-engineering.md): 안내·관찰·차단·자동 수정의 구분과 적용 기준
- [스킬 구조와 검증](docs/skill-strategy.md): 참조 배포 구조와 검증 범위

## Contributing

[기여 관례](CONTRIBUTING.md)에서 개발 환경, 테스트, 브랜치·커밋 형식을 확인한다.

## License

[MIT](LICENSE)
