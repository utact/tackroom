# 서체·정보 위계·현지화

확인: 2026-10-04.

## 요약

제목·본문·보조 정보의 위계를 서체 역할로 정하고 언어·확대 설정에서 검증한다.

## 문제 신호

큰 글자에서 버튼이 잘리거나 한글·숫자·다른 언어의 높이와 폭이 어긋난다.

## 기준선의 한계

디자인 시안의 고정 크기와 짧은 예시 문구만으로 실제 콘텐츠를 처리할 수 없다.

## 원리

제목·본문·레이블의 역할을 정하고 크기·굵기·행간·간격으로 위계를 표현한다. 시각적 크기와 의미상 제목 구조는 함께 맞춘다. Apple의 Dynamic Type과 Android의 sp는 사용자 글자 크기 설정을 반영한다.

Material 3의 기본 본문 크기·행간은 bodyLarge 16/24sp, bodyMedium 14/20sp, bodySmall 12/16sp다. Android는 본문을 12sp보다 작게 하지 않도록 권장하고 Apple의 터치 UI 안내는 최소 11pt를 제시한다. 하한이 모든 본문에 적합한 크기라는 뜻은 아니며 단위·서체·사용 맥락을 구분한다.

## 가치

콘텐츠 양과 접근성 설정이 바뀌어도 중요도를 읽을 수 있다.

## 트레이드오프와 리스크

브랜드 서체의 글리프 범위·라이선스·로딩 비용을 확인해야 한다. 텍스트 확대를 막아 배치를 유지하면 읽기 요구를 놓친다.

## 대안과 경계

플랫폼의 시스템 서체와 텍스트 역할을 기준선으로 삼는다. 웹에는 모든 본문에 적용할 단일 WCAG 최소 글자 크기가 없으므로 확대·대비·재배치 조건을 확인한다. 장식 서체는 짧은 제목·삽화 등 적합한 범위에 한정한다.

## 깊이 있는 활용

한글·라틴·숫자의 혼합 문구와 긴 번역을 실제 화면에 넣어 위계를 조정한다.

## 임시방책의 신호

제목은 늘 한 줄이라는 가정으로 생략하거나 이미지를 써서 본문을 고정한다.

## 실패 재현

최대 지원 글자 크기에서 긴 버튼명·가격·오류 문구를 표시한다.

## 측정과 검증

문자 누락, 잘림, 줄 수, 읽기 순서와 주요 행동의 노출을 확인한다. 굵기·크기만 바꿔도 제목·본문·보조 정보의 역할을 구별할 수 있는지 실제 콘텐츠로 검토한다.

## 재검토 조건

지원 언어·서체·OS가 바뀌면 글리프와 확대 동작을 재검토한다.

## 출처

- [Apple Dynamic Type](https://developer.apple.com/videos/play/wwdc2024/10074/): 텍스트 확대와 배치.
- [WAI 제목 구조](https://www.w3.org/WAI/tutorials/page-structure/headings/): 의미에 따른 제목 위계.
- [Compose Material 3](https://developer.android.com/develop/ui/compose/designsystems/material3): 텍스트 역할과 기본 크기·행간.
- [Android 접근성](https://developer.android.com/design/ui/mobile/guides/foundations/accessibility): sp와 본문 12sp 하한 권장.
- [Apple UI Design Dos and Don’ts](https://developer.apple.com/design/tips/): 터치 UI의 글자 크기 안내.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/): 텍스트 확대·대비·재배치 기준.
