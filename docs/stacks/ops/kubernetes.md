# Kubernetes

확인: 2026-09-27, kubernetes/website 저장소(main)의 문서 기준.

## 요약

Kubernetes는 "이 컨테이너를 이만큼, 이런 조건으로 돌려라"라는 원하는 상태를 선언하면, 제어 루프가 실제 상태를 계속 맞춰 가는 컨테이너 오케스트레이터다.
배포, 복구, 확장, 서비스 발견을 선언으로 다룬다.
가치는 여러 인스턴스를 자동으로 다루는 데서 나오고, 비용은 그 자동화가 우리 애플리케이션에 요구하는 규칙(종료 처리, 건강 검사, 자원 선언)과 클러스터 운영에서 나온다.

## 문제 신호

- 서비스가 여러 개이고 각각 여러 인스턴스로 돈다.
- 인스턴스가 죽으면 사람이 다시 띄운다.
- 배포할 때마다 순서대로 한 대씩 내리고 올리는 절차가 수동이다.
- 부하에 따라 인스턴스 수를 바꿔야 한다.

## 기준선의 한계

기준선은 서버(VM) 몇 대에 컨테이너나 프로세스를 직접 띄우고, 로드 밸런서에 수동으로 등록하는 방식이다.

- 장애 복구, 배포 순서, 확장이 모두 사람이나 스크립트의 일이다.
- 서버 수가 적고 서비스가 하나면 이것으로 충분하다. Kubernetes의 운영 비용이 이 수동 작업의 비용보다 크다.
- 관리형 PaaS(서버리스 컨테이너, 앱 플랫폼)도 대부분의 자동화를 클러스터 운영 없이 준다.

## 원리

- **선언과 제어 루프.** Deployment는 원하는 파드 수와 템플릿을 선언하고, 컨트롤러가 차이를 메운다. 롤링 업데이트 기본값은 최대 불가용 25%, 최대 초과 25%다.
- **건강 검사 세 종류.** startup probe는 시작이 끝났는지, liveness probe는 멈췄는지(실패하면 재시작), readiness probe는 요청을 받을 준비가 됐는지(실패하면 서비스에서 뺌)를 본다. 문서는 readiness와 liveness가 서로에게 의존하지 않는다고 주의를 준다.
- **자원 요청과 제한.** 요청(request)은 스케줄링과 자동 확장의 기준이고, 제한(limit)은 상한이다. 문서는 CPU 제한은 스로틀링으로, 메모리 제한은 커널의 OOM 종료로 강제된다고 설명한다.
- **종료 절차.** 파드를 지우면 기본 30초의 유예 시간이 주어진다. preStop 훅이 있으면 먼저 실행하고, 그 뒤 각 컨테이너의 PID 1에 SIGTERM을 보낸다. 동시에 제어 평면은 파드를 서비스의 EndpointSlice에서 뺀다. 유예가 끝나면 강제로 죽인다.
- **HPA.** 수평 자동 확장은 주기적으로 지표를 읽어, CPU·메모리 사용률은 요청 대비 비율로 계산해 복제본 수를 정한다.
- **CronJob.** 문서는 CronJob이 실행 시각마다 "대략 한 번" Job을 만들며, 두 번 만들거나 만들지 않는 경우가 있으므로 Job은 멱등해야 한다고 적는다. 동시 실행 정책 기본값은 `Allow`다. 시간대를 지정하지 않으면 컨트롤러 매니저의 시간대를 따른다.

## 가치

Kubernetes의 가치는 **여러 서비스·여러 인스턴스의 운영 규칙을 한 선언 모델로 통일하는 것**이다.

- 파드가 죽으면 다시 만들고, 노드가 죽으면 다른 노드로 옮긴다.
- 롤링 업데이트와 되돌리기가 선언의 변경이다.
- HPA로 부하에 맞춰 확장한다.
- 서비스 발견, 설정, 비밀, 네트워크 정책이 같은 API로 다뤄진다.

그래서 Kubernetes가 맞는 상황은 서비스와 인스턴스가 여럿이고, 그 운영 자동화를 팀이 감당할 수 있는 경우다.

