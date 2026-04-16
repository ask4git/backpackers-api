# Google 소셜 로그인 프론트엔드 연동 가이드

## 방식

**Frontend-initiated OAuth** — 프론트가 Google SDK로 `id_token`을 직접 발급받고, 백엔드는 토큰 검증만 담당합니다.

```
프론트 → Google SDK → id_token 획득 → POST /auth/google/verify → JWT 반환
```

---

## 1. 패키지 설치

```bash
# React
npm install @react-oauth/google

# 또는 Next.js도 동일
```

---

## 2. 앱 최상단에 Provider 설정

```jsx
// main.jsx 또는 _app.tsx
import { GoogleOAuthProvider } from "@react-oauth/google";

root.render(
  <GoogleOAuthProvider clientId="586595362779-s7c5mj2k5p57m12qut4klp9850l63kmo.apps.googleusercontent.com">
    <App />
  </GoogleOAuthProvider>
);
```

---

## 3. 로그인 버튼 구현

```jsx
import { GoogleLogin } from "@react-oauth/google";

const BASE_URL = "https://backpackers-api.8x8077g16h76j.ap-northeast-2.cs.amazonlightsail.com";

function GoogleLoginButton() {
  const handleSuccess = async (credentialResponse) => {
    const idToken = credentialResponse.credential; // Google id_token

    const res = await fetch(`${BASE_URL}/auth/google/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: idToken }),
    });

    if (!res.ok) {
      console.error("로그인 실패");
      return;
    }

    const { access_token, user } = await res.json();
    localStorage.setItem("access_token", access_token);

    console.log("로그인 성공:", user);
    // 이동 처리 (예: navigate("/"))
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={() => console.error("Google 로그인 실패")}
    />
  );
}
```

---

## 4. 인증이 필요한 API 호출

토큰을 헤더에 포함해서 요청합니다.

```js
const BASE_URL = "https://backpackers-api.8x8077g16h76j.ap-northeast-2.cs.amazonlightsail.com";

async function fetchWithAuth(path, options = {}) {
  const token = localStorage.getItem("access_token");

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (res.status === 401) {
    // 토큰 만료 → 로그아웃 처리
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  }

  return res;
}

// 사용 예시 — 캠핑장 제보 (로그인 필요)
await fetchWithAuth("/spots/report", {
  method: "POST",
  body: JSON.stringify({
    name: "새 캠핑장",
    description: "설명",
    lat: 37.5,
    lng: 127.0,
    address: "서울시 ...",
  }),
});
```

---

## 5. 로그아웃

```js
function logout() {
  localStorage.removeItem("access_token");
  window.location.href = "/login";
}
```

---

## 정리

| 단계 | 내용 |
|------|------|
| 1 | `GoogleOAuthProvider` 로 앱 감싸기 |
| 2 | `<GoogleLogin onSuccess={...} />` 버튼 렌더링 |
| 3 | `credentialResponse.credential` → `POST /auth/google/verify` 전송 |
| 4 | 응답의 `access_token` → `localStorage` 저장 |
| 5 | 이후 모든 요청에 `Authorization: Bearer <token>` 헤더 포함 |

---

## 참고

- 토큰 만료 시간: **24시간** (`ACCESS_TOKEN_EXPIRE_MINUTES=1440`)
- 만료 후 재로그인 필요 (자동 갱신 미구현)
- 인증 필요 API: `POST /spots/report`
