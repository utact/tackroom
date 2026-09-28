# Airflow

확인: 2026-09-27, Apache Airflow 3.3.2 문서와 설정 템플릿(`config.yml`) 기준.

## 요약

Airflow는 여러 단계의 작업과 그 사이의 의존성을 Python 코드(Dag)로 정의하고, 스케줄러가 각 실행(Dag run)의 작업을 순서대로 실행하며 상태를 메타데이터 DB에 기록하는 워크플로 도구다.
실행마다 처리 대상 구간(data interval)이 붙어서, 과거 구간을 다시 실행(backfill)하거나 실패한 단계만 다시 돌리는 운영이 핵심 가치다.
작업 자체를 처리하는 엔진이 아니라, 다른 시스템의 작업을 순서대로 부르고 지켜보는 조율자다.

## 문제 신호

- 추출 → 정제 → 적재 → 집계 → 보고처럼 여러 단계가 앞 단계의 완료에 의존한다.
- 단계들이 서로 다른 시스템(DB, 객체 저장소, 외부 API, Spark, dbt)에 걸쳐 있다.
- "지난달 3일치를 다시 계산해야 한다"는 요청이 자주 온다.
- 어느 단계가 언제 실패했고 몇 번 재시도했는지 운영자가 화면에서 봐야 한다.
- cron 작업이 서로의 완료 시각을 짐작해 시간차로 이어져 있다.

## 기준선의 한계

- cron으로 단계마다 시각을 어긋나게 두면, 앞 단계가 늦거나 실패해도 뒤 단계가 돈다.
- 하나의 스크립트로 전부 이으면 중간 단계만 다시 돌릴 수 없다.
- 과거 구간 재실행을 위해 스크립트마다 날짜 인자와 반복문을 따로 만든다.
- 실행 이력과 단계별 로그가 흩어진다.

## 원리

- **Dag와 작업.** 작업(task)과 작업 사이의 의존성을 방향 비순환 그래프로 정의한다. 스케줄러는 의존성이 충족된 작업만 실행기(executor)로 보낸다.
- **Dag run과 data interval.** 시간 기반 스케줄의 각 실행은 처리할 구간을 갖고, 그 구간이 끝난 뒤에 예약된다. 1일 스케줄이면 어제 구간의 실행이 오늘 자정 이후에 돈다.
- **catchup과 backfill.**
  - Airflow 3에서 `catchup` 기본값은 False라, 활성화 전의 놓친 구간을 자동으로 만들지 않는다.
  - 과거 구간은 CLI나 REST API의 backfill로 만든다. 이미 있는 실행의 처리 방식(none, failed, completed)과 동시 실행 수를 정한다.
- **재시도.** 작업 재시도 기본값은 0이다(`default_task_retries`). 작업마다 `retries`, `retry_delay`를 지정한다.
- **동시성 상한.** Dag당 동시 실행 수 기본 16(`max_active_runs_per_dag`) 등 여러 층의 상한이 있다.
- **구성 요소(Airflow 3).** 스케줄러, Dag 파일을 파싱해 DB에 직렬화하는 Dag processor, REST API와 UI를 제공하는 API 서버, 메타데이터 DB가 기본이다. 작업은 task SDK로 API 서버와 통신하며, 메타데이터 DB에 직접 접근하지 않는다.
- **Dag 파일은 반복해서 파싱된다.** Dag processor는 작업 밖의 최상위 코드를 주기적으로 실행한다. 문서는 최상위에 무거운 코드나 import를 두지 말라고 강조한다.

## 가치

Airflow의 가치는 **"어느 구간의 어느 단계가 끝났는가"를 기록하고, 그 단위로 다시 실행하게 하는 것**이다.

- 의존성이 코드로 명시돼 앞 단계가 끝나야 뒤 단계가 돈다.
- 구간 단위 실행 덕분에 "3일치 재계산"이 backfill 한 번이다. 실패한 단계만 다시 실행(clear)할 수 있다.
- 실행 이력, 단계별 로그, 재시도, 소요 시간이 UI와 API로 보인다.
- 수많은 외부 시스템 연동(provider)이 있어 조율 코드를 적게 쓴다.

그래서 Airflow가 맞는 상황은 데이터 파이프라인처럼 구간 단위로 처리하고 다시 처리할 일이 많은 경우다.
단일 서비스 안의 정기 작업 몇 개에는 과하다.

