# Spring Batch

확인: 2026-09-27, Spring Batch 6.0.5 문서(spring-batch-docs) 기준.

## 요약

Spring Batch는 대량의 항목을 읽고, 가공하고, 쓰는 일을 청크 단위 트랜잭션으로 나눠 실행하고, 그 진행 상태를 메타데이터 저장소에 기록한다.
실패하면 마지막으로 커밋된 청크 다음부터 다시 시작할 수 있다.
"언제 실행할지"가 아니라 "많은 일을 어떻게 끝까지, 다시 할 수 있게 할지"를 푸는 도구다.

## 문제 신호

- 수십만~수억 건을 한 번에 처리하는 작업(정산, 이관, 대량 알림, 파일 적재)이 있다.
- 처리 중간에 실패하면 처음부터 다시 돌려야 하고, 그러면 이미 처리한 건이 두 번 처리된다.
- 일부 불량 레코드 때문에 전체 작업이 실패한다.
- 한 트랜잭션으로 전체를 처리하다 DB 잠금과 메모리 문제가 생겼다.

## 기준선의 한계

기준선은 "스케줄 메서드 안에서 반복문으로 전부 처리하는" 방식이다.

- 전체를 한 트랜잭션으로 묶으면 긴 트랜잭션, 큰 undo, 잠금 경합이 생긴다. 건마다 커밋하면 느리다.
- 어디까지 처리했는지 기록하지 않으면 재시작 지점이 없다.
- 불량 레코드 하나가 예외를 던지면 전체가 멈춘다. 건너뛰기와 재시도를 직접 만들어야 한다.
- 실행 이력(언제, 몇 건, 무엇이 실패)이 없다.

## 원리

- **JobInstance와 JobExecution.** `JobInstance = Job + 식별 JobParameters`다. 같은 식별 파라미터로 다시 실행하면 JobExecution만 새로 생기고, 한 JobInstance는 동시에 하나만 돈다.
- **청크 지향 처리.** 항목을 하나씩 읽고 가공해 청크(commit interval)만큼 모으면 한 트랜잭션으로 쓰고 커밋한다. 6.0에서 `ChunkOrientedStep`이 새 구현으로 안정화됐다.
- **상태 저장.** 기본 reader와 writer는 쓰기와 같은 트랜잭션에서 현재 위치를 `ExecutionContext`에 저장하고, 재시작하면 그 위치부터 읽는다.
- **건너뛰기와 재시도.** 결정적인 예외(파싱 실패)는 건너뛰기 한도 안에서 건너뛰고, 일시적 예외(데드락)는 재시도한다. 문서는 둘을 이렇게 구분하라고 설명한다.
- **메타데이터 저장소.** 실행 기록과 `ExecutionContext`를 저장한다. 6.0부터 기본 저장소는 아무것도 남기지 않는 resourceless이고, JDBC 저장소는 `@EnableJdbcJobRepository`로 켠다.
- **동시성.** 6.0의 동시 청크 처리는 제한된 큐를 둔 생산자-소비자 모델이다. 멀티스레드 step의 processor는 스레드 안전해야 한다.

## 가치

Spring Batch의 가치는 **대량 처리를 "다시 실행해도 안전한" 단위로 쪼개고, 그 경계를 기록하는 것**이다.

- 실패 지점부터 재개하므로, 실패가 전체 재실행 비용이 되지 않는다.
- 청크 크기로 트랜잭션 크기와 처리량의 균형을 조절한다.
- 불량 레코드를 건너뛰고 기록해 나머지를 끝까지 처리한다.
- 실행 이력과 건수가 메타데이터로 남아, 운영자가 무엇이 언제 몇 건 처리됐는지 조회한다.

## 트레이드오프와 리스크

