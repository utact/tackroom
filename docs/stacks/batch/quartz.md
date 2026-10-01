# Quartz

확인: 2026-09-27, Quartz 2.5.2 소스, quartz-scheduler.org-site 저장소의 2.3.0 문서(최신 공개 문서), Spring Boot 4.1.1 소스 기준.

## 요약

Quartz는 작업(Job)과 실행 시점 규칙(Trigger)을 분리해 저장하고, 정해진 때에 스레드 풀에서 실행하는 Java 스케줄러다.
JDBC 작업 저장소를 쓰면 여러 노드가 같은 DB를 공유해 한 번의 발화를 한 노드만 실행하고, 노드가 죽으면 다른 노드가 이어받는다.
[Spring 스케줄러와 ShedLock](spring-scheduler-shedlock.md)과 달리 놓친 실행(misfire)을 어떻게 처리할지 정책으로 정할 수 있다.

## 문제 신호

- 놓친 실행을 보충하거나, 반대로 확실히 건너뛰어야 한다.
- 사용자나 관리자가 실행 중에 스케줄을 추가·변경·일시정지한다(예: 고객별 보고서 발송 시각).
- 작업 수가 수십~수천 개이고, 작업마다 다른 규칙과 데이터를 가진다.
- 여러 노드에 부하를 나누면서 한 발화는 한 번만 실행해야 한다.

## 기준선의 한계

- OS cron과 `@Scheduled`는 스케줄이 코드나 설정에 고정돼 있다. 실행 중에 바꾸려면 배포가 필요하다.
- `@Scheduled` + ShedLock은 놓친 실행을 다시 하지 않고, 잠금이 잡혀 있으면 건너뛴다. 실행 이력이 없다.
- 작업이 많아지면 스케줄 작업마다 코드와 잠금 이름이 늘어난다.

## 원리

- **Job과 Trigger의 분리.** Job은 "무엇을", Trigger는 "언제"다. 하나의 Job에 여러 Trigger를 붙일 수 있고, Job마다 데이터(`JobDataMap`)를 가진다.
- **작업 저장소.** 메모리 저장소(RAMJobStore)는 재시작하면 스케줄을 잃고, JDBC 저장소는 Job, Trigger, 발화 상태를 DB에 둔다. Spring Boot의 기본값은 메모리다.
- **클러스터링.** JDBC 저장소에서 `isClustered=true`로 여러 노드가 테이블을 공유한다. 발화 때 Trigger를 먼저 잠근 노드 하나만 실행한다.
- **장애 조치.** 노드가 실행 중에 죽으면 다른 노드가 이를 감지한다. "복구 요청(requests recovery)" 표시가 있는 Job은 남은 노드가 다시 실행하고, 없는 Job은 다음 발화 때 실행된다.
- **misfire.** 발화 시각을 `misfireThreshold`(기본 60초) 넘게 지나친 경우다. 스레드가 모두 바쁘거나 스케줄러가 꺼져 있을 때 생긴다.
  - Trigger마다 misfire 지시(즉시 한 번, 다음부터, 놓친 만큼)를 고른다.
  - 기본값인 smart policy는 CronTrigger에서 "지금 한 번 실행"이다.
- **동시 실행 제어.** `@DisallowConcurrentExecution`은 같은 Job 정의(JobKey)의 인스턴스가 동시에 실행되지 않게 한다. 클래스 단위가 아니라 Job 정의 단위다.

## 가치

Quartz의 가치는 **스케줄 자체를 데이터로 관리하고, 놓친 실행의 처리 방식을 명시하는 것**이다.

- 스케줄을 실행 중에 추가하고 바꾸고 멈출 수 있다. 사용자별 스케줄 같은 요구를 코드 변경 없이 받는다.
- misfire 정책으로 "배포 중 놓친 정산은 다시 돈다", "놓친 알림은 보내지 않는다"를 작업마다 정한다.
- 클러스터링이 발화 단위의 중복 방지와 장애 조치를 함께 준다.

- **학습 실험.** 정기 보고서 작업을 두 스케줄러 인스턴스로 실행한다. 실행 중 종료와 예정 시각을 넘긴 중단을 재현해 중복·misfire를 계수하고, 스케줄 복구와 업무의 정확히 한 번 반영을 구분한다.

