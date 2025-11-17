# Frontend Guide

## 프로젝트 구조 개요

- **Expo Router 기반 라우팅**  
  `app` 폴더의 디렉터리 구조가 곧 라우팅 구조입니다.  
  - `(auth)` 그룹: 로그인/회원가입 등 인증 화면  
  - `(tabs)` 그룹: 홈, 구독, 프로필 등 탭 스택  
  - `[param]` 폴더: 동적 라우트 (예: `topic/[topic].tsx`, `article/[id].tsx`)
- **전역 상태 관리**  
  `providers/AuthProvider.tsx`에서 인증, 사용자 정보, 구독 토픽 등을 Context로 제공합니다. `useAuth()` 훅으로 전역 상태에 접근합니다.
- **공용 유틸**  
  - `utils/api.ts`: 모든 REST API 요청 정의  
  - `types/`: DTO 및 공용 타입  
  - `components/`: 재사용 UI (예: `FeedCard`, `NavigationHeader`, `ServerConnectivityBanner`, `FeedState`)  
  - `hooks/`: 공용 훅 (`useServerConnectivity`, `useFeedLoader` 등)

## 코드 스타일 가이드

1. **함수형 컴포넌트 + Hooks**  
   - `useCallback`, `useMemo`, `useEffect` 의존성 배열을 명확히 관리하고, ESLint 경고가 없도록 유지합니다.
   - 로딩/에러/데이터 상태는 `useState`와 공용 훅(`useFeedLoader`)을 활용합니다.

2. **상태/데이터 패턴 통일**  
   - 비동기 피드 로딩은 `useFeedLoader` 훅을 사용해 `isLoading`, `isRefreshing`, `error`, `reload`, `refresh`를 일관되게 처리합니다.
   - 알림, 구독 등 전역 데이터는 `useAuth()`에서 제공되는 메서드(`refreshProfile`, `refreshSubscribedTopics` 등)를 통해 갱신합니다.

3. **재사용 컴포넌트 활용**  
   - 공통 로딩/에러 UI는 `FeedLoadingState`, `FeedErrorState`를 사용합니다.
   - 카드/헤더/배너 등 기존 컴포넌트를 재사용하고, 필요 시 props로 커스터마이즈합니다.  
   - 새로운 UI 패턴이 반복된다면 `components/`에 컴포넌트를 추가하고, 각 화면에서는 props만 전달하는 구조로 만듭니다.

4. **스타일 작성**  
   - `StyleSheet.create`를 사용하고, 색상/여백 스케일은 기존 값(예: `#2563eb`, `gap: 12`, `paddingHorizontal: 20`)을 따릅니다.
   - 컴포넌트 파일 하단에 스타일을 정의하며, 이름/구조를 다른 화면과 일관되게 유지합니다.

5. **타입스크립트 & 린트**  
   - 모든 새 파일/컴포넌트는 TS 타입을 명시합니다.
   - `npm run lint` 와 `npx tsc --noEmit`가 항상 통과하도록 합니다. 경고가 나오면 즉시 수정합니다.

## 컴포넌트/훅 사용 기준

- **FeedCard**: 기사/토픽 리스트 항목에 사용. `onPressCard`, `onPressTopic`, `showDate` 등 props로 동작 제어.
- **NavigationHeader**: 화면 상단의 뒤로가기 + 우측 버튼. `title`, `onBack`, `rightButton` 등을 전달.
- **FeedState (Loading/Error)**: 피드 로딩/실패 UI를 통일. 메시지, 재시도 콜백만 주입.
- **useFeedLoader**:  
  ```ts
  const fetcher = useCallback(async () => {
    const response = await getSubscribedArticles(token, 0, 100);
    return response.items;
  }, [token]);

  const { items, isLoading, isRefreshing, error, reload, refresh } = useFeedLoader({
    fetcher,
    fallbackErrorMessage: '피드를 불러올 수 없습니다',
  });
  ```
  - `items`: 화면에서 사용할 데이터  
  - `reload()`: 로딩 상태로 다시 요청  
  - `refresh()`: 풀투리프레시 핸들러에 연결  
  - `error`: 실패 메시지 표시용

## 개발 워크플로우

1. 화면 추가 시
   - `app/` 경로와 라우트 네이밍 규칙을 따릅니다.
   - 필요한 경우 `_layout.tsx`를 수정해 그룹 레이아웃(탭/스택)을 조정합니다.
2. API 호출
   - `utils/api.ts`에 함수를 추가하고, `types`에 DTO를 정의합니다.
   - `useAuth`나 전역 훅에서 재사용해야 하면 해당 Provider/Hooks에 메서드를 추가합니다.
3. 검사
   - `npm run lint` / `npx tsc --noEmit` / 필요 시 `npm run test`로 검증합니다.
   - Expo 앱 실행 후 주요 흐름(로그인, 피드 로딩, 구독 토글)을 직접 확인합니다.

## 컨벤션 요약

- 파일명/컴포넌트명은 PascalCase, 훅은 camelCase + `use` 접두어.
- 네트워크 에러는 콘솔에 상세 로그를 남기고, 사용자에게는 Alert 또는 ErrorState로 안내.
- 상태는 불변성을 지키며 업데이트하고, AsyncStorage/연결 상태는 Provider에서 관리.
- UI 텍스트와 Alert는 한글로 통일. (예: “안내”, “다시 시도” 등)

이 가이드를 기준으로 새 기능을 추가하거나 코드를 리팩터링하면, 현재 프로젝트와 자연스럽게 어우러집니다.