## 트레이드오프와 리스크

- **운영 복잡도.** 클러스터 버전 업그레이드, 네트워크(CNI), 인그레스, 인증서, 저장소, 권한(RBAC), 관측이 모두 새 일이다. 관리형 클러스터도 워크로드 설정은 우리 몫이다.
- **잘못된 probe가 장애를 키운다.** liveness probe가 DB 같은 의존 시스템을 검사하면, DB가 잠깐 느려질 때 모든 파드가 동시에 재시작해 장애가 커진다. 시작이 느린 애플리케이션에 startup probe 없이 liveness만 두면 시작 도중에 계속 죽는다.
- **종료 경쟁.** SIGTERM과 EndpointSlice 제거가 동시에 일어나므로, 애플리케이션이 SIGTERM을 받자마자 멈추면 아직 라우팅되던 요청이 실패한다.
- **CPU 제한의 스로틀링.** CPU 제한이 낮으면 평균 사용률이 낮아도 순간 스로틀링으로 지연 꼬리가 길어진다. JVM처럼 시작할 때 CPU를 많이 쓰는 런타임은 시작이 느려진다.
- **요청값이 HPA와 스케줄링을 좌우한다.** 요청을 실제보다 높게 잡으면 자원이 낭비되고, 낮게 잡으면 노드가 과밀해지고 HPA가 늦게 반응한다.
- **CronJob은 정확히 한 번이 아니다.** 기본 `Allow`에서는 이전 실행이 끝나지 않아도 다음 실행이 시작된다.

## 대안과 경계

| 대안 | 고를 때 |
|---|---|
| VM + 컨테이너 직접 실행 | 서비스가 하나이고 인스턴스가 몇 개다. |
| 관리형 컨테이너 플랫폼(서버리스 컨테이너, 앱 플랫폼) | 확장과 복구는 원하지만 클러스터는 운영하고 싶지 않다. |
| Docker Compose | 단일 호스트에서 여러 컨테이너를 묶는다. 개발·시험 환경. |
| Nomad 등 | 컨테이너 외 작업(바이너리, VM)도 함께 스케줄한다. |

## 깊이 있는 활용

- **probe의 역할을 나눈다.** liveness는 "프로세스가 자기 힘으로 회복 못 하는 상태"(교착)만 본다. 의존 시스템은 절대 검사하지 않는다. readiness는 의존 시스템과 워밍업을 포함해 "지금 요청을 받아도 되는가"를 본다. 시작이 느리면 startup probe로 liveness를 늦춘다.
- **종료를 두 단계로.** preStop에서 몇 초 기다려(sleep) EndpointSlice 제거가 퍼질 시간을 주고, SIGTERM을 받으면 새 요청 수신을 멈추고 처리 중인 요청을 끝낸 뒤 종료한다. `terminationGracePeriodSeconds`는 preStop 대기 + 최장 요청 처리 시간보다 길게 둔다. 컨테이너 진입점은 PID 1이 신호를 받게 만든다([Docker](docker.md)).
- **메모리는 요청 = 제한으로.** 메모리는 압축할 수 없는 자원이라, 요청과 제한을 같게 두면 스케줄링과 OOM 동작이 예측 가능해진다. JVM은 제한에 맞춰 힙 비율을 정한다.
- **CPU 제한은 신중히.** 지연에 민감한 서비스는 CPU 요청만 두고 제한을 두지 않거나 넉넉히 두는 방식을 검토한다. 스로틀링 지표(`container_cpu_cfs_throttled_periods_total` 등)를 보고 정한다. (미검증: 조직 정책과 노드 공유 정도에 따라 권장이 갈린다.)
- **중단 예산을 둔다.** PodDisruptionBudget으로 노드 유지보수 중에도 최소 가용 파드 수를 지킨다.
- **CronJob은 `Forbid`와 시작 기한을 둔다.** 겹치면 안 되는 작업은 `concurrencyPolicy: Forbid`, 너무 늦으면 의미 없는 작업은 `startingDeadlineSeconds`를 둔다. `timeZone`을 명시한다. 작업은 멱등하게 만든다([Spring 스케줄러와 ShedLock](../batch/spring-scheduler-shedlock.md)의 "처리 구간 상태" 기법이 그대로 쓰인다).
- **HPA는 요청값 정확도가 전제다.** 실제 사용량을 관찰해 요청값을 맞춘 뒤 HPA 목표 사용률을 정한다. 급증 대응이 필요하면 최소 복제본을 여유 있게 둔다.