## 트레이드오프와 리스크

- **클러스터는 전역 잠금을 쓴다.** 공식 문서는 노드를 약 세 개 넘게 늘리면 클러스터 전역 잠금 때문에 성능이 떨어진다고 적는다. 1초짜리 짧은 작업 수천 개에는 스케줄러를 나누라고 권한다.
- **시계 동기화가 필수다.** 문서는 노드 시계가 1초 이내로 맞지 않으면 클러스터링을 쓰지 말라고 경고한다.
- **비클러스터 인스턴스를 같은 테이블에 띄우면 데이터가 깨진다.** 문서의 명시적 경고다. 로컬 개발 인스턴스가 운영 DB를 보면 사고가 난다.
- **misfire 기본 동작을 모르면 놀란다.** smart policy의 동작은 Trigger 종류와 설정에 따라 다르다. 몇 시간 꺼져 있던 스케줄러가 켜지면서 한꺼번에 실행하거나, 반대로 조용히 건너뛸 수 있다.
- **DB 테이블 11개 남짓과 스키마 관리.** 버전을 올릴 때 테이블 변경이 따라온다. [Flyway](../state/schema-migration.md)로 함께 관리해야 한다.
- **메모리 저장소 기본값.** Spring Boot에서 설정을 바꾸지 않으면 재시작 때 동적으로 추가한 스케줄이 사라진다.
- **스레드 풀 크기가 동시 실행의 상한이다.** 풀이 바쁘면 발화가 밀려 misfire가 된다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| [Spring 스케줄러와 ShedLock](spring-scheduler-shedlock.md) | 스케줄이 고정돼 있고 수가 적다. 놓친 실행은 작업이 상태로 메운다. |
| [DB 작업 큐](../async/db-job-queue.md), db-scheduler, JobRunr | 작업이 사건으로도 생기고, 재시도와 죽은 작업 감지, 대시보드가 필요하다. |
| [Airflow](airflow.md) | 단계 간 의존성, 과거 구간 재실행(backfill), 실행 이력 화면이 핵심이다. |
| Kubernetes CronJob | 작업을 별도 컨테이너로 격리한다. 동적 스케줄은 API로 CronJob을 만들어야 한다. |

## 깊이 있는 활용

- **JDBC 저장소와 클러스터를 운영에서는 기본으로 둔다.** Spring Boot에서 `spring.quartz.job-store-type=jdbc`로 바꾸고, 스키마는 마이그레이션 도구로 관리한다.
- **misfire 지시를 작업마다 명시한다.** 정산처럼 반드시 해야 하는 작업은 "즉시 실행"(CronTrigger의 `withMisfireHandlingInstructionFireAndProceed`), 알림처럼 늦으면 무의미한 작업은 "건너뛰고 다음부터"(`withMisfireHandlingInstructionDoNothing`)로 정한다. 기본값에 맡기지 않는다.
- **복구 요청은 멱등한 작업에만 켠다.** 노드 사망 후 재실행되므로 같은 작업이 두 번 돌 수 있다.
- **긴 작업은 Quartz 스레드에서 오래 쥐지 않는다.** Quartz는 시작만 하고, 실제 처리는 [Spring Batch](spring-batch.md)나 작업 큐로 넘긴다. 스레드 풀이 막혀 다른 발화가 misfire되는 것을 막는다.
- **Job 정의 단위의 동시 실행 제어를 이해한다.** 고객별로 Job 정의를 나누면 `@DisallowConcurrentExecution`은 고객 단위로 동작한다. 전체를 하나로 막고 싶으면 Job 정의를 하나로 둔다.
- **스케줄러를 목적별로 나눈다.** 짧고 잦은 작업과 길고 드문 작업을 같은 스케줄러에 두지 않는다. 테이블 접두어(`tablePrefix`)나 스케줄러 이름으로 나눈다.

## 임시방책의 신호

