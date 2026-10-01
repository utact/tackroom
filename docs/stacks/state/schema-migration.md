# Flyway와 무중단 스키마 변경

확인: 2026-09-29 재검토. 최초 조사는 2026-09-27, Flyway 12.9 문서와 소스(flyway 저장소), PostgreSQL 문서(master 브랜치) 기준.

## 요약

Flyway는 스키마 변경을 버전이 붙은 SQL 파일로 두고, DB에 적용 이력 테이블을 남겨 어느 환경이든 같은 순서로 같은 변경을 적용한다.
무중단 스키마 변경은 도구가 아니라 절차다. 옛 코드와 새 코드가 동시에 도는 배포 구간에서도 둘 다 동작하도록 변경을 여러 단계로 나눈다(expand/contract).
둘을 함께 써야 "재현 가능한 변경"과 "멈추지 않는 변경"을 함께 얻는다.

## 문제 신호

- 운영 DB 스키마가 누가 언제 바꿨는지 모르게 환경마다 다르다.
- 배포 중 스키마 변경 때문에 오류가 나거나 서비스가 멈춘 적이 있다.
- 컬럼 이름을 바꾸거나 타입을 바꿔야 하는데, 롤링 배포 중에 옛 인스턴스가 살아 있다.
- 큰 테이블에 인덱스를 추가해야 한다.

## 기준선의 한계

- 사람이 SQL을 손으로 실행하면 환경마다 적용 여부가 다르고, 실패한 변경의 복구 절차가 없다.
- ORM의 자동 스키마 생성(`ddl-auto=update` 등)은 삭제와 이름 변경을 다루지 못하고, 운영에서 무엇을 실행할지 미리 볼 수 없다.
- 변경을 한 번에 적용하면, 롤링 배포 중 옛 코드가 새 스키마를 만나 실패한다. 예를 들어 컬럼 이름을 바꾸는 순간 옛 인스턴스의 쿼리가 모두 실패한다.

## 원리

- **버전 파일과 이력 테이블.** `V1__init.sql`, `V2__add_email.sql`처럼 버전 순서로 적용하고, 적용 결과와 체크섬을 이력 테이블에 남긴다.
- **적용 전 검증.** `validateOnMigrate` 기본값은 true다. 이미 적용한 파일이 바뀌었거나(체크섬 불일치) 빠졌으면 적용을 거부한다.
- **순서 강제.** `outOfOrder` 기본값은 false다. 이미 3까지 적용된 DB에 늦게 합쳐진 2는 적용되지 않는다.
- **트랜잭션 단위.** `executeInTransaction` 기본값은 true로, 마이그레이션 하나를 트랜잭션 하나로 실행한다. PostgreSQL은 DDL도 트랜잭션 안에서 롤백되지만, MySQL과 Oracle은 DDL 전후에 암묵적으로 커밋한다.
- **동시 실행 잠금.** 여러 인스턴스가 동시에 시작해도 한 곳만 적용하도록 잠금을 쓴다. PostgreSQL에서는 기본적으로 트랜잭션 수준 advisory lock을 쓴다.
- **안전장치.** `clean`(스키마 전체 삭제)은 기본적으로 막혀 있다(`cleanDisabled=true`).
- **expand/contract.** 스키마 변경을 "추가(expand) → 코드 전환 → 제거(contract)"로 나눈다. 혼재하는 앱 버전이 함께 동작하도록 확장하고, 이전 구조를 쓰는 코드와 롤백 의존성이 없어진 뒤 제거한다.

## 가치

Flyway의 가치는 **스키마를 코드처럼 리뷰하고 재현하는 것**이다.
어느 환경이 어떤 상태인지 이력 테이블로 알 수 있고, 새 환경은 처음부터 같은 순서로 만들어진다.

expand/contract의 가치는 **배포와 스키마 변경을 분리하는 것**이다.
호환되는 버전이 공존하는 동안 롤링 배포와 앱 롤백이 가능하다. 컬럼·데이터를 제거한 뒤에는 그 구조를 요구하는 앱으로 바로 롤백할 수 없으므로, 제거 시점과 복구 절차를 따로 정한다.

- **학습 실험.** 구버전과 신버전 앱을 동시에 실행하며 컬럼 확장·백필·읽기 전환·제거를 순서대로 적용한다. 중간 실패와 재실행을 시험하고, 앱 롤백만으로 되돌릴 수 없는 변경을 구분한다.

## 트레이드오프와 리스크

