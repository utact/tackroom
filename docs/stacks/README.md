# 기술 스택 조사

기술 판단 스킬의 재료다.
주니어 개발자가 기능을 만들며 여러 기술의 원리와 적용 조건을 실제로 경험하게 하는 것이 목적이다.
AI는 현재 기능과 연결되는 학습 기회를 적극적으로 제안하고, 선택한 기술을 구현과 실험으로 연결한다.
스킬은 필요한 카드를 참조하며 적용 조건, 예외, 근거 수준을 보존한다.
조사가 틀리면 스킬도 틀리므로, 중요한 주장마다 출처와 확인 범위를 남긴다.

일반 개발에서 어떻게 활용되는지는 [플러그인 안내](../../README.md#plugins)에 있다.
이 목록은 AI가 프로젝트 맥락에 맞는 참조를 찾는 색인이다.
사용자가 카드를 먼저 골라야 Skill이 동작하는 구조를 전제로 하지 않는다.

## 목록을 고른 기준

- 선택하려는 문제와 배울 원리를 먼저 정한다. 정합성, 전달과 복구, 재실행, 검색 품질, 운영 가능성을 구분한다.
- 기준선은 비교의 출발점이다. 현재 규모에서 충분해도 학습 목표와 실험이 있으면 새 기술을 적용할 수 있다.
- 대체 기술, 함께 쓰는 구성요소, 먼저 할 진단을 구분한다. 같은 표에 있다는 이유로 경쟁 기술로 취급하지 않는다.
- 기술이 아닌 패턴(멱등 키, outbox)도 여러 기술에 걸쳐 쓰이면 따로 조사한다.
- 검증 도구와 통계도 한 영역으로 둔다. 선택의 근거는 측정으로 끝나기 때문이다.
- 현재 조사에는 Java·Spring 백엔드와 Python AI 작업의 예가 많다. 이는 자료의 범위이며 Skill을 쓸 프로젝트의 제한이 아니다. 다른 스택에서는 원리와 적용 조건을 연결하고, 카드에 없는 도구는 조사 범위를 밝혀 추가 확인한다.

## 목록

| 선택하려는 문제 | 비교의 출발점 | 조사 대상 |
|---|---|---|
| 업무 상태와 동시 갱신 | 기존 DB의 제약 조건과 트랜잭션 | [PostgreSQL](state/postgresql.md), [MySQL InnoDB](state/mysql-innodb.md), [DynamoDB](state/dynamodb.md) |
| 스키마 변경과 호환성 | 기존 스키마와 배포 순서 | [Flyway와 무중단 스키마 변경](state/schema-migration.md) |
| API와 동시성 | 타임아웃이 있는 단일 요청 | [타임아웃·재시도·멱등 키](api/timeout-retry-idempotency.md), [잠금 전략](api/locking.md), [Resilience4j](api/resilience4j.md), [속도 제한](api/rate-limiting.md) |
| 작업 분배와 사건 로그 | 동기 처리, 기존 DB 작업 큐 | [DB 작업 큐](async/db-job-queue.md), [RabbitMQ](async/rabbitmq.md), [Kafka](async/kafka.md), [Redis Streams](async/redis-streams.md) |
| 저장과 사건 발행의 연결 | 업무 DB의 로컬 트랜잭션 | [Outbox와 CDC](async/outbox-cdc.md) |
| 서비스 간 업무와 보상 | 한 DB의 트랜잭션 | [사가 패턴](async/saga.md) |
| 실행 시점과 중복 실행 | OS cron | [Spring 스케줄러와 ShedLock](batch/spring-scheduler-shedlock.md), [Quartz](batch/quartz.md) |
| 항목 처리와 재개 | 반복문과 진행 상태 | [Spring Batch](batch/spring-batch.md) |
| 작업 간 의존성과 재실행 | 명시적인 순서가 있는 스크립트 | [Airflow](batch/airflow.md) |
| 조회 가속과 신선도 | 실행 계획을 확인한 쿼리와 HTTP 응답 | [Redis 캐시](search/redis-cache.md), [Caffeine](search/caffeine.md), [HTTP 캐시와 CDN](search/http-cache.md) |
| 검색과 관련도 | SQL·키워드 검색, 정확 벡터 검색 | [Elasticsearch](search/elasticsearch.md), [pgvector](search/pgvector.md), [하이브리드 검색과 리랭킹](search/hybrid-rerank.md), [Qdrant](search/qdrant.md) |
| RAG와 문서 처리 | 키워드 검색과 원문 제시 | [RAG 파이프라인](rag/rag-pipeline.md), [문서 파싱](rag/document-parsing.md), [청킹](rag/chunking.md), [임베딩 모델 선택](rag/embeddings.md) |
| LLM 추론 서빙 | 외부 API 또는 단일 요청 추론 | [vLLM](rag/vllm.md) |
| LLM 품질 평가 | 정답·근거가 있는 사례의 수동 판정 | [LLM 평가](rag/llm-evaluation.md) |
| LLM 통합 | HTTP로 LLM API 직접 호출과 애플리케이션 안의 도구 정의 | [LLM API와 SDK](llm/llm-api.md), [MCP](llm/mcp.md), [A2A](llm/a2a.md) |
| 실행 환경과 배포 자동화 | 단일 서버의 재현 가능한 실행 절차 | [Docker](ops/docker.md), [GitHub Actions](ops/github-actions.md), [Kubernetes](ops/kubernetes.md) |
| 관측과 사용자 영향 | 구조화 로그와 요청 식별자 | [OpenTelemetry](ops/opentelemetry.md), [Prometheus와 Grafana](ops/prometheus-grafana.md), [Loki와 로그 수집](ops/loki.md), [SLO와 알림](ops/slo-alerting.md) |
| 요청 경로와 TLS | 애플리케이션의 직접 HTTPS 제공 | [Nginx와 TLS](ops/nginx-tls.md) |
| 신원·접근 제어와 비밀 | 서버 세션과 환경에 맞는 자격 증명 관리 | [OAuth 2.0과 JWT](ops/oauth-jwt.md), [비밀 관리](ops/secrets.md) |
| 검증 | 수동 확인 | [k6](verify/k6.md), [Toxiproxy](verify/toxiproxy.md), [Testcontainers](verify/testcontainers.md), [측정 통계](verify/statistics.md) |
| 대규모 데이터 처리 | 애플리케이션 반복문과 운영 DB 집계 | [DuckDB와 단일 노드 분석](data/duckdb.md), [Spark](data/spark.md), [BigQuery](data/bigquery.md), [Flink](data/flink.md) |
| 배포와 공개 | 멈추고 교체하는 배포 | [배포 전략](deploy/deployment-strategies.md), [기능 플래그](deploy/feature-flags.md) |
| 클라이언트 갱신과 양방향 통신 | 폴링 | [폴링과 롱 폴링](comm/polling.md), [SSE](comm/sse.md), [WebSocket](comm/websocket.md) |
| 서비스 간 호출과 외부 알림 | HTTP API와 주기적 조회 | [gRPC](comm/grpc.md), [웹훅](comm/webhook.md) |
| 파일과 객체 저장 | DB BLOB 또는 서버 로컬 디스크 | [객체 저장소](storage/object-storage.md), [파일 업로드](storage/file-upload.md) |

디렉터리는 기존 링크를 유지하는 보관 위치이며, 위 표가 선택 문제별 진입점이다.
vLLM은 RAG 밖에서도 쓰는 서빙 도구이고, LLM 평가의 공통 방법은 RAG 이외의 생성·도구 호출 평가에도 적용한다.
Spring Batch를 Quartz나 Airflow로 실행하거나 Saga의 사건 발행에 Outbox를 쓰는 것처럼 여러 카드를 함께 읽을 수 있다.

## 비교와 학습 실험

- 대안 표의 각 항목은 대체 관계, 보완 관계, 선행 진단 중 무엇인지 문맥으로 구분한다. 함께 써야 하는 도구 사이에 승자를 고르지 않는다.
- 문제 신호와 재검토 조건은 판단 자료다. 작은 규모, 단일 소비자, 사용 빈도 하나로 도입이나 제거를 자동 결정하지 않는다. 기능 적합성, 학습할 원리, 실행 제약과 전환 비용을 함께 검토한다.
- 각 카드의 가치 절에 학습 실험을 둔다. AI가 실패 재현·측정 절과 함께 읽고 현재 프로젝트의 구현 검증으로 바꿔 적용하는 재료다. 사용자에게 별도 실습이나 카드 순회 과정을 요구하지 않는다.
- 재검토 조건에는 한계가 드러나는 동작·부하·운영 변화와 검증할 대안을 쓴다. 프로젝트 목적에 맞춰 판단하며 학습 완료를 제거 조건으로 삼지 않는다.
- 학습·포트폴리오에서는 기존 구현, 재현 방법과 비교 결과를 보존한다. 카드의 운영상 전환 권고를 포트폴리오의 자동 삭제·교체 지침으로 적용하지 않는다.
- 카드에 적힌 실험은 실행 지침이다. 실행 로그와 결과가 없으면 검증을 마쳤다고 쓰지 않는다.
- 모든 작업에 카드의 실험을 전부 수행하도록 강제하지 않는다. 현재 적용한 성질을 확인하는 검증을 고르고, 필요하면 더 깊게 확장한다.
- 작은 실험에서도 핵심 원리를 관찰할 수 있다. 운영 규모의 성능·가용성을 주장하려면 해당 환경에서 별도로 검증한다.
- 기술 간 연결도 시험한다. DB 저장 후 발행 중단, 캐시 무효화 유실, 검색 색인의 삭제·권한 변경 반영, 배포 중 버전 공존이 예다.
- 상태를 보관하는 설계에는 복구 원천, 허용 데이터 손실(RPO), 허용 복구 시간(RTO), 복원 후 검증을 함께 적는다.

## 확인 수준

최초 조사 환경에서는 대부분의 공식 문서 사이트가 네트워크 정책으로 막혀 있었다.
그래서 각 프로젝트가 GitHub에 두는 문서 원본과 소스 코드를 사용했다.
릴리스 태그를 고정한 자료와 변경 가능한 main·master 자료가 섞여 있다.
기본값은 가능하면 설정 클래스의 소스에서 확인했다.
최초 조사에서 검색 요약으로 확인한 자료는 각 출처에 표시했다. 이후 원문을 읽은 항목은 확인 날짜와 해당 절·주장을 따로 적고, 같은 문서의 다른 주장까지 확인된 것으로 바꾸지 않는다.
출처 없이 적은 경험칙은 본문에 `(미검증)`을 붙였다.
카드의 확인 날짜는 기록한 자료를 확인한 날짜이며, 모든 주장이나 실험의 검증 완료를 뜻하지 않는다.
2026-09-29 개정에서는 학습 목적, 분류, 비교의 조건을 보완하고, 재확인한 기술 주장의 출처에는 해당 범위를 적었다.
2026-10-01에는 카드의 재검토 조건을 구체화하고, LLM 캐시 수치를 모델·API와 확인 날짜별로 보완했다.
공식 원문, 검색 요약, 경험칙 모두 주장별로 반례와 적용 조건을 검토한다.
중요한 버전별 기본값은 태그나 커밋을 고정하고, 고정하지 못하면 이동 가능한 출처임을 남긴다.

`tests/test_stacks.py`가 이 목록과 파일이 일치하는지, 모든 문서가 아래 양식의 항목을 순서대로 갖췄는지 검사한다.
이 테스트는 사실의 정확성, 출처의 뒷받침, 실험의 성공을 판정하지 않는다.

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
| 가치 | 어떤 요구에 유리하고, 현재 기능에서 어떤 원리를 실험하며 배울 수 있는가? |
| 트레이드오프와 리스크 | 도입하면 무엇을 잃는가? 새로 생기는 실패 방식, 운영 부담, 학습 비용, 되돌리기 어려움을 쓴다. |
| 대안과 경계 | 대체 기술, 함께 쓸 구성요소, 선행 진단의 관계와 적용 조건을 쓴다. |
| 깊이 있는 활용 | 원리를 이해해야 쓸 수 있는 설계와 실무 기법이다. 흔한 사용법은 쓰지 않는다. |
| 임시방책의 신호 | 추가 확인이 필요한 모양과 문맥이다. 구문이나 기술 이름만으로 잘못된 구현이라고 단정하지 않는다. |
| 실패 재현 | 이 기술이 지키겠다고 약속한 성질이 깨지는 상황을 어떻게 만드는가? |
| 측정과 검증 | 무엇을, 어떤 도구와 통계로, 어떤 조건에서 재는가? |
| 재검토 조건 | 어떤 변화가 한계를 드러내며, 어떤 구현 개선이나 대안을 검증할 것인가? |
| 출처 | 1차 자료를 먼저 쓴다. 공식 문서, 설계 문서, 소스 코드, 장애 회고 순이다. |
