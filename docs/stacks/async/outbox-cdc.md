# Outbox와 CDC

확인: 2026-09-27, Debezium 문서(main 브랜치)와 PostgreSQL 문서(master 브랜치) 기준.

## 요약

업무 데이터와 "내보낼 사건"을 같은 DB 트랜잭션으로 저장하고(outbox 테이블), 별도 프로세스가 그 테이블을 읽어 브로커로 보낸다.
읽는 방식은 주기적 조회(폴링 발행)나 DB 변경 로그 구독(CDC, Debezium)이다.
DB 저장과 메시지 발행이라는 두 쓰기를 하나의 DB 쓰기로 바꿔, 둘 중 하나만 성공하는 상태를 없앤다.

## 문제 신호

- 주문을 저장하고 `OrderCreated`를 Kafka나 RabbitMQ로 보내는 코드가 있다.
- 가끔 "DB에는 있는데 이벤트가 안 갔다"거나 "이벤트는 갔는데 DB 저장은 롤백됐다"는 불일치가 보고된다.
- 발행 실패를 로그로만 남기고 있다.
- 다른 서비스나 검색 색인이 원본 DB와 조금씩 어긋난다.

## 기준선의 한계

- **저장 후 발행.** 트랜잭션 커밋 후 발행하면, 커밋과 발행 사이에 프로세스가 죽을 때 사건을 잃는다.
- **발행 후 저장, 또는 트랜잭션 안에서 발행.** 발행이 먼저 나가고 트랜잭션이 롤백되면 존재하지 않는 사건이 퍼진다. 브로커 호출이 트랜잭션을 길게 만든다.
- **2단계 커밋(XA).** 브로커와 DB가 모두 지원해야 하고, 조정자 장애 시 복구가 어렵다. Kafka 설계 문서도 많은 출력 시스템이 2단계 커밋을 지원하지 않는다고 적는다.
- 이 문제는 브로커의 종류와 무관하다. Kafka든 RabbitMQ든 같은 이중 쓰기 문제가 생긴다.

## 원리

- **하나의 원자적 쓰기로 바꾼다.** 업무 행과 outbox 행을 같은 트랜잭션으로 저장한다. 커밋되면 둘 다 있고, 롤백되면 둘 다 없다.
- **발행은 그 뒤에 따로, 반복 가능하게 한다.** 릴레이는 커밋된 행만 보고 실패하면 다시 보낸다. 결과는 at-least-once다.
- **폴링 발행.** 릴레이가 주기적으로 미발행 행을 `SKIP LOCKED`로 가져와 발행하고, 발행 확인을 받은 뒤 발행 표시를 하거나 지운다. [DB 작업 큐](db-job-queue.md)와 같은 구조다.
- **CDC.** Debezium은 DB의 변경 로그(PostgreSQL은 논리 복제 슬롯, MySQL은 binlog)를 구독해 outbox 테이블의 `INSERT`를 사건으로 바꾼다. outbox 이벤트 라우터 SMT는 `aggregatetype`으로 토픽을 정하고 `aggregateid`를 메시지 키로 쓴다.

## 가치

Outbox의 가치는 **"저장했다"와 "알렸다"를 같은 사실로 만드는 것**이다.

- 업무 데이터가 커밋되면 사건은 결국 나간다. 커밋되지 않으면 사건도 없다.
- 사건의 순서가 DB 커밋 순서를 따른다(CDC). 같은 집계(aggregate)의 사건을 같은 키로 보내면 소비자는 순서대로 받는다.
- 발행 실패가 요청 실패가 되지 않는다. 브로커 장애 동안 사건은 outbox에 쌓였다가 복구 후 나간다.

CDC가 폴링보다 나은 점은 폴링 쿼리 부하와 폴링 지연이 없고, 커밋 순서를 정확히 따른다는 것이다.
폴링이 CDC보다 나은 점은 새 인프라(Kafka Connect, Debezium) 없이 애플리케이션 코드만으로 된다는 것이다.

- **학습 실험.** 주문 저장과 알림 발행 사이에 프로세스를 종료한다. 직접 이중 쓰기와 outbox를 비교하고, 중복 발행뿐 아니라 로그 보존을 넘긴 중단에서 무엇을 복구 원천으로 쓸지도 확인한다.

## 트레이드오프와 리스크

- **중복은 없앨 수 없다.** Debezium도 장애 복구 중에는 중복을 낼 수 있다고 적고, 폴링 발행도 발행 후 표시 전에 죽으면 다시 보낸다. 소비자 멱등 처리가 필수다.
- **복제 슬롯이 WAL을 붙잡는다(CDC, PostgreSQL).** 슬롯은 연결이 없어도 필요한 WAL과 카탈로그 행을 지우지 못하게 한다.
  - `max_slot_wal_keep_size` 기본값이 -1(무제한)이라, Debezium이 멈추면 DB 디스크가 찬다.
  - 극단적인 경우 트랜잭션 ID 겹침을 막으려 DB가 멈출 수 있다.
