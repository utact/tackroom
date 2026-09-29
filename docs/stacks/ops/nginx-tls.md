# Nginx와 TLS

확인: 2026-09-29 재검토. 최초 조사는 2026-09-27, nginx/nginx.org 저장소(main)의 모듈 문서, nginx 최신 태그 1.31.6 기준.

## 요약

Nginx는 클라이언트와 애플리케이션 사이에서 TLS를 끝내고(종단), 요청을 여러 애플리케이션 인스턴스로 나누고, 느린 클라이언트와 요청 폭주에서 애플리케이션을 보호하는 리버스 프록시다.
요청 경로의 첫 관문이라, 여기의 타임아웃·재시도·버퍼·신뢰 경계 설정이 애플리케이션의 동작을 바꾼다.
네트워크 문제를 추적할 때 DNS → TLS → 프록시 → 애플리케이션 순서로 요청 경로를 나눠 보는 출발점이기도 하다.

## 문제 신호

- 애플리케이션이 TLS 인증서와 HTTP 연결 관리를 직접 한다.
- 인스턴스 여러 개에 요청을 나눠야 한다.
- 느린 모바일 클라이언트가 애플리케이션 스레드를 오래 잡는다.
- 특정 IP나 경로의 요청 폭주를 막아야 한다.
- 로그의 클라이언트 IP가 모두 로드 밸런서 IP다.

## 기준선의 한계

기준선은 애플리케이션 서버(내장 Tomcat 등)를 직접 인터넷에 노출하는 것이다.

- 인증서 갱신, TLS 설정, HTTP/2 협상, 느린 클라이언트 처리를 애플리케이션마다 해야 한다.
- 인스턴스가 여럿이면 앞단에 분배기가 필요하다.
- 정적 파일, 압축, 요청 크기 제한 같은 공통 기능이 애플리케이션에 섞인다.

## 원리

- **TLS 종단.** Nginx가 인증서를 들고 클라이언트와 TLS를 맺고, 애플리케이션에는 평문(또는 내부 TLS)으로 전달한다. `ssl_protocols` 기본값은 `TLSv1.2 TLSv1.3`이다.
- **버퍼링.** `proxy_buffering` 기본값은 on이다. 상위 응답을 빨리 받아 버퍼(넘치면 임시 파일)에 담으므로, 애플리케이션은 느린 클라이언트를 기다리지 않는다.
- **타임아웃.** `proxy_connect_timeout`과 `proxy_read_timeout` 기본값은 60초다. 읽기 타임아웃은 응답 전체가 아니라 연속된 두 읽기 사이에 적용되어, 조금씩 흘리는 응답은 끝없이 이어질 수 있다.
- **다음 서버로 재시도.** `proxy_next_upstream` 기본값은 `error timeout`이다.
  - 이미 보낸 비멱등 요청(POST, LOCK, PATCH)은 넘기지 않는다. `non_idempotent`로 켤 수 있다.
  - 클라이언트에 응답을 보내기 시작했으면 재시도할 수 없다.
  - `proxy_next_upstream_tries` 기본값 0은 횟수 제한이 없다는 뜻이다.
- **상위 연결 재사용.** 1.29.7부터 상위 서버 keepalive 연결 캐시가 기본으로 켜진다(워커당 유휴 연결 32개).
- **실제 클라이언트 IP.** realip 모듈은 `set_real_ip_from`으로 지정한 신뢰 주소가 보낸 헤더(`X-Forwarded-For` 등)에서만 클라이언트 주소를 바꾼다.
- **요청 속도 제한.** `limit_req`는 키(예: 클라이언트 IP)별로 정한 속도를 넘는 요청을 지연시키고, 버스트 크기를 넘으면 오류로 끊는다. 기본 버스트는 0이다.

## 가치

Nginx의 가치는 **애플리케이션 앞에서 느림과 폭주를 흡수하고, 요청 경로의 공통 정책을 한곳에 두는 것**이다.

- 느린 클라이언트와 TLS 계산을 흡수해 애플리케이션 자원을 요청 처리에만 쓴다.
- 인스턴스 분배, 장애 인스턴스 우회, 무중단 교체의 기반이 된다.
- 속도 제한, 요청 크기 제한, 접근 제어를 애플리케이션 밖에서 건다.

## 트레이드오프와 리스크

