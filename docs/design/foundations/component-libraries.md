# 컴포넌트 재사용과 라이브러리

확인: 2026-10-04.

## 요약

내장 컨트롤, 스타일이 없는 동작 라이브러리, 테마를 제공하는 라이브러리를 역할별로 비교한다.

## 문제 신호

대화상자·메뉴마다 초점과 키보드 동작을 직접 구현해 같은 결함이 반복된다.

## 기준선의 한계

도형과 클릭 이벤트를 조합하는 방식은 입력·상태·접근성 구현까지 떠안는다.

## 원리

웹의 Radix Primitives는 스타일 없이 역할·초점·키보드 동작을 제공한다. Material UI는 Material 계열 컴포넌트를 제공한다. 네이티브·Flutter에서는 플랫폼 컨트롤과 Material·Cupertino 계열을 검토한다.

## 가치

기존 동작을 재사용하면서 제품의 표현 범위를 조정한다.

## 트레이드오프와 리스크

Radix Primitives와 Material UI의 확인한 라이선스는 MIT다. 별도 제품·유료 기능까지 같은 조건으로 간주하지 않는다. 래핑과 스타일 변경 후에도 동작을 검증해야 한다.

## 대안과 경계

단순 화면은 내장 컨트롤로 충분할 수 있다. 사용자 정의는 기존 구현으로 요구를 충족할 수 없는 부분에 한정한다.

## 깊이 있는 활용

필요한 컴포넌트만 골라 테마·SSR·포털·폼 상태와의 연결을 검토한다.

## 임시방책의 신호

라이브러리 설치를 디자인 완성으로 보고 기본 예제를 그대로 제품에 넣는다.

## 실패 재현

메뉴 안의 대화상자, 중첩 포털, 폼 오류와 화면 전환에서 초점 복귀를 확인한다.

## 측정과 검증

실제 번들 크기, 스타일 재정의 범위, 입력 동작과 지원 버전의 호환성을 비교한다.

## 재검토 조건

컴포넌트 동작을 크게 재정의하거나 여러 체계가 섞이면 재사용 범위를 다시 정한다.

## 출처

- [Radix Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction), [라이선스](https://github.com/radix-ui/primitives/blob/main/LICENSE): 동작 기반과 MIT 조건.
- [Material UI](https://mui.com/material-ui/getting-started/), [라이선스](https://github.com/mui/material-ui/blob/master/LICENSE), [Flutter Cupertino](https://docs.flutter.dev/ui/widgets/cupertino): 컴포넌트 체계.