- **되돌리기는 기본 기능이 아니다.** Undo는 유료(Teams) 기능이라, 되돌리는 마이그레이션을 새 버전으로 적용한다. 데이터를 지운 변경은 되돌릴 수 없다.
- **적용한 파일을 고치면 안 된다.** 체크섬 불일치로 적용이 멈춘다. `repair`로 이력을 맞출 수 있지만, 환경마다 실제 스키마가 달라지는 원인이 된다.
- **시작 시 자동 적용의 위험.** Spring Boot처럼 애플리케이션 시작 때 적용하면, 오래 걸리는 변경이 헬스 체크 실패와 재시작 반복을 부를 수 있다. 여러 인스턴스가 동시에 시작하면 잠금을 기다린다.
- **트랜잭션 안에서 못 하는 문장이 있다.** PostgreSQL의 `CREATE INDEX CONCURRENTLY`는 트랜잭션 안에서 실행되지 않는다. 해당 마이그레이션은 트랜잭션 없이 실행해야 하고, 실패하면 중간 상태가 남는다.
- **expand/contract는 배포 횟수를 늘린다.** 컬럼 이름 하나를 바꾸는 데 배포가 서너 번 필요하다. 중간 단계의 이중 쓰기 코드가 복잡도를 더한다.
- **잠금은 도구가 막아 주지 않는다.** Flyway는 SQL을 실행할 뿐이다. `ACCESS EXCLUSIVE` 잠금 대기열로 서비스를 멈추게 하는 SQL도 그대로 실행한다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| Liquibase | 여러 DB를 지원하는 추상 변경 형식(XML, YAML)과 내장 롤백 정의가 필요하다. |
| ORM 자동 스키마 | 로컬 개발과 테스트에서만. 운영에는 쓰지 않는다. |
| gh-ost, pt-online-schema-change | MySQL에서 INSTANT로 안 되는 큰 테이블 변경. 그림자 테이블에 복사하고 교체한다. |

## 깊이 있는 활용

- **컬럼 이름 바꾸기는 다섯 단계로 한다.** 새 컬럼 추가(expand) → 코드가 두 컬럼에 모두 쓰기 → 옛 데이터를 새 컬럼으로 나눠서 복사 → 코드가 새 컬럼만 읽고 쓰기 → 옛 컬럼 삭제(contract). 각 단계 사이에 배포가 있고, 어느 시점에서든 직전 버전으로 되돌릴 수 있다.
- **큰 데이터 이동은 마이그레이션 밖에서 나눠 한다.** 수백만 행의 `UPDATE`를 마이그레이션 하나로 돌리면 긴 트랜잭션과 잠금이 생긴다. 기본 키 범위로 나눠 짧은 트랜잭션으로 반복하는 배치로 뺀다.
- **PostgreSQL 인덱스는 동시 생성용 설정을 쓴다.**
  - 파일 옆 `V5__idx.sql.conf`에 `executeInTransaction=false`를 두어 그 파일만 트랜잭션 밖에서 실행한다.
  - Flyway 잠금은 `postgresql.transactional.lock=false`로 세션 수준으로 바꾼다.
  - 실패하면 INVALID 인덱스를 지우고 다시 만든다.
- **제약은 두 단계로 건다.** `NOT VALID`로 새 쓰기부터 검사하고, 다음 마이그레이션의 `VALIDATE CONSTRAINT`가 쓰기를 막지 않는 약한 잠금으로 기존 행을 검사한다. `NOT NULL`은 PostgreSQL 18부터 `ADD CONSTRAINT 이름 NOT NULL col NOT VALID` → `VALIDATE CONSTRAINT`로 바로 건다. 17 이하에서는 `CHECK (col IS NOT NULL) NOT VALID` → 검증 → `SET NOT NULL` 순서면 테이블 스캔을 건너뛴다.
- **모든 DDL 앞에 `SET lock_timeout`을 둔다.** 잠금을 몇 초 안에 못 얻으면 실패하고 재시도해, 대기열로 서비스를 멈추지 않는다. MySQL은 `lock_wait_timeout`이다.
- **적용과 배포를 분리한다.** 애플리케이션 시작 시 자동 적용 대신 배포 파이프라인의 별도 단계에서 `flyway migrate`를 실행한다. 적용 결과를 확인한 뒤 새 코드를 배포한다.
- **CI에서 빈 DB와 운영 사본 모두에 적용해 본다.** 빈 DB에 처음부터 적용하는 시험은 파일 순서와 문법을, 운영 스냅샷 사본에 적용하는 시험은 실행 시간과 잠금을 잡는다.

## 임시방책의 신호

