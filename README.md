<p align="center">
  <img src="assets/readme-header.png" alt="Tackroom — 코드, 기술 자료, 노트를 정돈한 개발 작업대" width="100%">
</p>

<h1 align="center">Tackroom</h1>

<p align="center">
  <strong>AI와 함께 개발할 때, 기술 선택부터 검증과 글쓰기까지.</strong><br>
  Claude Code에서 독립적으로 골라 쓰는 개발 플러그인 모음.
</p>

<p align="center">
  <a href="https://github.com/utact/tackroom/actions/workflows/test.yml"><img src="https://github.com/utact/tackroom/actions/workflows/test.yml/badge.svg" alt="테스트 상태"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0f766e" alt="MIT 라이선스"></a>
  <a href="CONTRIBUTING.md#requirements"><img src="https://img.shields.io/badge/Python-3.8%2B-3776ab" alt="Python 3.8 이상"></a>
</p>

<p align="center">
  <a href="#installation">Installation</a> ·
  <a href="#plugins">Plugins</a> ·
  <a href="#documentation">Documentation</a> ·
  <a href="#contributing">Contributing</a>
</p>

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

## Plugins

| 플러그인 | 목적 | 동작 방식 |
| --- | --- | --- |
| [techjudge](plugin/techjudge/skills/tech-judgment/SKILL.md) | 기술 선택과 적용 | Skill과 기술 카드 |
| [harness](plugin/harness/skills/harness-engineering/SKILL.md) | AI 작업 환경 개선 | Skill과 판단 기준 |
| [kowrite](plugin/kowrite/README.md) | 한국어 작성 규칙 | 세션 지침과 훅 |

### techjudge

기능을 설계하거나 확장할 때 맞는 기술을 고른다.

- 기존 구조와 프로젝트 제약을 살펴 기술 후보를 찾고 비교한다.
- 고른 기술을 구현과 검증까지 이어서 적용한다.
- 주니어 개발자의 학습도 도입 이유로 다룬다.
- 선택 이유, 배울 원리, 추가 부담, 확인할 동작을 설명한다.

개발 요청에 맞춰 자동으로 쓰이며, `/techjudge:tech-judgment`로 직접 호출할 수도 있다.

### harness

AI가 지침을 놓치거나 도구·테스트 결과를 잘못 다룰 때 원인을 진단한다.

- 지침, 도구, 훅, 피드백, 평가 중 고칠 곳을 정한다.
- 검사 뒤의 수정·재검사 경로와 사용자에게 결정을 넘길 경로를 정한다.

개발 요청에 맞춰 자동으로 쓰이며, `/harness:harness-engineering`으로 직접 호출할 수도 있다.

### kowrite

문서와 코드가 함께 지키는 한국어 작성 규칙이다.

- 훅이 문서·주석의 문장 중간 개행과 커밋의 도구 표기를 검사한다.
- 훅이 문서의 수치를 코드 상수와 연결하고, 설명하는 코드의 변경을 추적한다.
- 세션 지침이 사용자나 저장소에서만 통하는 표현을 통용 용어로 바꾸도록 안내한다.

자세한 규칙과 검사 범위는 [kowrite 안내](plugin/kowrite/README.md)에 있다.

## Documentation

- [기술 카드](docs/stacks/README.md): 기술별 원리, 적용 조건, 반례, 검증 방법
- [하네스 엔지니어링](docs/harness-engineering.md): AI 작업 환경을 개선하는 판단 기준
- [스킬 구조와 검증](docs/skill-strategy.md): 두 Skill의 역할, 배포 참조, 평가 설계

## Contributing

[기여 관례](CONTRIBUTING.md)에서 개발 환경, 테스트, 브랜치·커밋 형식을 확인한다.

## License

[MIT](LICENSE)
