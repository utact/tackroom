# MySQL InnoDB

확인: 2026-09-29 재검토. 최초 조사는 2026-09-27, MySQL 8.4 LTS(소스 태그 mysql-8.4.9)와 8.4 레퍼런스 매뉴얼 기준. 혁신 릴리스는 9.7까지 나와 있다.

## 요약

InnoDB는 MySQL의 기본 저장 엔진으로, 행을 기본 키 순서의 B-tree(클러스터드 인덱스)에 저장하는 트랜잭션 엔진이다.
기본 격리 수준은 Repeatable Read이고, 잠금 읽기에서는 행 사이의 틈(gap)까지 잠가 팬텀을 막는다.
[PostgreSQL](postgresql.md)과 같은 문제를 풀지만, 같은 SQL이 다른 잠금과 다른 결과를 낼 수 있다는 점이 핵심이다.

## 문제 신호

- 팀이나 조직의 운영 경험, 백업·복제·모니터링 도구가 MySQL에 맞춰져 있다.
- 기본 키 범위 조회가 많고, 행을 기본 키 순서로 모아 두면 이득이 크다.
- MySQL에서 동시 요청 중 데드락이 자주 난다. 원인이 gap 잠금인 경우가 많다.
- PostgreSQL 기준으로 짠 코드를 MySQL로 옮긴다.

## 기준선의 한계