## 임시방책의 신호

- liveness probe가 `/health`를 호출하고, 그 엔드포인트가 DB 연결을 검사한다.
- 배포 때마다 5xx가 잠깐 튀는 것을 "원래 그렇다"고 둔다.
- 파드가 OOMKilled로 재시작하자 메모리 제한만 올린다.
- CronJob이 두 번 실행되자 작업 안에 "이미 돌았으면 끝" 로직을 급하게 넣는다.
- 모든 설정을 기본값으로 두고 문제가 생기면 복제본 수를 늘린다.

## 실패 재현

- **probe 연쇄 재시작.** liveness가 DB를 검사하게 두고 DB에 지연을 넣어([Toxiproxy](../verify/toxiproxy.md)) 모든 파드가 재시작되는 것을 본다.
- **종료 중 요청 실패.** [k6](../verify/k6.md)로 일정 부하를 거는 중에 롤링 배포를 하고 5xx 수를 센다. preStop 대기와 우아한 종료를 넣고 반복한다.
- **스로틀링.** CPU 제한을 낮게 두고 부하를 걸어 p99 지연과 스로틀링 지표의 관계를 본다.
- **OOM.** 메모리 제한을 넘게 할당하는 부하로 OOMKilled를 만들고, 힙 설정을 바꿔 반복한다.
- **CronJob 중첩.** 실행 간격보다 오래 걸리는 Job을 `Allow`와 `Forbid`에서 각각 돌려 동시 실행 수를 본다.
- 로컬 재현은 kind나 k3d 같은 가벼운 클러스터로 한다.

## 측정과 검증

- **배포 품질.** 배포 구간의 오류율, p99 지연, 롤아웃 소요 시간을 배포마다 기록한다.
- **재시작.** 파드 재시작 수와 원인(OOMKilled, liveness 실패)을 추세로 본다.
- **자원 적정성.** 요청 대비 실제 사용량 분포, CPU 스로틀링 비율, 노드 사용률을 본다.
- **확장 반응.** 부하 급증에서 HPA가 복제본을 늘리기까지의 시간과 그동안의 지연을 잰다.
- **복구 시간.** 노드나 파드를 강제로 죽였을 때 서비스 지표가 회복되기까지의 시간을 잰다.

## 재검토 조건

- 서비스와 인스턴스 수가 줄어 클러스터 운영 비용이 더 크다. 관리형 플랫폼으로 옮긴다.
- 대부분의 장애가 클러스터 자체(업그레이드, 네트워크)에서 난다. 관리형 서비스나 운영 역량을 다시 본다.

## 출처

- Kubernetes 문서, [Pod Lifecycle](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/workloads/pods/pod-lifecycle.md): 기본 유예 30초, preStop, SIGTERM, EndpointSlice 제거의 동시 진행.
- Kubernetes 문서, [Configure Liveness, Readiness and Startup Probes](https://github.com/kubernetes/website/blob/main/content/en/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes.md): 세 probe, 느린 시작 보호, readiness와 liveness의 독립.
- Kubernetes 문서, [Resource Management for Pods and Containers](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/configuration/manage-resources-containers.md): CPU 제한의 스로틀링, 메모리 제한의 OOM 종료.
- Kubernetes 문서, [Deployments](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/workloads/controllers/deployment.md): 롤링 업데이트 기본 25%·25%.
- Kubernetes 문서, [Horizontal Pod Autoscaling](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale.md): 요청 대비 사용률 계산.
- Kubernetes 문서, [CronJob](https://github.com/kubernetes/website/blob/main/content/en/docs/concepts/workloads/controllers/cron-jobs.md): 대략 한 번 생성과 멱등성 요구, `Allow` 기본값, `startingDeadlineSeconds`, 시간대.