## 트레이드오프와 리스크

- **작업이 멱등하지 않으면 재실행 가치가 사라진다.** 문서의 모범 사례는 재실행 때 `INSERT` 대신 UPSERT를 쓰고, "최신 데이터"가 아니라 특정 구간(파티션)을 읽고 쓰며, 작업 안에서 `now()`로 중요한 계산을 하지 말라고 한다. 이 규칙을 어기면 backfill이 중복과 불일치를 만든다.
- **운영할 구성 요소가 많다.** 스케줄러, Dag processor, API 서버, 메타데이터 DB, 실행기(Celery라면 브로커와 워커, Kubernetes라면 파드)를 운영해야 한다.
- **스케줄 지연.** Airflow는 실시간 시스템이 아니다. 작업 사이에 스케줄링 지연이 있어 짧은 작업이 많은 파이프라인은 대기 시간이 실행 시간보다 길 수 있다.
- **Dag 파싱 비용.** 최상위 코드가 무거우면 파싱이 느려지고 스케줄러 전체가 느려진다. 파일 파싱에는 시간 상한(`dagbag_import_timeout`, 기본 30초)이 있다.
- **큰 데이터를 작업 사이로 넘기면 안 된다.** 작업 사이 메시지(XCom)는 작은 값용이다. 문서는 큰 데이터는 원격 저장소에 두고 경로만 넘기라고 한다.
- **시간 의미론이 헷갈린다.** 논리 날짜(logical date)는 구간의 시작이지 실행 시각이 아니다. 이를 모르고 날짜를 쓰면 하루씩 어긋난다.
- **버전 이행 비용.** Airflow 3은 작업의 DB 직접 접근 제거, 기본값 변경(catchup) 등 2.x와 다른 점이 많다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| [Spring 스케줄러와 ShedLock](spring-scheduler-shedlock.md), [Quartz](quartz.md) | 단계 간 의존성이 없거나 한 서비스 안에서 끝난다. |
| [Spring Batch](spring-batch.md) | 한 단계 안에서 대량 항목을 나눠 처리하고 재개해야 한다. Airflow의 한 작업으로 Spring Batch Job을 부를 수 있다. |
| Kubernetes CronJob + 간단한 스크립트 | 단계가 둘셋이고 backfill이 드물다. |
| Dagster, Prefect | 데이터 자산 중심 모델이나 다른 개발 경험을 원한다. (미검증: 이 조사에서는 비교하지 않았다.) |
| [Flink](../data/flink.md) | 구간 배치가 아니라 연속 스트림으로 처리해야 한다. |

## 깊이 있는 활용

- **작업을 "구간 → 결과 파티션" 함수로 만든다.** 작업은 data interval을 입력으로 받아 그 구간만 읽고, 결과를 그 구간의 파티션에 덮어쓴다(파티션 교체나 UPSERT). 같은 구간을 몇 번 돌려도 결과가 같아진다. backfill과 재실행이 안전해진다.
- **`now()` 대신 구간 값을 쓴다.** 날짜 계산은 `data_interval_start`, `data_interval_end`로 한다. 논리 날짜가 구간의 시작이라는 점을 감안한다.
- **Airflow는 부르기만 한다.** 무거운 처리는 DB, Spark, dbt, 컨테이너에서 하고, 작업은 호출과 결과 확인만 한다. 워커 자원과 처리 자원이 분리된다.
- **catchup은 끄고 backfill은 명시적으로 한다.** 새 Dag를 켤 때 수백 개 과거 실행이 몰리는 것을 막는다. 과거 구간이 필요하면 backfill의 동시 실행 수(`max_active_runs`)를 낮게 걸어 하위 시스템을 보호한다.
- **재시도는 작업마다 정한다.** 기본 재시도 0이다. 외부 API 호출처럼 일시적 실패가 있는 작업은 재시도와 지연을 두고, 데이터 검증 작업은 재시도하지 않는다.
- **기다리는 작업은 deferrable로 만든다.** 외부 조건을 기다리는 센서가 워커 슬롯을 쥐고 있지 않게, 기다림을 triggerer로 넘기는 deferrable 연산자를 쓴다.
- **사건 기반 스케줄을 쓴다.** 시간이 아니라 "이 데이터(asset)가 갱신됐을 때"로 다음 Dag를 실행하면, 상류 Dag의 완료 시각을 짐작할 필요가 없다.
- **Dag 파일은 가볍게.** 무거운 import와 계산은 작업 함수 안으로 옮긴다. 파싱 시간을 CI에서 잰다.