- **재시작은 저장소가 있어야 한다.** 기본 resourceless 저장소로는 재시작 의미론이 없다. JDBC 저장소를 켜야 "재시작 가능한 배치"다.
- **재시작 위치는 reader의 정렬을 전제로 한다.** 페이징 reader는 정렬 키에 유일 제약이 있어야 실행 사이에 데이터를 잃지 않는다고 문서가 적는다. 정렬이 불안정하면 재시작 때 건너뛰거나 중복한다.
- **청크 단위 커밋은 청크 안의 부분 실패를 다시 처리한다.** 청크 쓰기 중 실패하면 그 청크의 항목이 다시 처리된다. 외부 부작용(메일 발송, 외부 API)은 두 번 일어날 수 있다.
- **처리 중 데이터가 바뀐다.** 긴 배치 동안 원본이 바뀌면 오프셋 기반 페이징은 행을 건너뛰거나 두 번 읽는다.
- **식별 파라미터 설계가 운영 방식을 정한다.** 같은 날짜로 성공한 JobInstance는 다시 실행되지 않는다(이미 완료). 재실행을 원하면 식별되지 않는 파라미터를 쓰거나 새 식별값이 필요하다.
- **메타데이터 테이블과 버전 이행.** 메이저 버전마다 스키마와 API가 바뀐다. 6.0은 XML 네임스페이스와 Jackson 2 지원을 폐기 예정으로 두었다.
- **프레임워크 개념의 학습 비용.** Job, Step, Chunk, ItemStream, ExecutionContext, 리스너, 파티셔닝을 이해해야 제대로 쓴다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| 반복문 + 진행 표시 컬럼 | 한 번 도는 작은 작업이다. 처리 여부 컬럼(`processed`)과 `WHERE processed = false`로도 재실행이 안전해진다. |
| [DB 작업 큐](../async/db-job-queue.md) | 항목이 계속 들어오고, 항목마다 독립적으로 처리·재시도한다. |
| [Airflow](airflow.md) | 여러 시스템에 걸친 단계 간 의존성과 과거 구간 재실행이 핵심이다. Spring Batch 작업을 Airflow의 한 단계로 부를 수 있다. |
| [Flink](../data/flink.md), Spark | 데이터가 한 노드에서 처리하기에 너무 크거나, 연속 스트림이다. |

실행 시점은 Spring Batch가 정하지 않는다.
[Spring 스케줄러와 ShedLock](spring-scheduler-shedlock.md), [Quartz](quartz.md), Kubernetes CronJob, Airflow가 Job을 실행시킨다.

## 깊이 있는 활용

- **JDBC 저장소를 명시적으로 켠다.** 운영 배치는 `@EnableJdbcJobRepository`와 메타데이터 스키마를 둔다. 스키마는 [Flyway](../state/schema-migration.md)로 관리한다.
- **식별 파라미터를 업무 단위로 정한다.** 처리 기준일을 식별 파라미터로 두면 같은 날짜는 한 번만 성공하고, 두 번째 실행은 거부된다. 실행 시각 같은 값은 식별하지 않는다.
- **keyset 페이징과 유일 정렬 키를 쓴다.** 기본 키처럼 유일하고 변하지 않는 키로 정렬한다. 오프셋이 아니라 "마지막으로 읽은 키 이후"로 읽으면 데이터 변경에 덜 흔들린다.
- **처리 표시 패턴으로 재실행을 쉽게 한다.** 원본의 처리 여부 컬럼을 읽기 조건에 넣고 `saveState(false)`로 위치 저장을 끈다. 재시작하면 처리 안 된 행만 읽힌다.
- **쓰기는 멱등하게 만든다.** 청크 재처리가 일어나므로 `INSERT ... ON CONFLICT`나 upsert로 쓴다. 외부 부작용은 [Outbox](../async/outbox-cdc.md)에 기록하고 따로 보낸다.
- **건너뛰기와 재시도를 예외 성격으로 나눈다.** 데이터 오류는 skip하고 리스너로 격리 테이블에 남기며, 데드락·타임아웃은 retry한다. 건너뛰기 한도는 원본 이상을 판단하는 기준이다.
- **청크 크기는 측정으로 정한다.** 청크를 키우면 커밋 수가 줄어 빨라지지만 트랜잭션과 재처리 범위가 커진다. 100, 500, 1000, 5000 정도로 바꿔 가며 처리량과 잠금 대기를 잰다.
- **확장은 파티셔닝으로 한다.** 키 범위로 데이터를 나눠 파티션마다 독립 step으로 실행하면, 파티션별로 재시작 상태를 가진다. 멀티스레드 step은 기본 reader가 스레드 안전하지 않은 경우가 많고 재시작 상태가 섞인다.
- **실패 복구 API를 쓴다.** 6.0부터 `JobOperator.recover`로 비정상 종료된 실행을 DB를 손대지 않고 복구한다. 이전에는 메타데이터 테이블을 SQL로 고쳐야 했다.

## 임시방책의 신호

- 배치가 실패하면 처리된 데이터를 손으로 지우고 처음부터 다시 돌린다.
- 전체를 `@Transactional` 메서드 하나로 처리한다.
- 불량 레코드를 만나면 예외를 잡아 로그만 남기고 계속한다. 무엇을 건너뛰었는지 기록이 없다.
- 오프셋 페이징(`LIMIT/OFFSET`)으로 읽으면서 같은 테이블을 갱신한다.
- 재실행을 위해 식별 파라미터에 현재 시각을 넣는다. 같은 날짜가 두 번 성공할 수 있다.
- 6.0으로 올린 뒤 메타데이터 테이블이 비어 있는데 재시작이 되는 줄 안다.

