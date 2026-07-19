/**
 * Demo guidance for non-technical / vibe-coding sellers.
 * Used by app registration + sell form.
 */
(function (global) {
  var TIPS = {
    website: {
      title: "웹사이트 데모 — 이렇게 올리세요",
      easy: "가장 쉬운 방법: 접속 가능한 주소 한 줄",
      steps: [
        "브라우저 주소창 링크를 복사해 붙여 넣기 (예: https://…)",
        "로그인이 필요하면 체험 계정 또는 「비회원으로 볼 수 있는 화면」을 적기",
        "주소가 없으면: 폰/PC 화면 녹화 후 YouTube 비공개·Loom에 올리고 링크 적기",
      ],
      example:
        "[사이트] https://my-trace.example\n[영상] https://… (2분, 메인→기능→결과)\n[계정] 게스트 / 샘플 로그인",
    },
    webapp: {
      title: "웹 앱·SaaS 데모 — 이렇게 올리세요",
      easy: "공개 URL이 없어도 됩니다. 동작 영상만으로도 검수 가능합니다.",
      steps: [
        "가능하면 스테이징·임시 주소. 없으면 화면 녹화 1~2분",
        "Windows: Win+G 또는 브라우저 확장 / Mac: Cmd+Shift+5 로 화면 녹화",
        "Loom·YouTube(링크 있는 사람만)·Drive 공유 후 링크를 데모 칸에 적기",
        "핵심 화면 2~3개만: 로그인 → 메인 기능 → 결과",
      ],
      example:
        "[영상] https://loom.com/share/…\n[흐름] 가입 없이 대시보드 → 분석 실행 → 리포트\n[제한] 샘플 데이터만",
    },
    mobile: {
      title: "모바일 앱 데모 — 이렇게 올리세요 (코딩 몰라도 OK)",
      easy: "스토어 링크가 없어도 됩니다. 폰 화면 녹화가 가장 확실합니다.",
      steps: [
        "아이폰: 제어센터 → 화면 기록 / 안드로이드: 빠른 설정 → 화면 녹화",
        "앱을 켜고 핵심 기능만 1~2분 찍기 (말 안 해도 됨)",
        "영상 파일을 YouTube 비공개·Drive·Loom에 올리고 링크 붙여 넣기",
        "있으면: TestFlight / Play 내부 테스트 링크도 같이",
        "스크린샷만 있어도 됨 → 사진 순서대로 설명 글로 적기",
      ],
      example:
        "[영상] https://… (아이폰 화면 기록 1분 40초)\n1) 홈 2) 추적 시작 3) 결과 화면\n[체험] 없음 · 소스·설치는 성사 후",
    },
    desktop: {
      title: "데스크톱 프로그램 데모 — 이렇게 올리세요",
      easy: "설치 파일을 지금 안 올려도 됩니다. 「돌아가는 모습」만 보여 주세요.",
      steps: [
        "PC에서 프로그램 실행 → 화면 녹화 (Win+G / Cmd+Shift+5)",
        "설치→실행→주요 기능 1~2개만. 길면 구매자가 안 봅니다",
        "영상 업로드 후 링크를 데모 칸에 적기",
        "설치가 복잡하면 「로컬에서만 실행됨」을 솔직히 적기 (프로토타입 상태 권장)",
      ],
      example:
        "[영상] https://… (Windows 실행 2분)\n[환경] Windows 10 · 설치 2분\n[제한] 라이선스 키 없음 · 성사 후 소스 전달",
    },
    api: {
      title: "API·백엔드 데모 — 이렇게 올리세요",
      easy: "서버를 공개 안 해도 됩니다. 요청·응답 예시가 있으면 됩니다.",
      steps: [
        "Postman/스크린으로 API 호출하는 짧은 영상",
        "또는 JSON 응답 예시 + 엔드포인트 목록을 글로",
        "Swagger/OpenAPI 링크가 있으면 최고",
      ],
      example:
        "[문서] https://…/docs\n[예시] POST /v1/trace → 200 {…}\n[영상] 호출 30초 녹화",
    },
    game: {
      title: "게임 데모 — 이렇게 올리세요",
      easy: "플레이 영상 1~2분이면 충분합니다.",
      steps: [
        "플레이 화면 녹화 (시작→조작→한 판 클리어/패배)",
        "웹 빌드가 있으면 링크, 없으면 영상만",
        "조작법 한 줄 적기",
      ],
      example: "[영상] https://…\n[플랫폼] PC · 키보드\n[상태] 프로토타입 1스테이지",
    },
    other: {
      title: "기타 제품 데모 — 이렇게 올리세요",
      easy: "「남이 보고 이해되는 증거」면 됩니다. URL 필수는 아닙니다.",
      steps: [
        "화면·동작 녹화 또는 사진 + 설명",
        "무엇을 보여 주는지 3줄로 적기",
        "설치·계정 필요 여부를 솔직히",
      ],
      example: "[영상/설명] …\n[보는 방법] …\n[제한] …",
    },
  };

  var DEFAULT = {
    title: "데모 안내 (바이브 코딩·비개발자도 OK)",
    easy: "완벽한 배포 URL이 없어도 됩니다. 동작이 보이면 됩니다.",
    steps: [
      "가장 쉬운 방법: 화면 녹화 1~2분 → 유튜브/룸/드라이브 링크",
      "그다음: 스크린 설명 (1. 메인 2. 기능 3. 결과)",
      "과장은 검수·신뢰에 불리합니다. 안 되는 부분은 적기",
    ],
    example: "[영상] …\n[설명] …",
  };

  function tipFor(key) {
    return TIPS[key] || DEFAULT;
  }

  function renderHtml(key) {
    var t = tipFor(key);
    var steps = (t.steps || [])
      .map(function (s, i) {
        return "<li><strong>" + (i + 1) + ".</strong> " + s + "</li>";
      })
      .join("");
    return (
      '<div class="demo-help-card">' +
      "<strong>" +
      t.title +
      "</strong>" +
      '<p class="demo-help-easy">' +
      t.easy +
      "</p>" +
      "<ol class='demo-help-steps'>" +
      steps +
      "</ol>" +
      (t.example
        ? '<p class="demo-help-label">데모 칸 예시</p><pre class="demo-help-example">' +
          t.example +
          "</pre>"
        : "") +
      '<p class="demo-help-foot muted fine">화면 녹화만 할 줄 알면 됩니다. 서버 배포·스토어 등록은 필수가 아닙니다. · <a class="text-link" href="/guide/demo.html" target="_blank" rel="noopener">자세히 보기</a></p>' +
      "</div>"
    );
  }

  function applyTo(boxEl, textareaEl, key) {
    if (boxEl) {
      if (!key) {
        boxEl.hidden = true;
        boxEl.innerHTML = "";
      } else {
        boxEl.hidden = false;
        boxEl.innerHTML = renderHtml(key);
      }
    }
    if (textareaEl && key) {
      var t = tipFor(key);
      if (t.example && !textareaEl.value) {
        textareaEl.placeholder = t.example.replace(/\n/g, " · ");
      }
    }
  }

  global.WakeAgainDemoHelp = {
    tips: TIPS,
    tipFor: tipFor,
    renderHtml: renderHtml,
    applyTo: applyTo,
  };
})(typeof window !== "undefined" ? window : globalThis);