이 문서의 기준선도 "RDB를 저장소로만 쓰고 규칙은 애플리케이션이 지키는" 방식이다. 한계는 [PostgreSQL](postgresql.md#기준선의-한계)과 같다.
MySQL에 고유한 한계는 기본값을 모른 채 쓸 때 생긴다.

## 원리

- **클러스터드 인덱스.** 테이블 자체가 기본 키 순서의 B-tree다. 보조 인덱스의 잎에는 기본 키 값이 들어 있고, 보조 인덱스로 찾은 뒤 기본 키로 다시 찾는다.
- **기본 격리 수준은 Repeatable Read다.** 소스의 `transaction_isolation` 기본값이 `ISO_REPEATABLE_READ`다. 일반 `SELECT`는 트랜잭션 첫 읽기 시점의 스냅샷을 보는 일관 읽기이고 잠금을 걸지 않는다.
- **잠금 읽기와 갱신은 최신 버전을 본다.** `SELECT ... FOR UPDATE`, `UPDATE`, `DELETE`는 스냅샷이 아니라 최신 커밋 버전을 기준으로 동작한다. 같은 트랜잭션 안에서 일반 `SELECT`와 잠금 읽기가 다른 행을 볼 수 있다.
- **next-key 잠금.** Repeatable Read의 잠금 읽기는 인덱스 레코드와 앞의 틈을 함께 잠가 팬텀을 막는다. 조건이 인덱스를 못 타면 훑은 범위 전체가 잠긴다.
- **잠금 대기 시간.** 행 잠금 대기 상한 `innodb_lock_wait_timeout`의 기본값은 50초다. 메타데이터 잠금(MDL) 대기 상한 `lock_wait_timeout`은 기본값이 최대값(1년, 31,536,000초)이다.
- **온라인 DDL.** 8.4는 가능한 변경에 INSTANT를 기본으로 써, 데이터 사전만 바꾸고 테이블 크기와 무관하게 끝낸다. 모든 변경이 INSTANT가 되지는 않는다.

## 가치

InnoDB의 가치는 **기본 키 중심 접근의 효율과 넓은 운영 생태계**다.

- 기본 키 범위 조회와 기본 키 순 삽입이 빠르다. 같은 기본 키 범위의 행이 물리적으로 모여 있다.
- 복제, 백업, 온라인 스키마 변경 도구(gh-ost, pt-online-schema-change), 관리형 서비스가 성숙해 있다.
- INSTANT DDL로 컬럼 추가 같은 흔한 변경이 매우 싸다.

그래서 InnoDB를 고르는 이유는 대개 기술적 우위보다 운영 맥락이다.
그 맥락에서 쓴다면, 기본값이 만드는 잠금 동작을 이해하는 것이 이 기술을 제대로 쓰는 조건이다.

- **학습 실험.** 두 세션에서 인덱스가 있는 범위 갱신과 삽입을 겹친다. 격리 수준·인덱스를 바꾸며 실제 잠금과 대기를 관찰하고, 같은 SQL의 잠금 범위가 달라지는 이유를 설명한다.

## 트레이드오프와 리스크

- **gap 잠금이 데드락을 만든다.** 흔한 예로, 두 트랜잭션이 없는 행을 `SELECT ... FOR UPDATE`로 확인하면 둘 다 같은 틈에 gap 잠금을 얻는다(gap 잠금끼리는 충돌하지 않는다). 그 뒤 둘 다 그 틈에 `INSERT`하려 하면 서로의 gap 잠금을 기다려 데드락이 된다. "없으면 넣기"를 잠금 읽기로 짜면 동시 요청에서 데드락이 난다. 매뉴얼의 두 규칙에서 바로 나온다. 서로 다른 트랜잭션의 gap 잠금은 공존하고, 삽입 의도 잠금은 그 틈의 다른 gap 잠금을 기다린다. 구체적인 틈의 범위는 인덱스 구조와 이웃 레코드에 따라 다르다.
- **인덱스 없는 조건은 잠금 범위를 키운다.** 조건 컬럼에 인덱스가 없으면 훑은 행과 틈을 모두 잠근다. 작은 `UPDATE` 하나가 테이블 대부분을 막을 수 있다.
- **스냅샷과 최신 버전의 혼재.** Repeatable Read에서 `SELECT`로 본 값과 `UPDATE`가 보는 값이 다를 수 있다. PostgreSQL은 직렬화 실패를 내지만 MySQL은 최신 버전에 그대로 적용해, 같은 코드가 다른 결과를 낸다.
- **MDL 대기가 사실상 무한이다.** `ALTER TABLE`이 긴 트랜잭션이 쥔 메타데이터 잠금을 기다리는 동안, 뒤에 온 모든 조회가 `ALTER`를 기다린다. `lock_wait_timeout` 기본값이 1년이라 스스로 풀리지 않는다.
- **기본 키 설계의 비용이 크다.** 무작위 UUID 기본 키는 삽입 위치가 흩어져 페이지 분할과 캐시 효율 저하를 부른다. 기본 키가 넓으면 모든 보조 인덱스가 함께 커진다.
- **긴 트랜잭션은 undo 로그를 붙잡는다.** 오래 열린 트랜잭션이 있으면 옛 버전을 지우지 못해 history list가 길어지고 읽기가 느려진다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| [PostgreSQL](postgresql.md) | 배제 제약, 부분 인덱스, 풍부한 인덱스 종류, 트랜잭션 DDL이 필요하다. 조직에 MySQL 운영 맥락이 없다. |
| 격리 수준을 Read Committed로 | gap 잠금으로 인한 데드락이 문제이고, 팬텀을 애플리케이션이나 제약으로 막을 수 있다. 문장별 스냅샷이 된다. |

## 깊이 있는 활용

- **"없으면 넣기"는 유일 제약과 `INSERT ... ON DUPLICATE KEY UPDATE`나 `INSERT IGNORE`로 한다.** 잠금 읽기로 존재를 확인하지 않는다. 멱등 키도 유일 인덱스로 받는다.
- **기본 키는 좁고 순서대로 커지게 한다.** 자동 증가 정수나 시간 순 UUID(UUIDv7 등)를 `BINARY(16)`으로 저장한다. 외부에 노출할 ID와 내부 기본 키를 나누는 것도 방법이다.
- **잠금 범위는 인덱스로 줄인다.** 조건 컬럼에 인덱스를 두고 `EXPLAIN`으로 확인한다. 유일 인덱스의 동등 비교는 행을 찾았을 때만 틈 없이 레코드만 잠근다. 찾는 행이 없으면 틈을 잠가, "없으면 넣기"의 데드락 조건은 그대로 남는다.
- **DDL 세션에는 짧은 `lock_wait_timeout`을 건다.** `SET SESSION lock_wait_timeout = 5`처럼 두고 실패하면 재시도한다. 먼저 `performance_schema.metadata_locks`와 긴 트랜잭션을 확인한다.
- **INSTANT가 되는지 명시한다.** `ALTER TABLE ... ALGORITHM=INSTANT`로 적으면 INSTANT가 불가능할 때 조용히 테이블을 다시 쓰는 대신 오류를 낸다. 불가능한 변경은 gh-ost 같은 도구로 한다.
- **데드락은 로그로 원인을 본다.** `SHOW ENGINE INNODB STATUS`의 최근 데드락 절에서 어떤 잠금(레코드, gap, 삽입 의도)이 부딪혔는지 본다. 데드락은 정상 동작의 일부이므로 트랜잭션 재시도를 넣는다.

## 임시방책의 신호

- 데드락이 나자 격리 수준을 이유 없이 바꾸거나, 잠금 읽기에 `NOWAIT`를 붙이고 실패를 무시한다.
- 데드락 예외를 잡아 로그만 남긴다. 재시도하지 않는다.
- 배포 중 `Waiting for table metadata lock`으로 서비스가 멈춘 뒤, DDL을 새벽에 돌리는 것으로 해결한다.
- 기본 키를 무작위 UUID 문자열(`CHAR(36)`)로 둔다.
- PostgreSQL에서 쓰던 "확인 후 쓰기"와 격리 수준 가정을 그대로 옮긴다.

## 실패 재현

- **gap 잠금 데드락.** 두 세션에서 같은 없는 키 범위를 `SELECT ... FOR UPDATE`한 뒤 둘 다 `INSERT`한다. 데드락이 나는지, `INSERT ... ON DUPLICATE KEY UPDATE`로 바꾸면 사라지는지 본다.
- **인덱스 없는 잠금.** 인덱스 없는 컬럼 조건으로 `UPDATE`하는 트랜잭션을 열어 두고, 다른 세션에서 무관한 행을 갱신해 막히는지 본다.
- **MDL 대기열.** 한 세션에서 트랜잭션을 열고 테이블을 읽은 채 두고, 다른 세션에서 `ALTER TABLE`, 세 번째 세션에서 단순 `SELECT`를 실행한다. 세 번째가 막히는지 `SHOW PROCESSLIST`로 본다.
- **격리 수준 차이.** 같은 동시성 테스트를 MySQL과 PostgreSQL에서 돌려 결과를 비교한다.
- 재현은 [Testcontainers](../verify/testcontainers.md)의 MySQL 모듈로 실제 서버에서 한다.

## 측정과 검증

- **정합성은 불변식으로 전수 검사한다.** 동시성 실험 후 SQL로 불변식 위반을 센다.
- **잠금 비용.** 부하 중 데드락 수(`INFORMATION_SCHEMA.INNODB_METRICS`의 `lock_deadlocks`), 행 잠금 대기 시간(`Innodb_row_lock_time_avg`), 재시도 횟수를 본다. MySQL에는 `Innodb_deadlocks` 상태 변수가 없다(MariaDB에는 있다). 데드락마다 원인을 남기려면 `innodb_print_all_deadlocks`를 켠다.
- **쿼리 성능.** `performance_schema`의 문장 요약(`events_statements_summary_by_digest`)으로 상위 쿼리를 찾고 `EXPLAIN ANALYZE`로 본다.
- **부하 시험.** sysbench나 [k6](../verify/k6.md)로 실제 요청 비율을 재현해 동시 접속 수에 따른 처리량과 p99 지연을 그린다.

## 재검토 조건

- gap 잠금으로 인한 데드락이 계속 운영 문제가 된다. 격리 수준과 쓰기 패턴을 다시 설계한다.
- PostgreSQL 고유 기능(배제 제약, 부분 인덱스, 트랜잭션 DDL)이 필요한 요구가 늘어난다.

## 출처

- MySQL 소스 8.4.9, [sys_vars.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.9/sql/sys_vars.cc): `transaction_isolation` 기본값 Repeatable Read, `lock_wait_timeout` 기본값 `LONG_TIMEOUT`.
- MySQL 소스 8.4.9, [ha_innodb.cc](https://github.com/mysql/mysql-server/blob/mysql-8.4.9/storage/innobase/handler/ha_innodb.cc): `innodb_lock_wait_timeout` 기본값 50초, `Innodb_row_lock_*` 상태 변수(데드락 수 상태 변수는 없음, 2026-09-29 재검토).
- MySQL 8.4 Reference Manual, [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html): `lock_deadlocks` 지표와 `innodb_print_all_deadlocks`. 검색 요약으로 확인했다.
- MySQL 8.4 Reference Manual, [Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html): 삽입 의도 잠금, 유일 검색 조건은 찾은 레코드만 잠금. 검색 요약으로 확인했다(2026-09-29 재검토).
- MySQL 8.4 Reference Manual, [InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html), [Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html), [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html): next-key 잠금, 일관 읽기, 갱신의 semi-consistent read. 이 환경에서는 원문 접근이 막혀 검색 요약으로 확인했다.
- MySQL 8.4 Reference Manual, [Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html): INSTANT 기본 알고리즘과 제약. 검색 요약으로 확인했다.
- `lock_wait_timeout` 기본값 31,536,000초는 [검색 결과의 2차 자료](https://oneuptime.com/blog/post/2026-03-31-mysql-metadata-locks/view)와 소스의 `LONG_TIMEOUT`을 함께 근거로 한다.