- **타임아웃 계층이 하나 더 생긴다.** Nginx 60초, 애플리케이션, 하위 호출의 타임아웃이 서로 맞지 않으면, 애플리케이션은 계속 처리하는데 클라이언트는 504를 받는다([타임아웃·재시도·멱등 키](../api/timeout-retry-idempotency.md)).
- **자동 재시도가 중복을 만든다.** 기본 설정에서 부작용이 있는 GET은 다른 서버에서 두 번 실행된다. `non_idempotent`를 켜면 POST도 중복된다.
- **버퍼링과 스트리밍의 충돌.** 서버 전송 이벤트(SSE), LLM 토큰 스트리밍처럼 조금씩 보내는 응답은 버퍼링 때문에 한꺼번에 도착한다.
- **신뢰 경계 오류.** `set_real_ip_from`을 넓게 잡거나 `X-Forwarded-For`를 그대로 믿으면, 클라이언트가 IP를 위조해 속도 제한과 IP 기반 접근 제어를 우회한다.
- **설정 오류의 영향 범위.** 모든 요청이 지나가므로 설정 실수 하나가 전체 장애가 된다. 인증서 만료도 전체 장애다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| 관리형 로드 밸런서(클라우드 L7) | TLS 종단과 분배를 관리형으로 맡긴다. 세밀한 설정은 제한된다. |
| Envoy, HAProxy | 동적 설정(xDS), 고급 부하 분산, 서비스 메시가 필요하다. |
| Kubernetes Ingress·Gateway | 클러스터 안에서 선언으로 관리한다. 구현체로 Nginx를 쓸 수도 있다. |
| Caddy 등 | 인증서 자동 발급·갱신이 기본인 단순한 구성이 필요하다. |

## 깊이 있는 활용

- **타임아웃을 계층별로 맞춘다.** 바깥에서 안으로 갈수록 짧게: 클라이언트 > Nginx `proxy_read_timeout` > 애플리케이션 요청 기한 > 하위 호출. 긴 작업은 동기 요청으로 두지 말고 비동기로 넘긴다.
- **재시도를 명시적으로 제한한다.** `proxy_next_upstream_tries`를 2 정도로 두고, 재시도 대상 상태 코드를 명시한다. 부작용이 있는 GET은 없앤다.
- **스트리밍 경로만 버퍼링을 끈다.** SSE나 LLM 스트리밍 경로에서만 `proxy_buffering off`(또는 응답 헤더 `X-Accel-Buffering: no`)를 쓰고, 그 경로의 읽기 타임아웃을 스트림 길이에 맞춘다.
- **신뢰하는 프록시만 적는다.** `set_real_ip_from`에는 로드 밸런서의 주소 범위만 넣고, `real_ip_recursive on`으로 헤더에 담긴 주소 중 신뢰하지 않는 마지막 주소를 클라이언트로 쓴다. 클라이언트가 헤더 앞쪽에 넣은 위조 값은 무시된다.
- **속도 제한은 버스트와 함께.** `limit_req`에 `burst`와 `nodelay`를 두면 짧은 급증은 통과시키고 지속적 초과만 끊는다. 키는 IP만이 아니라 API 키나 사용자 단위도 검토한다.
- **TLS는 현대 프로토콜만.** 기본값(TLS 1.2, 1.3)을 유지하고, 세션 재개로 핸드셰이크 비용을 줄인다.
- **OCSP stapling은 CA를 확인하고 켠다.** Let's Encrypt는 2025년 5월 인증서에서 OCSP 주소를 빼고 8월에 OCSP 응답기를 껐다. 폐기 정보는 CRL로만 낸다. OCSP 주소가 없는 인증서에 stapling을 켜면 얻는 것 없이 경고만 남는다.
- **인증서 갱신은 자동화가 전제다.** CA/Browser Forum 결의(SC-081v3)로 공개 TLS 인증서의 최대 수명이 2026년 3월 15일부터 200일, 2027년부터 100일, 2029년부터 47일로 준다. ACME 자동 갱신을 두고, 만료까지 남은 일수를 경보로 감시한다.
- **요청 경로를 층별로 진단한다.** 느리거나 실패하면 DNS 조회, TCP 연결, TLS 핸드셰이크, 첫 바이트, 전송 순서로 나눠 잰다(`curl -w`의 `time_namelookup`, `time_connect`, `time_appconnect`, `time_starttransfer`). Nginx 로그에 `$request_time`과 `$upstream_response_time`을 함께 남기면 지연이 프록시와 애플리케이션 중 어디인지 보인다.