## 실패 재현

- **중간 실패와 재시작.** 중간 항목에서 예외를 던지고 재시작한 뒤, 결과에 중복이나 누락이 없는지 대조한다. resourceless와 JDBC 저장소에서 각각 해 본다.
- **프로세스 강제 종료.** 청크 커밋 사이와 청크 쓰기 도중에 `kill -9`로 죽이고, 재시작 후 재처리된 범위를 확인한다.
- **정렬 불안정.** 유일하지 않은 정렬 키로 페이징하고, 같은 값이 페이지 경계에 걸치게 데이터를 만든다. 재시작 때 행이 빠지거나 겹치는지 본다.
- **처리 중 원본 변경.** 배치가 도는 동안 원본에 삽입·삭제를 하고, 오프셋 페이징과 keyset 페이징의 누락·중복을 비교한다.
- **불량 레코드.** 잘못된 형식의 레코드를 섞어 skip 동작과 한도 초과 시 실패를 본다.
- 재현은 [Testcontainers](../verify/testcontainers.md)로 실제 DB를 쓰고, `spring-batch-test`의 `JobOperatorTestUtils`(6.0 이전은 `JobLauncherTestUtils`)로 Job을 실행한다.

## 측정과 검증

- **정합성은 전수 대조한다.** 입력 건수 = 성공 건수 + 건너뛴 건수여야 한다. 결과 테이블의 키별 반영 횟수가 모두 1인지 본다.
- **처리량.** 초당 처리 항목 수를 청크 크기, 스레드·파티션 수에 따라 잰다. 메타데이터의 StepExecution에 읽기·쓰기·건너뛰기 수와 시작·종료 시각이 남는다.
- **자원 영향.** 배치 중 DB CPU, 잠금 대기, 업무 쿼리의 p99 지연을 본다. 배치가 업무 트래픽을 해치는 지점이 청크 크기와 병렬도의 상한이다.
- **재시작 비용.** 실패 시점별 재시작 후 추가 소요 시간을 잰다. 처음부터 다시 도는 것과 비교한다.

## 재검토 조건

- 데이터가 커져 한 노드로 시간 안에 끝나지 않는다. 분산 처리 엔진을 검토한다.
- 입력이 연속적으로 들어와 배치 주기가 지연 요구를 맞추지 못한다. 스트림 처리로 옮긴다.
- 작업이 작아 프레임워크 설정이 작업보다 크다. 처리 표시 컬럼 방식으로 단순화한다.

## 출처

- Spring Batch 6.0.5, [What's new in Spring Batch 6](https://github.com/spring-projects/spring-batch/blob/v6.0.5/spring-batch-docs/modules/ROOT/pages/whatsnew.adoc): resourceless 기본 저장소, `@EnableJdbcJobRepository`, `ChunkOrientedStep`, 생산자-소비자 동시성, `JobOperator.recover`, 폐기 예정 목록.
- Spring Batch 6.0.5, [The Domain Language of Batch](https://github.com/spring-projects/spring-batch/blob/v6.0.5/spring-batch-docs/modules/ROOT/pages/domain.adoc): JobInstance와 식별 파라미터, 동시 실행 제한.
- Spring Batch 6.0.5, [Preventing State Persistence](https://github.com/spring-projects/spring-batch/blob/v6.0.5/spring-batch-docs/modules/ROOT/pages/readers-and-writers/process-indicator.adoc): 처리 표시 패턴과 `saveState`.
- Spring Batch 6.0.5, [Database readers](https://github.com/spring-projects/spring-batch/blob/v6.0.5/spring-batch-docs/modules/ROOT/pages/readers-and-writers/database.adoc): 정렬 키의 유일 제약.
- Spring Batch 6.0.5, [Configuring Retry Logic](https://github.com/spring-projects/spring-batch/blob/v6.0.5/spring-batch-docs/modules/ROOT/pages/step/chunk-oriented-processing/retry-logic.adoc), [Scaling and Parallel Processing](https://github.com/spring-projects/spring-batch/blob/v6.0.5/spring-batch-docs/modules/ROOT/pages/scalability.adoc): 결정적·비결정적 예외 구분, 멀티스레드 step의 스레드 안전성.