- 운영 스키마를 손으로 고치고 마이그레이션 파일은 나중에 맞춘다.
- 체크섬 오류가 나자 이미 적용한 파일을 고치고 `repair`를 돌린다.
- 컬럼 이름 변경을 마이그레이션 하나로 하고, 배포 중 오류는 "잠깐이니까" 넘긴다.
- 운영에서 `ddl-auto=update`를 켜 둔다.
- 큰 테이블 인덱스를 일반 `CREATE INDEX`로 만들고 새벽 배포로 피해를 줄인다.
- `validateOnMigrate=false`로 검증을 끈다.

## 실패 재현

- **롤링 배포 비호환.** 옛 버전과 새 버전 애플리케이션을 동시에 띄우고, 한 번에 적용하는 변경(이름 변경)과 expand/contract 변경에서 각각 옛 버전 요청이 실패하는지 본다.
- **잠금 대기열.** 긴 트랜잭션을 열어 둔 채 마이그레이션을 적용하고, 다른 요청의 지연이 치솟는 것을 본다. `lock_timeout`을 넣고 반복한다.
- **동시 인덱스 생성 실패.** 유일 인덱스를 동시 생성하는 중에 중복 값을 넣어 실패시키고 INVALID 인덱스가 남는지 본다.
- **동시 시작.** 인스턴스 여러 개를 동시에 시작해 한 곳만 적용하는지 본다.
- **운영 크기 재현.** 운영 규모의 데이터를 넣은 사본에서 마이그레이션 시간과 잠금 종류(`pg_locks`)를 측정한다.

## 측정과 검증

- **마이그레이션 시간과 잠금.** 운영 규모 사본에서 각 파일의 실행 시간, 잡은 잠금의 종류와 유지 시간을 기록한다. `ACCESS EXCLUSIVE`를 몇 초 이상 잡는 변경은 설계를 바꾼다.
- **배포 중 오류율.** 배포 구간의 요청 오류율과 p99 지연을 배포 전 구간과 비교한다. [k6](../verify/k6.md)로 배포 내내 일정한 도착률의 요청을 보내면서 잰다.
- **환경 간 일치.** 각 환경의 이력 테이블과 실제 스키마 덤프를 비교한다.

## 재검토 조건

- 여러 종류의 DB를 같은 변경 정의로 관리해야 한다. Liquibase를 검토한다.
- MySQL에서 INSTANT로 안 되는 대형 변경이 잦다. 온라인 스키마 변경 도구를 들인다.
- 배포 빈도가 낮아 expand/contract의 추가 배포가 부담이다. 짧은 점검 창을 허용하는 편이 싸다.

## 출처

- Flyway 문서, [Execute In Transaction](https://github.com/flyway/flyway/blob/main/documentation/Reference/Configuration/Flyway%20Namespace/Flyway%20Execute%20In%20Transaction%20Setting.md), [Clean Disabled](https://github.com/flyway/flyway/blob/main/documentation/Reference/Configuration/Flyway%20Namespace/Flyway%20Clean%20Disabled%20Setting.md), [Validate On Migrate](https://github.com/flyway/flyway/blob/main/documentation/Reference/Configuration/Flyway%20Namespace/Flyway%20Validate%20On%20Migrate%20Setting.md), [Out Of Order](https://github.com/flyway/flyway/blob/main/documentation/Reference/Configuration/Flyway%20Namespace/Flyway%20Out%20Of%20Order%20Setting.md), [Mixed](https://github.com/flyway/flyway/blob/main/documentation/Reference/Configuration/Flyway%20Namespace/Flyway%20Mixed%20Setting.md): 기본값과 의미, MySQL·Oracle의 암묵적 커밋.
- Flyway 문서, [PostgreSQL Transactional Lock](https://github.com/flyway/flyway/blob/main/documentation/Reference/Configuration/Flyway%20Namespace/Flyway%20PostgreSQL%20Namespace/Flyway%20PostgreSQL%20Transactional%20Lock%20Setting.md): `CREATE INDEX CONCURRENTLY`에는 false로.
- Flyway 문서, [Script Configuration](https://github.com/flyway/flyway/blob/main/documentation/Reference/Script%20Configuration.md), [Undo](https://github.com/flyway/flyway/blob/main/documentation/Reference/Commands/Undo.md): 파일별 설정, Undo는 Teams 등급.
- PostgreSQL, [ALTER TABLE](https://github.com/postgres/postgres/blob/master/doc/src/sgml/ref/alter_table.sgml), [CREATE INDEX](https://github.com/postgres/postgres/blob/master/doc/src/sgml/ref/create_index.sgml): `NOT VALID`와 `SET NOT NULL`의 스캔 생략, 동시 인덱스 생성.
- PostgreSQL, [18 릴리스 노트](https://github.com/postgres/postgres/blob/REL_18_STABLE/doc/src/sgml/release-18.sgml): NOT NULL 제약을 `NOT VALID`로 추가(2026-09-29 재검토).