- **변경이 적은 테이블만 구독하면 WAL이 쌓인다.** 다른 테이블 변경은 많고 outbox 변경은 드물면 슬롯 위치가 늦게 전진한다. Debezium은 heartbeat 설정(`heartbeat.interval.ms`)으로 해결하라고 안내한다.
- **새 인프라와 권한.** CDC는 Kafka Connect 클러스터, 커넥터 설정, DB 복제 권한, 논리 복제 설정(`wal_level=logical`)을 요구한다. 스키마 변경이 커넥터를 멈출 수 있다.
- **outbox 테이블은 추가 전용이다.** Debezium outbox SMT는 변경이 모두 `INSERT`라고 가정하고 `DELETE`는 거른다. 정리 작업을 따로 둔다.
- **사건 형식이 공개 계약이 된다.** outbox의 payload는 다른 팀이 의존하는 API다. 내부 엔티티를 그대로 직렬화하면 내부 변경이 외부 장애가 된다.
- **폴링 발행의 부담.** DB 작업 큐의 부담(폴링 부하, 테이블 부풂)을 그대로 가진다. 릴레이를 여러 개 띄우면 순서가 깨질 수 있다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| [DB 작업 큐](db-job-queue.md) | 사건을 받는 쪽이 같은 애플리케이션 안의 작업자다. 브로커로 내보낼 필요가 없다. |
| 테이블 CDC(outbox 없이) | 업무 테이블의 변경을 그대로 복제하면 된다(검색 색인, 분석 저장소). 사건의 의미와 형식을 설계할 필요가 없을 때만 쓴다. 내부 스키마가 곧 외부 계약이 된다. |
| Kafka 트랜잭션 | 입력과 출력이 모두 Kafka 토픽이다. DB가 끼면 해당하지 않는다. |
| 2단계 커밋 | 참여 시스템이 모두 XA를 지원하고, 조정자 운영을 감당한다. 드물다. |

## 깊이 있는 활용

- **outbox 행에 사건 ID를 두고 헤더로 보낸다.** Debezium outbox 라우터가 `id` 컬럼을 헤더로 보내고, 소비자는 이 ID로 중복을 거른다. 폴링 발행도 같은 ID를 쓴다.
- **집계 ID를 메시지 키로 쓴다.** 같은 주문의 사건이 같은 파티션으로 가서 순서가 유지된다. 커밋 순서를 그대로 따르는 CDC와 결합하면 집계 단위 순서가 보장된다.
- **outbox 삭제는 복구 원천과 함께 정한다(CDC).** 필요한 변경 로그가 남아 있고 커넥터가 해당 변경을 처리한다면 삽입 후 삭제로 테이블을 비울 수 있다. 하지만 행과 WAL을 모두 잃으면 새 스냅샷으로 과거 사건을 복원할 수 없다. 전달 완료 확인, 보관 기간, 별도 사건 보관소나 재구성 절차를 정한 뒤 삭제한다.
- **슬롯을 감시하고 상한을 둔다.** `restart_lsn`과 현재 LSN의 차이에 경보를 건다. `max_slot_wal_keep_size`는 디스크를 보호하지만 필요한 WAL이 제거되면 슬롯을 정상적으로 이어 읽을 수 없다. 슬롯·커넥터 복구와 스냅샷만으로 돌아오지 않는 사건의 대사 절차를 함께 정한다.
- **폴링 발행은 발행 확인 후에 표시한다.** 브로커의 발행 확인(Kafka `acks=all`, RabbitMQ publisher confirm)을 받은 뒤에만 `published_at`을 기록한다. 순서가 필요하면 릴레이를 하나만 활성으로 두거나 집계 ID로 릴레이를 나눈다.
- **사건 스키마를 버전 관리한다.** payload에 스키마 버전을 넣고, 소비자가 모르는 필드를 무시하게 한다. 필드 삭제와 의미 변경은 새 사건 종류로 한다.

## 임시방책의 신호

- `@Transactional` 메서드 안에서 `kafkaTemplate.send()`를 호출한다.
- 커밋 후 발행에 실패하면 `catch`에서 로그만 남긴다.
- 불일치를 찾는 야간 대사(reconciliation) 배치가 생기고 계속 늘어난다.
- `@TransactionalEventListener(phase = AFTER_COMMIT)`에서 발행하고 이것으로 원자성이 보장된다고 여긴다. 커밋 후 발행 전에 죽으면 여전히 잃는다.
- 중복 사건이 보이자 발행 쪽에서 "보냈는지" 캐시를 둔다.