## 임시방책의 신호

- 작업이 "오늘 날짜"나 "최신 데이터"를 읽는다. backfill이 전부 같은 결과를 낸다.
- 재실행하면 중복 행이 쌓여서, 재실행 전에 사람이 행을 지운다.
- 큰 DataFrame을 XCom으로 넘긴다.
- Dag 파일 최상위에서 DB나 API를 호출해 Dag 목록을 만든다.
- 뒤 단계를 앞 단계 예상 종료 시각 뒤로 cron을 어긋나게 둔다(Airflow 안에서도).
- 모든 작업에 같은 큰 재시도 횟수를 건다.

## 실패 재현

- **재실행 멱등성.** 같은 구간을 두 번 실행해 결과 테이블의 행 수와 값이 같은지 본다. `INSERT` 버전과 파티션 교체 버전을 비교한다.
- **입력 변경 중 재실행.** 입력 데이터를 바꾼 뒤 과거 구간을 재실행해, "최신 읽기" 작업은 결과가 바뀌고 "구간 읽기" 작업은 그대로인지 본다.
- **중간 단계 실패.** 가운데 작업을 실패시키고 그 작업만 다시 실행(clear)해 뒤 단계가 이어지는지, 앞 단계는 다시 돌지 않는지 본다.
- **catchup 폭주.** `catchup=True`로 오래전 `start_date`의 Dag를 켜고 생성되는 실행 수와 하위 시스템 부하를 본다.
- **파싱 지연.** 최상위에 느린 호출을 넣어 Dag 파싱 시간과 스케줄 지연이 늘어나는 것을 본다.
- 로컬 재현은 공식 Docker Compose나 `airflow standalone`으로 하고, 작업 단위 테스트는 `dag.test()`로 한다.

## 측정과 검증

- **정합성은 구간별로 대조한다.** 구간마다 입력 건수와 결과 건수, 합계 같은 불변량을 기록하고 재실행 전후를 비교한다.
- **스케줄 지연.** 작업의 예정 시각(또는 의존 작업 완료 시각)과 실제 시작 시각의 차이를 본다. 작업 실행 시간 대비 대기 비율이 크면 Airflow가 병목이다.
- **파이프라인 SLA.** 구간 종료부터 최종 결과 준비까지의 시간을 Dag run별로 기록하고 p95를 본다.
- **실패와 재시도.** 작업별 실패율, 재시도 후 성공률을 본다. 재시도 후에도 실패하는 작업은 재시도가 아니라 수정이 필요하다.
- **Dag 파싱 시간.** Dag processor의 파일별 파싱 시간을 추세로 본다.

## 재검토 조건

- 파이프라인이 단계 하나로 줄었거나 backfill을 쓰지 않는다.
- 지연 요구가 분 단위 이하로 짧아졌다. 스트림 처리를 검토한다.
- Airflow 운영 비용이 조율하는 작업의 가치를 넘는다. 관리형 서비스나 더 단순한 도구를 검토한다.

## 출처

- Apache Airflow 3.3.2, [Dag Runs](https://github.com/apache/airflow/blob/3.3.2/airflow-core/docs/core-concepts/dag-run.rst): data interval, catchup 기본값 False.
- Apache Airflow 3.3.2, [Backfill](https://github.com/apache/airflow/blob/3.3.2/airflow-core/docs/core-concepts/backfill.rst): 재처리 옵션과 동시성 제어.
- Apache Airflow 3.3.2, [Best Practices](https://github.com/apache/airflow/blob/3.3.2/airflow-core/docs/best-practices.rst): UPSERT, 특정 파티션 읽기·쓰기, `now()` 금지, XCom은 작은 값, 최상위 코드 피하기.
- Apache Airflow 3.3.2, [Architecture Overview](https://github.com/apache/airflow/blob/3.3.2/airflow-core/docs/core-concepts/overview.rst): Dag processor, Dag bundle, API 서버, task SDK, 메타데이터 DB.
- Apache Airflow 3.3.2, [config.yml](https://github.com/apache/airflow/blob/3.3.2/airflow-core/src/airflow/config_templates/config.yml): `default_task_retries` 0, `max_active_runs_per_dag` 16, `dagbag_import_timeout` 30초.