- 메모리 저장소로 운영하다 재시작 뒤 스케줄이 사라져 수동으로 다시 등록한다.
- misfire 정책을 모른 채 쓰다가, 배포 뒤 작업이 한꺼번에 몰려 실행된다.
- 클러스터 노드 수를 늘려 처리량을 올리려다 전역 잠금 경합으로 오히려 느려진다.
- 개발 PC의 Quartz가 운영 DB를 바라본다.
- 긴 작업이 Quartz 스레드를 몇 시간씩 쥔다.

## 실패 재현

- **재시작 손실.** 메모리 저장소에서 스케줄을 동적으로 추가하고 재시작해 사라지는 것을 본다.
- **misfire.** 스케줄러를 발화 시각을 넘겨 몇 분간 멈췄다가 켜고, 지시별(기본, 즉시 실행, 무시)로 실행 횟수를 센다.
- **스레드 기아.** 스레드 풀을 1로 두고 긴 작업과 짧은 작업을 함께 스케줄해, 짧은 작업이 misfire되는 것을 본다.
- **노드 사망.** 클러스터에서 작업 실행 중인 노드를 죽이고, 복구 요청 유무에 따라 다른 노드가 다시 실행하는지 본다.
- **시계 차이.** 노드 하나의 시계를 수 초 틀어 놓고 발화가 두 번 일어나거나 지연되는지 본다.

## 측정과 검증

- **발화 정확성.** 발화 기록(Quartz의 `JobListener`나 별도 테이블)으로 예정 발화별 실행 횟수를 센다. 0과 2 이상을 센다.
- **발화 지연.** 예정 시각과 실제 시작 시각의 차이를 분포로 본다. `misfireThreshold`에 가까워지면 스레드나 스케줄러를 늘릴 때다.
- **클러스터 확장성.** 노드 수를 1, 2, 3, 5로 바꿔 가며 초당 발화 처리량과 잠금 대기 시간을 잰다. 전역 잠금이 병목이 되는 지점을 찾는다.

## 재검토 조건

- 짧은 작업이 초당 수백 건으로 늘어 전역 잠금이 병목이다.
- 작업 사이의 의존성과 재실행 요구가 늘었다. 워크플로 도구로 옮긴다.
- 스케줄이 고정되고 수가 줄었다. ShedLock으로 단순화한다.

## 출처

- Quartz 2.3.0 문서, [Configure Clustering with JDBC-JobStore](https://github.com/quartz-scheduler/quartz-scheduler.org-site/blob/master/documentation/quartz-2.3.0/configuration/ConfigJDBCJobStoreClustering.md): 발화 단위 단일 실행, 장애 조치와 복구 요청, 약 세 노드 이상의 전역 잠금 성능 저하, 시계 1초 이내 동기화, 비클러스터 인스턴스 경고.
- Quartz 2.3.0 문서, [JobStoreTX 설정](https://github.com/quartz-scheduler/quartz-scheduler.org-site/blob/master/documentation/quartz-2.3.0/configuration/ConfigJobStoreTX.md): `misfireThreshold` 기본 60초.
- Quartz 2.3.0 튜토리얼, [Lesson 3](https://github.com/quartz-scheduler/quartz-scheduler.org-site/blob/master/documentation/quartz-2.3.0/tutorials/tutorial-lesson-03.md), [Lesson 4](https://github.com/quartz-scheduler/quartz-scheduler.org-site/blob/master/documentation/quartz-2.3.0/tutorials/tutorial-lesson-04.md), [Lesson 6](https://github.com/quartz-scheduler/quartz-scheduler.org-site/blob/master/documentation/quartz-2.3.0/tutorials/tutorial-lesson-06.md): `@DisallowConcurrentExecution`의 적용 단위, smart policy 기본값과 CronTrigger 해석.
- Spring Boot 4.1.1 소스, [QuartzProperties.java](https://github.com/spring-projects/spring-boot/blob/v4.1.1/module/spring-boot-quartz/src/main/java/org/springframework/boot/quartz/autoconfigure/QuartzProperties.java): 저장소 기본값 `MEMORY`.
- 최신 릴리스는 [Quartz v2.5.2](https://github.com/quartz-scheduler/quartz/tree/v2.5.2)다. 공개 문서는 2.3.0 기준이라, 2.5에서 바뀐 동작이 있을 수 있다.