## 실패 재현

- **커밋 후 발행 전 종료(기준선).** outbox 없는 코드에서 커밋 직후 `kill -9`로 죽이고 사건 유실을 확인한다. outbox 적용 후 같은 실험에서 사건이 결국 나가는지 본다.
- **롤백.** 업무 로직이 outbox 기록 뒤에 예외를 던지게 해서 사건이 나가지 않는지 본다.
- **브로커 장애.** 브로커를 멈춘 동안 요청을 계속 보내고, 요청이 성공하는지, 복구 후 쌓인 사건이 순서대로 나가는지 본다.
- **릴레이 중복.** 폴링 릴레이가 발행 확인을 받은 직후, 표시 전에 죽이고 중복 발행과 소비자의 중복 처리를 본다.
- **커넥터 정지(CDC).** Debezium을 멈추고 DB 쓰기를 계속해 `pg_wal` 크기와 슬롯 지연이 커지는 것을 본다. 재시작 후 중복 사건 수를 센다.
- **복구 원천 상실.** 별도 실험 DB에서 outbox 삭제와 필요한 WAL 제거가 겹친 상황을 만들고, 스냅샷에 없는 사건을 확인한다. 보관소 또는 재구성 절차로 복구한 뒤 사건 ID를 대조하고 손실 범위와 복구 시간을 기록한다.
- 재현은 [Testcontainers](../verify/testcontainers.md)로 PostgreSQL, Kafka, Debezium 컨테이너를 함께 띄운다.

## 측정과 검증

- **정합성은 전수 대조한다.** 실험 후 업무 행과 소비한 사건을 키로 맞춰 센다.
  - 업무 행만 있는 수, 사건만 있는 수: 0이어야 한다.
  - 두 번 반영된 수: 소비자 멱등 처리 후 0이어야 한다.
- **발행 지연.** outbox 기록 시각과 소비 시각의 차이를 p50, p99로 본다. 폴링은 폴링 주기가, CDC는 커넥터 지연이 주된 요인이다.
- **슬롯 지연과 WAL 크기(CDC).** `pg_current_wal_lsn()`과 슬롯 `confirmed_flush_lsn`의 차이, `pg_wal` 디렉터리 크기를 추세로 본다.
- **outbox 적체(폴링).** 미발행 행 수와 가장 오래된 미발행 행의 나이를 본다.

## 재검토 조건

- 외부 사건 발행이 사라지고 같은 DB의 작업자만 남았다. 업무 변경과 작업 생성을 같은 트랜잭션으로 처리할 수 있으면 DB 작업 큐로 단순화한다.
- CDC 장애 복구·로그 보관 부담이 크고 폴링으로 전달 지연과 DB 부하 목표를 맞출 수 있다. 폴링 발행으로 전환한다.
- 폴링 부하가 업무 쿼리에 영향을 준다. CDC로 옮긴다.

## 출처

- Debezium, [Outbox Event Router](https://github.com/debezium/debezium/blob/main/documentation/modules/ROOT/pages/transformations/outbox-event-router.adoc): outbox 패턴의 목적, 테이블 구조, `INSERT` 전용 가정과 `DELETE` 필터, 사건 ID 헤더.
- Debezium, [PostgreSQL connector](https://github.com/debezium/debezium/blob/main/documentation/modules/ROOT/pages/connectors/postgresql.adoc): 장애 복구 중 중복 가능성, 슬롯의 WAL 보존, WAL 디스크 사용 급증과 heartbeat.
- PostgreSQL, [Logical Decoding Concepts](https://github.com/postgres/postgres/blob/master/doc/src/sgml/logicaldecoding.sgml): 복제 슬롯이 연결 없이도 WAL과 카탈로그 행 제거를 막고 극단적으로 DB 정지까지 갈 수 있다는 경고.
- PostgreSQL, [Server Configuration](https://github.com/postgres/postgres/blob/master/doc/src/sgml/config.sgml): `max_slot_wal_keep_size` 기본값 -1.
- PostgreSQL 18, [Logical Decoding Concepts](https://www.postgresql.org/docs/18/logicaldecoding-explanation.html): 슬롯의 재전송과 필요한 WAL 제거 시 이어받기의 제약. 2026-09-29 원문 확인. 삭제된 사건의 복구 원천에 관한 결론은 이 조건을 적용한 설계 검토다.
- Apache Kafka, [Design](https://github.com/apache/kafka/blob/4.3.1/docs/design/design.md): 외부 시스템으로의 exactly-once와 2단계 커밋의 한계.
