# 기술 스택 조사

기술 판단 스킬의 재료다.
AI가 맥락 없이 임시방책으로 문제를 넘기지 않고, 문제에 맞는 기술을 원리부터 이해해 고르고 깊이 쓰게 하는 것이 목적이다.
스킬은 이 조사를 요약해 만든다.
조사가 틀리면 스킬도 틀리므로, 주장마다 1차 출처와 확인 날짜를 남긴다.

## 목록을 고른 기준

- 문제 영역을 먼저 정하고, 영역마다 기술을 고른다. 영역은 기술이 지키는 성질(정합성, 전달 보장, 재실행, 검색 품질, 운영 가능성)로 나눈다.
- 영역마다 기준선을 둔다. 새 기술 없이 기존 도구로 어디까지 되는지가 모든 비교의 출발점이다.
- 영역마다 서로 경쟁하는 기술을 둘 이상 둔다. "왜 이 기술인가"는 대안이 있어야 답할 수 있다.
- 기술이 아닌 패턴(멱등 키, outbox)도 여러 기술에 걸쳐 쓰이면 따로 조사한다.
- 검증 도구와 통계도 한 영역으로 둔다. 선택의 근거는 측정으로 끝나기 때문이다.
- 스택은 Java·Spring 백엔드와 Python AI 작업을 기준으로 한다. 다른 언어의 동등한 도구는 각 문서의 대안에 적는다.

## 목록

| 영역 | 기준선 | 조사 대상 |
|---|---|---|
| 상태와 정합성 | RDB 제약 조건과 트랜잭션 | [PostgreSQL](state/postgresql.md), [MySQL InnoDB](state/mysql-innodb.md), [Flyway와 무중단 스키마 변경](state/schema-migration.md) |
| API와 동시성 | 타임아웃이 있는 단일 요청 | [타임아웃·재시도·멱등 키](api/timeout-retry-idempotency.md), [잠금 전략](api/locking.md), [Resilience4j](api/resilience4j.md) |
| 비동기 처리 | 요청 안에서 동기 처리 | [DB 작업 큐](async/db-job-queue.md), [RabbitMQ](async/rabbitmq.md), [Kafka](async/kafka.md), [Redis Streams](async/redis-streams.md), [Outbox와 CDC](async/outbox-cdc.md) |
| 정기·대량 처리 | OS cron | [Spring 스케줄러와 ShedLock](batch/spring-scheduler-shedlock.md), [Quartz](batch/quartz.md), [Spring Batch](batch/spring-batch.md), [Airflow](batch/airflow.md) |
| 조회와 검색 | 인덱스를 탄 SQL | [Redis 캐시](search/redis-cache.md), [Caffeine](search/caffeine.md), [Elasticsearch](search/elasticsearch.md), [pgvector](search/pgvector.md), [하이브리드 검색과 리랭킹](search/hybrid-rerank.md) |
| RAG와 LLM | 키워드 검색과 원문 제시 | [문서 파싱](rag/document-parsing.md), [청킹](rag/chunking.md), [임베딩 모델 선택](rag/embeddings.md), [LLM 평가](rag/llm-evaluation.md), [vLLM](rag/vllm.md) |
| 운영과 보안 | 단일 서버에 수동 배포 | [Docker](ops/docker.md), [GitHub Actions](ops/github-actions.md), [Kubernetes](ops/kubernetes.md), [OpenTelemetry](ops/opentelemetry.md), [Prometheus와 Grafana](ops/prometheus-grafana.md), [Nginx와 TLS](ops/nginx-tls.md), [OAuth 2.0과 JWT](ops/oauth-jwt.md) |
| 검증 | 수동 확인 | [k6](verify/k6.md), [Toxiproxy](verify/toxiproxy.md), [Testcontainers](verify/testcontainers.md), [측정 통계](verify/statistics.md) |
| 스트림 처리 | 배치 집계 | [Flink](stream/flink.md) |

## 조사 양식

모든 문서는 아래 순서를 따른다.
항목을 비우지 않는다.
모르면 모른다고 적고, 출처 없이 경험칙으로 적은 내용은 `(미검증)`을 붙인다.

| 항목 | 답할 질문 |
|---|---|
| 요약 | 어떤 문제를 어떤 원리로 푸는가? 한두 문장으로 쓴다. |
| 문제 신호 | 어떤 관찰이 있을 때 이 기술을 검토하는가? |
| 기준선의 한계 | 이 기술 없이 기존 도구로 어디까지 되고, 어디서 막히는가? |
| 원리 | 가치를 만드는 내부 구조는 무엇인가? 사용법이 아니라 구조를 쓴다. |
| 가치 | 그 원리가 어떤 상황에 붙을 때 대안보다 나은가? "왜 이 기술인가"의 답이다. |
| 트레이드오프와 리스크 | 도입하면 무엇을 잃는가? 새로 생기는 실패 방식, 운영 부담, 학습 비용, 되돌리기 어려움을 쓴다. |
| 대안과 경계 | 비슷해 보이지만 다른 문제를 푸는 기술, 같은 문제를 다르게 푸는 기술과의 경계를 쓴다. |
| 깊이 있는 활용 | 원리를 이해해야 쓸 수 있는 설계와 실무 기법이다. 흔한 사용법은 쓰지 않는다. |
| 임시방책의 신호 | AI가 이 문제를 땜질할 때 코드에 남는 모양이다. |
| 실패 재현 | 이 기술이 지키겠다고 약속한 성질이 깨지는 상황을 어떻게 만드는가? |
| 측정과 검증 | 무엇을, 어떤 도구와 통계로, 어떤 조건에서 재는가? |
| 재검토 조건 | 어떤 변화가 생기면 이 선택을 다시 따지거나 걷어내는가? |
| 출처 | 1차 자료를 먼저 쓴다. 공식 문서, 설계 문서, 소스 코드, 장애 회고 순이다. |
