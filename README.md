# Tackroom

개인용 Claude Code 플러그인과, 그 플러그인을 만들기 위한 조사를 모은 저장소다.

## 구성

- `plugin/`: 플러그인
  - [kowrite](plugin/kowrite/README.md): 한국어 문서·주석·커밋의 규칙을 훅으로 검사한다.
- `docs/`: 설계 원칙과 조사
  - [하네스 엔지니어링](docs/harness-engineering.md): 훅과 지침을 언제, 어디에 두는지에 대한 원칙
  - [기술 스택 조사](docs/stacks/README.md): 문제 영역별 기준선과 기술의 원리, 트레이드오프, 검증 방법
  - [기술 판단 스킬 전략](docs/skill-strategy.md): 조사를 스킬로 만드는 구조와 평가 설계
- `tests/`: 테스트

## 테스트

```
python -m unittest discover -s tests
```

- `test_regressions.py`: 발견한 결함을 입력 그대로 남긴다.
- `test_rules.py`: 규칙마다 차원을 정해 곱집합으로 검사한다. 목록에 사례 없는 값이 생기면 실패한다.
- `test_metrics.py`: 올바른 글의 오탐률과 어절마다 끊은 글의 재현율을 잰다. 재현율 하한은 올리기만 한다.
- `test_state.py`: 훅 상태가 한도 안에 머물고 작업 트리에 드러나지 않는지 확인한다.
- `test_stacks.py`: 기술 스택 조사 문서가 목록과 일치하고 양식을 갖췄는지 확인한다.
