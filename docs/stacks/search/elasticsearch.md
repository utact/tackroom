# Elasticsearch

확인: 2026-09-27, Elasticsearch v9.5.4 레퍼런스 문서(elastic/elasticsearch 저장소 docs/reference) 기준.

## 요약

Elasticsearch는 문서를 분석기로 토큰으로 쪼개 역색인에 넣고, 관련도 점수로 정렬해 찾는 분산 검색 엔진이다.
샤드로 나눠 여러 노드에 두고, 쓰기는 주기적인 refresh 뒤에 검색에 보인다(near-real-time).
원본을 두는 곳이 아니라, 원본에서 만들어 계속 따라가게 하는 **파생 색인**이다. 그 따라가는 경로를 설계하는 것이 도입의 절반이다.

## 문제 신호

- 사용자가 자유 문장으로 찾고, 형태소 분석(한국어 조사·어미 처리), 동의어, 오타 교정, 관련도 순위가 필요하다.
- 여러 조건의 필터와 패싯(카테고리별 개수)을 함께 보여줘야 한다.
- 로그나 이벤트처럼 대량 데이터를 시간 범위로 집계하고 검색한다.
- RDB의 `LIKE '%단어%'`나 전문 검색으로는 품질이나 속도가 모자란 것이 측정됐다.

## 기준선의 한계

기준선은 RDB의 인덱스와 전문 검색이다.

- `LIKE '%단어%'`는 B-tree 인덱스를 쓰지 못한다. PostgreSQL의 `pg_trgm`이나 전문 검색(`tsvector`)으로 상당 부분 해결되지만, 한국어 형태소 분석과 관련도 튜닝은 제한적이다.
- RDB는 검색 결과의 관련도 순위, 패싯 집계, 하이라이트를 대량 데이터에서 빠르게 하도록 설계되지 않았다.
- 검색 부하가 업무 쿼리와 같은 DB 자원을 쓴다.

## 원리

- **역색인과 분석기.** 텍스트 필드는 분석기(문자 필터 → 토크나이저 → 토큰 필터)를 거쳐 토큰이 되고, 토큰 → 문서 목록의 역색인에 들어간다. 질의도 같은 분석을 거친다. 한국어는 nori 형태소 분석 플러그인을 쓴다.
- **매핑.** 필드마다 타입과 분석기를 정한다. `text`는 분석되어 검색용, `keyword`는 그대로 저장되어 정확 일치·정렬·집계용이다. 매핑된 필드는 나중에 타입을 바꿀 수 없어, 바꾸려면 새 색인으로 다시 넣어야 한다.
- **샤드.** 색인은 주 샤드로 나뉜다. 주 샤드 수(`index.number_of_shards`, 기본 1)는 색인을 만들 때만 정할 수 있다. 문서는 라우팅 값으로 샤드가 정해진다.
- **near-real-time.** 쓴 문서는 refresh 뒤에 검색에 보인다. `index.refresh_interval` 기본값은 1초이고, 설정하지 않으면 한동안 검색이 없던 샤드는 검색 요청이 올 때까지 배경 refresh를 하지 않는다.
- **내구성.** translog 기본값(`index.translog.durability=request`)은 요청마다 주 샤드와 모든 복제본에서 fsync 후 성공을 돌려준다.
- **동시성.** 문서마다 순번(`_seq_no`)과 주 샤드 임기(`_primary_term`)가 있고, `if_seq_no`와 `if_primary_term`으로 낙관적 동시성 제어를 한다. 외부 버전(`version_type=external`)으로 원본 쪽 버전을 문서 버전으로 쓸 수도 있다.
- **깊은 페이지 제한.** `from + size`는 기본 10,000(`index.max_result_window`)까지다. 그 너머는 `search_after`로 넘긴다.

## 가치

Elasticsearch의 가치는 **"무엇이 가장 맞는가"를 대량 데이터에서 빠르게 답하는 것**이다.

- 분석기로 언어를 이해한 검색(형태소, 동의어, 오타 허용)을 하고, BM25 같은 점수로 순위를 매긴다.
- 필터, 패싯 집계, 하이라이트, 자동완성을 한 질의로 한다.
- 샤드와 복제본으로 검색 처리량과 데이터 양을 수평으로 늘린다.

그래서 Elasticsearch가 맞는 상황은 검색 품질 자체가 제품의 기능인 경우, 또는 대량 로그를 탐색하는 경우다.
단순한 정확 일치 조회나 목록 필터링에는 과하다.

## 트레이드오프와 리스크

