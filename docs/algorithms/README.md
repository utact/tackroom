# 수학·알고리즘·표현 기법

규칙의 성질, 데이터 표현, 계산 위치를 바꾸는 방법을 조사한다. 특정 프로젝트나 기술 제품에 한정하지 않으며, 흥미로운 원리를 먼저 이해하고 활용처를 찾는 학습에도 사용한다. 구현 사례는 원리의 근거와 적용 후보로 연결한다.

카드는 기존 기술 카드와 같은 절을 사용한다. 요약에서 출처까지 원리·성립 조건·비용·대안·반례·검증 방법을 함께 읽는다. 현재 적용할 문제가 없어도 원리는 조사할 수 있으며, 활용 예시는 채택을 요구하는 지침이 아니다.

## 목록

수열의 규칙, 공간 배치, 형태 생성, 구조 제약, 화면 표현, 저장 표현, 데이터 처리 순으로 배치했다. 원리에서 구현으로 읽는 순서이며 도입 우선순위는 아니다. 각 범주에서는 기본 연산과 성질을 먼저, 합성과 복합 구현을 뒤에 둔다.

### 수열과 반복

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| 중국인의 나머지 정리 | 나머지 조건의 결합·복원 | [나머지 정리](sequences/chinese-remainder.md) |
| 이진 반사 Gray code | 인접 항목의 한 비트 차이 | [Gray code](sequences/gray-code.md) |
| De Bruijn 수열 | 순환 창의 전체 조합 순회 | [De Bruijn](sequences/de-bruijn.md) |
| Thue–Morse 수열 | 재귀 치환과 반복 제한 | [Thue–Morse](sequences/thue-morse.md) |
| 콜라츠 수열 | 홀짝 궤적과 경로 합류 | [콜라츠](sequences/collatz.md) |
| 로지스틱 사상·Lorenz 계 | 매개변수·초기값의 동역학 | [혼돈 동역학](sequences/chaotic-dynamics.md) |
| IFS·Mandelbrot | 수축·복소 반복의 형상 | [프랙탈](sequences/fractals.md) |

### 공간 배치

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| 잎차례·황금각 | 각도·반지름의 나선 배치 | [잎차례](space/phyllotaxis.md) |
| Poisson·Sobol·Halton | 최소 거리와 공간 피복 | [표본 배치](space/sampling.md) |
| Voronoi·Delaunay | 거리 영역과 이웃 관계 | [거리 기반 공간 구조](space/voronoi.md) |
| Hilbert 순서 | 계층적 순서와 지역성 | [공간 순서](space/hilbert.md) |
| 비주기 타일링·hat | 주기적 이동의 배제 | [비주기 타일링](space/aperiodic-tiling.md) |

### 형태와 국소 상호작용

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| Perlin·OpenSimplex2·fBm·좌표 변형 | 연속 변화와 규모 합성 | [노이즈](generation/noise.md) |
| L-system·Space colonization | 치환과 유인점 기반 분기 | [가지 성장](generation/branching.md) |
| 셀룰러 오토마타·Rule 90 | 이웃 상태의 동시 갱신 | [셀룰러 오토마타](generation/cellular-automata.md) |
| Gray–Scott | 반응·확산의 무늬 형성 | [반응·확산](generation/reaction-diffusion.md) |
| DLA·Physarum 입자 모델 | 부착 성장과 흔적 상호작용 | [입자 성장](generation/particle-growth.md) |
| Boids | 분리·정렬·응집의 운동 | [군집 운동](generation/boids.md) |
| 퍼콜레이션·공간 순환 경쟁 | 연결 임계와 공존 조건 | [공간 동역학](generation/spatial-dynamics.md) |
| Shan Shui Infinite·Fishdraw | 매개변수 기반 선 형상 | [절차적 그림](generation/procedural-illustration.md) |

### 구조와 제약

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| BSP·스패닝 트리·Wilson | 영역 분할과 연결 구성 | [공간 구성](structure/layout.md) |
| WFC·ConvChain | 국소 제약과 패턴 분포 | [패턴 합성](structure/pattern-synthesis.md) |
| MarkovJunior·그래프 문법 | 단계별 치환과 목표 제약 | [규칙 기반 구조](structure/markov-junior.md) |
| 정확 덮개·Algorithm X·DLX | 중복 없는 조건 충족 | [정확 덮개](structure/exact-cover.md) |
| 그래프 동형·정규 라벨 | 이름에 무관한 구조 비교 | [그래프 정규화](structure/canonical-graphs.md) |