## 임시방책의 신호

- 504가 나자 `proxy_read_timeout`을 몇 분으로 늘린다.
- 스트리밍이 한꺼번에 오는 문제를 애플리케이션에서 해결하려 한다.
- 속도 제한을 애플리케이션 코드에서 인스턴스별 메모리 카운터로 한다.
- 로그의 IP가 모두 같아 IP 기반 제한을 포기한다. 또는 `X-Forwarded-For` 첫 값을 그대로 믿는다.
- 인증서 갱신을 달력에 적어 둔다.

## 실패 재현

- **중복 요청.** 상위 서버가 처리 후 응답 전에 연결을 끊게 해([Toxiproxy](../verify/toxiproxy.md)), 멱등 요청이 다른 서버로 재시도돼 두 번 처리되는지 센다.
- **타임아웃 불일치.** 애플리케이션 처리 시간을 Nginx 읽기 타임아웃보다 길게 만들어, 클라이언트는 504를 받고 애플리케이션은 계속 처리하는 것을 본다.
- **느린 데이터 흘림.** 상위 서버가 몇 초마다 한 바이트씩 보내게 해 읽기 타임아웃이 걸리지 않는 것을 확인한다.
- **IP 위조.** 신뢰 범위 밖에서 `X-Forwarded-For`를 넣어 보내 속도 제한 키가 바뀌는지 본다.
- **스트리밍 버퍼링.** 스트리밍 응답을 버퍼링 켬·끔에서 받아 첫 토큰 도착 시간을 비교한다.

## 측정과 검증

- **지연 분해.** `$request_time`(클라이언트 기준 전체)과 `$upstream_response_time`(상위 서버)의 차이로 프록시·네트워크 구간을 본다.
- **상위 서버 오류와 재시도.** 상위 상태 코드별 수, 재시도 발생 수, 504 수를 본다.
- **TLS.** 핸드셰이크 시간, 세션 재개 비율, 인증서 만료까지 남은 일수를 본다.
- **속도 제한 효과.** 거부된 요청 수와 정상 사용자의 거부 비율(오탐)을 본다.

## 재검토 조건

- 서비스 메시나 동적 라우팅 요구가 커졌다. Envoy 계열을 검토한다.
- 클러스터 안의 선언적 관리가 필요하다. Gateway API로 옮긴다.

## 출처

- nginx 문서, [ngx_http_proxy_module](https://github.com/nginx/nginx.org/blob/main/xml/en/docs/http/ngx_http_proxy_module.xml): `proxy_read_timeout`·`proxy_connect_timeout` 기본 60초와 읽기 사이 적용, `proxy_next_upstream` 기본값과 비멱등 요청, 응답 시작 후 재시도 불가, `proxy_next_upstream_tries`, `proxy_buffering`.
- nginx 문서, [ngx_http_upstream_module](https://github.com/nginx/nginx.org/blob/main/xml/en/docs/http/ngx_http_upstream_module.xml): 1.29.7부터 keepalive 캐시 기본 활성.
- nginx 문서, [ngx_http_ssl_module](https://github.com/nginx/nginx.org/blob/main/xml/en/docs/http/ngx_http_ssl_module.xml): `ssl_protocols` 기본 TLSv1.2 TLSv1.3.
- Let's Encrypt, [Ending OCSP Support in 2025](https://letsencrypt.org/2024/12/05/ending-ocsp)와 [OCSP Service Has Reached End of Life](https://letsencrypt.org/2025/08/06/ocsp-service-has-reached-end-of-life): 2025-05-07 인증서에서 OCSP 주소 제거, 2025-08-06 응답기 종료. 검색 요약으로 확인했다(2026-09-29 재검토).
- CA/Browser Forum, [Ballot SC081v3](https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/): 인증서 최대 수명 단계적 단축. 검색 요약으로 확인했다(2026-09-29 재검토).
- nginx 문서, [ngx_http_realip_module](https://github.com/nginx/nginx.org/blob/main/xml/en/docs/http/ngx_http_realip_module.xml): 신뢰 주소와 재귀 탐색.
- nginx 문서, [ngx_http_limit_req_module](https://github.com/nginx/nginx.org/blob/main/xml/en/docs/http/ngx_http_limit_req_module.xml): 지연과 버스트, 기본 버스트 0.