- **원본과 어긋난다.** 색인은 원본의 사본이다. 동기화 경로가 실패하거나 순서가 바뀌면 삭제된 문서가 검색되거나 최신 가격이 안 보인다. 권한이 바뀐 문서가 검색되면 보안 사고다.
- **쓴 직후에는 안 보인다.** refresh 전까지 검색에 없다. "저장 후 목록으로 이동"하는 화면에서 방금 쓴 글이 없다.
- **스키마 변경은 재색인이다.** 필드 타입이나 분석기를 바꾸려면 새 색인을 만들고 전부 다시 넣어야 한다. 주 샤드 수도 마찬가지다(split·shrink는 제한적).
- **매핑 폭발.** 동적 매핑이 켜진 상태로 임의 키가 있는 JSON을 넣으면 필드가 끝없이 늘어난다. 필드 수 상한 기본값은 1,000이다.
- **깊은 페이지가 비싸다.** `from + size`에 비례해 힙과 시간을 쓴다. 문서는 이 이유로 10,000 상한을 둔다.
- **운영 부담.** JVM 힙, 샤드 수와 크기, 노드 역할, 스냅샷, 버전 업그레이드를 관리해야 한다. 샤드가 너무 많으면 클러스터 상태가 무거워진다.
- **라이선스와 포크.** Elastic의 라이선스 변경 뒤 AWS 주도의 OpenSearch 포크가 있다. 관리형 서비스와 플러그인 선택이 달라진다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| PostgreSQL 전문 검색, `pg_trgm` | 데이터가 수백만 건 이하이고, 트랜잭션 일관성이 중요하고, 관련도 튜닝 요구가 작다. 새 인프라가 없다. |
| [pgvector](pgvector.md) | 의미 기반 검색(임베딩 유사도)이 주 요구다. Elasticsearch도 벡터 검색을 지원하므로 둘 중 하나로 모을 수 있다. |
| [하이브리드 검색과 리랭킹](hybrid-rerank.md) | 키워드와 의미 검색을 합친다. Elasticsearch 안에서 하거나 애플리케이션에서 합친다. |
| OpenSearch | Elasticsearch와 비슷한 기능을 Apache 2.0 라이선스로 원한다. API는 갈라지고 있다. |
| 관리형 검색 서비스 | 운영을 맡기고 기능 범위가 맞는다. |

## 깊이 있는 활용

- **별칭(alias)으로 무중단 재색인을 한다.** 애플리케이션은 항상 별칭(`products`)으로 읽고 쓴다. 매핑을 바꿀 때 새 색인(`products_v2`)을 만들어 전부 넣고, 그 사이 변경분을 따라잡은 뒤 별칭을 원자적으로 새 색인으로 바꾼다.
- **동기화는 [Outbox와 CDC](../async/outbox-cdc.md)로 한다.** 저장 후 애플리케이션이 직접 색인하면 이중 쓰기다. 원본 변경을 사건으로 내보내고 색인기가 소비한다. 색인기는 멱등해야 한다.
- **순서 역전은 외부 버전으로 막는다.** 원본 행의 버전이나 갱신 순번을 `version_type=external`로 넣으면, 늦게 도착한 옛 사건이 새 문서를 덮어쓰지 못한다.
- **삭제와 권한 변경을 1급 사건으로 다룬다.** 삭제는 색인에서도 지우고, 권한은 문서에 접근 가능한 주체 목록을 필드로 넣어 질의에 필터로 건다. 색인과 원본의 권한을 주기적으로 대조한다.
- **"방금 쓴 것"이 보여야 하면 `refresh=wait_for`를 쓴다.** 강제 refresh(`true`)는 문서가 신중히 쓰라고 경고할 만큼 비싸다. `wait_for`는 다음 refresh를 기다렸다가 응답한다. 대량 적재 중에는 `refresh_interval`을 `-1`로 두고 끝나면 되돌린다.
- **텍스트 필드는 두 번 매핑한다.** 같은 필드를 검색용 `text`와 정렬·집계용 `keyword`로 다중 필드 매핑한다.
- **동적 매핑을 제한한다.** 임의 키 JSON은 `dynamic: false`나 `flattened` 타입으로 받아 필드 폭발을 막는다.
- **깊은 페이지는 `search_after`와 point in time으로 한다.** 정렬에 유일한 동률 해소 필드(ID)를 넣는다. 사용자 화면은 "다음 페이지" 방식으로 설계한다.
- **샤드는 크기로 정한다.** 샤드가 너무 작고 많으면 오버헤드가, 너무 크면 복구 시간이 문제다. 데이터 증가를 보고 색인을 시간 단위로 나누거나(롤오버) 처음 샤드 수를 정한다.
- **한국어 분석기를 시험셋으로 고른다.** nori의 분해 모드(`decompound_mode`)와 사용자 사전을 바꿔 가며 실제 질의 집합으로 평가한다.