### 화면 표현

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| 직교·등각 투영·패럴랙스 | 투영과 층별 깊이 단서 | [투영·패럴랙스](rendering/projection-parallax.md) |
| 빌보드·교차 평면·Impostor | 평면·깊이 데이터의 형상 대체 | [평면 기반 물체](rendering/billboards-impostors.md) |
| 스프라이트 노멀 맵 | 표면 방향의 조명 반응 | [스프라이트 조명](rendering/sprite-lighting.md) |
| 높이·거리 변위 매핑 | 시선과 표면의 교차 탐색 | [픽셀 변위](rendering/displacement.md) |
| 암시적 표면·Metaball·SDF | 등위면과 안전한 거리 보폭 | [암시적 표면](rendering/implicit-surfaces.md) |
| Mode 7·주사선별 투영 | 평면 변환과 축척 변화 | [배경 평면 변환](rendering/mode7.md) |

### 저장 표현

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| 팔레트·비트 패킹·메타타일 | 작은 값과 공통 조각의 재사용 | [팔레트·타일](storage/palette-tiles.md) |
| 포켓몬 그림 압축 | 평면·차분·XOR·RLE의 조합 | [포켓몬 코덱](storage/pokemon-codec.md) |
| LZ77·Huffman·DEFLATE·QOI | 반복·빈도·픽셀 차이의 부호 | [무손실 부호화](storage/lossless-codecs.md) |
| GPU 압축·Basis Universal | 전송·상주 형식의 연결 | [GPU 텍스처](storage/gpu-textures.md) |
| Draco·meshoptimizer | 기하 정밀도·부호·접근 순서 | [메시 표현](storage/mesh-compression.md) |
| CSR·COO·Roaring | 희소 값과 정수 집합의 표현 | [희소 표현](storage/sparse-sets.md) |
| 카운터 난수·Random123 | 호출 순서와 재생성의 분리 | [재생성·변경분](storage/reproducible-generation.md) |

### 데이터 처리와 선택

| 조사 대상 | 중심 성질 | 카드 |
|---|---|---|
| 콘텐츠 주소·Merkle DAG | 내용 식별과 변경 전파 | [내용 기반 식별](systems/content-addressing.md) |
| Bloom filter·HyperLogLog | 소속 가능성과 개수 요약 | [확률적 요약](systems/probabilistic-summaries.md) |
| Fractional indexing | 이웃 사이의 순서 키 생성 | [순서 키](systems/fractional-indexing.md) |
| CRDT·CALM | 병합 성질과 정보 단조성 | [수렴·조정](systems/crdt-calm.md) |
| URL 상태·Web Workers | 상태 운반과 계산 위치 | [클라이언트 처리](systems/client-processing.md) |
| FFT 합성곱 | 변환 영역의 공간 연산 | [FFT 합성곱](systems/fft-convolution.md) |
| 단조 경계·이분 탐색 | 한 번 바뀌는 조건의 탐색 | [단조 탐색](systems/monotone-search.md) |
| 브라에스 역설 | 선택·혼잡과 균형 비용 | [혼잡 경로 선택](systems/braess.md) |

## 읽는 방법

같은 모양을 만드는 방식이라도 보장하는 성질은 다르다. 최소 거리와 공간 피복, 국소 제약과 전체 연결, 명암과 실루엣, 저장 크기와 GPU 상주량을 카드의 원리·대안에서 비교한다. 합성한 기법의 설명을 반복하기보다 관련 카드로 연결했다. 직접 업로드와 재시도·멱등 처리는 기존 [파일 업로드](../stacks/storage/file-upload.md), [타임아웃·재시도·멱등 키](../stacks/api/timeout-retry-idempotency.md)를 함께 읽는다.

확인 날짜는 자료를 읽은 날짜다. 출처에는 읽은 정의·API·소스 위치와 자료 버전을 적었다. 기본 브랜치와 현재 문서는 적용 시 사용할 버전에서 다시 확인한다. 문헌의 성질, 조건에 따른 추론, 활용 가설과 직접 실행 결과를 구분한다. “제안 실험”은 실행 결과가 아니며, 직접 계산한 예제는 환경·입력·한도를 함께 적는다.

오픈소스를 도입하거나 코드를 재사용할 때는 선택한 버전의 라이선스·유지 상태·실행 환경·통합 비용을 추가로 확인한다. 자료를 읽었다는 사실을 구현의 정확성이나 적용 성능 검증으로 확대하지 않는다.