## 임시방책의 신호

- 저장 API 안에서 DB 저장 후 색인 API를 부르고, 실패하면 로그만 남긴다.
- 색인과 원본이 어긋나자 야간에 전체 재색인을 돌려 덮는다.
- 방금 쓴 글이 안 보이자 모든 쓰기에 `refresh=true`를 붙인다.
- 10,000건 제한에 걸리자 `index.max_result_window`를 크게 늘린다.
- 필드 수 상한 오류가 나자 `total_fields.limit`을 올린다.
- 한국어 검색 품질 문제를 `wildcard`나 `ngram`만으로 덮는다.
- 권한 필터를 검색 결과를 받은 뒤 애플리케이션에서 건다. 페이지 크기와 총 건수가 틀어진다.

## 실패 재현

- **이중 쓰기 불일치.** DB 저장 후 색인 전에 프로세스를 죽여, 원본에는 있고 색인에는 없는 문서를 만든다. outbox 방식으로 바꿔 반복한다.
- **순서 역전.** 같은 문서의 갱신 사건 두 개를 역순으로 색인해 옛 값이 남는지 본다. 외부 버전으로 반복한다.
- **삭제 누락.** 원본에서 삭제하고 삭제 사건을 유실시켜 검색에 계속 나오는지 본다. 대조 작업이 잡아내는지 확인한다.
- **refresh 지연.** 쓰기 직후 검색해 안 보이는 것을 테스트로 고정하고, `wait_for`로 해결되는지 본다.
- **매핑 폭발.** 임의 키 JSON 수천 종을 동적 매핑으로 넣어 필드 수 상한 오류를 만든다.
- 재현은 [Testcontainers](../verify/testcontainers.md)의 Elasticsearch 모듈로 한다.

## 측정과 검증

- **검색 품질은 평가셋으로 잰다.** 실제 질의와 정답 문서(관련도 판정)를 모아, 변경 전후의 nDCG@10, Recall@k, MRR을 비교한다. Elasticsearch의 순위 평가 API(`_rank_eval`)를 쓸 수 있다. 판정은 사람이 하거나, 모델 판정을 사람 판정과 맞춰 보정한다.
- **색인 신선도.** 원본 변경 시각과 검색에 보이기 시작한 시각의 차이를 p50, p99로 잰다.
- **정합성 대조.** 주기적으로 원본과 색인의 문서 수, 표본 문서의 필드 값, 삭제 여부를 대조해 불일치율을 기록한다.
- **성능.** 실제 질의 분포로 [k6](../verify/k6.md) 부하를 걸어 검색 p99와 처리량을 본다. 색인 부하를 함께 걸어 쓰기가 검색을 해치는지 본다. 느린 질의는 `profile` API로 본다.
- **클러스터 상태.** 힙 사용률, GC, 샤드 수와 크기, 거부된 요청(thread pool rejections)을 추세로 본다.

## 재검토 조건

- 데이터가 작고 검색 품질 요구가 단순해 PostgreSQL 전문 검색으로 충분하다.
- 의미 검색이 주가 됐다. 벡터 저장소와 하나로 모을지 다시 본다.
- 색인 동기화 불일치가 반복된다. 동기화 경로를 CDC로 바꾼다.

## 출처

- Elasticsearch v9.5.4, [Index modules](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/index-settings/index-modules.md): 주 샤드 수 기본 1과 생성 시에만 설정, `refresh_interval` 기본 1초와 검색 유휴 샤드, `max_result_window` 기본 10,000.
- Elasticsearch v9.5.4, [Mapping limit settings](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/index-settings/mapping-limit.md): 필드 수 기본 상한 1,000.
- Elasticsearch v9.5.4, [Translog](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/index-settings/translog.md): `durability=request` 기본값과 `async`의 유실 범위.
- Elasticsearch v9.5.4, [The refresh parameter](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/rest-apis/refresh-parameter.md): `true`의 비용 경고, `wait_for`.
- Elasticsearch v9.5.4, [Optimistic concurrency control](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/rest-apis/optimistic-concurrency-control.md), [Reindex](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/rest-apis/reindex-indices.md): 순번과 임기, `version_type: external`.
- Elasticsearch v9.5.4, [Paginate search results](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch/rest-apis/paginate-search-results.md): 10,000건 한도와 `search_after`.
- Elasticsearch v9.5.4, [Nori analysis plugin](https://github.com/elastic/elasticsearch/blob/v9.5.4/docs/reference/elasticsearch-plugins/analysis-nori-analyzer.md): 한국어 형태소 분석.
