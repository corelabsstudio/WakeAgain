/**
 * Demo guidance — plain language first. URL is optional, not required.
 */
(function (global) {
  var TIPS = {
    website: {
      title: "웹사이트 — 이렇게 적으면 됩니다",
      easy: "주소가 없어도 됩니다. 화면을 글로 적어도 OK.",
      steps: [
        "가장 쉬움: 「메인 화면 → 무슨 버튼 → 결과가 뭐」 3줄 글",
        "주소가 있으면 붙여 넣기 (선택)",
        "화면 녹화 영상이 있으면 링크 추가 (선택)",
      ],
      example:
        "1) 메인에서 프로젝트를 고름\n2) 시작 버튼을 누르면 진행 화면\n3) 끝나면 결과 요약이 보임\n(주소·영상 링크는 있으면 적고, 없어도 됨)",
      fill:
        "1) 홈/메인에서 무엇을 고르거나 입력함\n2) 핵심 버튼을 누르면 이런 화면으로 바뀜\n3) 결과로 ○○가 보임\n지원: 웹 브라우저\n참고: 주소·영상 링크는 있으면 추가 (없어도 등록 가능)",
    },
    webapp: {
      title: "웹 앱·SaaS — 이렇게 적으면 됩니다",
      easy: "공개 주소 없어도 됩니다. 쓰는 흐름만 적으면 됩니다.",
      steps: [
        "가입 → 메인 기능 → 결과 순서를 글로",
        "주소·영상은 있으면 좋고, 없어도 등록 가능",
        "안 되는 기능은 「지금 안 되는 것」칸에",
      ],
      example:
        "1) 로그인(또는 게스트) 후 대시보드\n2) ○○ 기능을 실행하면 진행 표시\n3) 결과 리포트/목록이 나옴\n주소·영상은 선택",
      fill:
        "1) 시작 화면에서 로그인 또는 바로 시작\n2) 핵심 기능(○○)을 실행하면 처리됨\n3) 결과 화면/목록을 볼 수 있음\n주소·영상 링크: 있으면 적기 (없어도 됨)",
    },
    mobile: {
      title: "모바일 앱 — 이렇게 적으면 됩니다",
      easy: "스토어 링크 없어도 됩니다. 폰 화면 순서만 적어도 OK.",
      steps: [
        "홈 → 핵심 기능 → 결과 화면을 글로",
        "영상·스토어 링크는 선택",
        "iOS/Android 중 어디인지 한 줄",
      ],
      example:
        "1) 앱 켜면 홈\n2) ○○ 탭에서 기능 실행\n3) 결과 화면\n지원: Android (예시)",
      fill:
        "1) 앱을 켜면 홈/목록이 보임\n2) ○○ 기능을 누르면 동작함\n3) 결과 화면이 나옴\n지원 OS: (Android / iOS)\n스토어·영상 링크: 있으면 추가 (없어도 됨)",
    },
    desktop: {
      title: "PC 프로그램 — 이렇게 적으면 됩니다",
      easy: "URL 필요 없습니다. 「실행하면 뭐가 되는지」만 적으면 됩니다.",
      steps: [
        "실행 → 첫 화면 → 핵심 기능 1~2개를 글로",
        "Windows/Mac 등 지원 OS 한 줄",
        "영상 링크는 있으면 좋고, 없어도 됨",
      ],
      example:
        "1) ReachKit.bat 실행 시 홈 화면\n2) ① 사이트 주소 넣으면 홍보글 생성\n3) ②③으로 올릴 곳·작성 보조\n지원: Windows 10/11\n(영상 있으면 링크 추가)",
      fill:
        "1) 실행하면 홈(또는 메인 창)이 뜸\n2) 핵심 기능: ○○ 하면 △△ 됨\n3) 이어서 □□ 까지 가능\n지원 OS: Windows 10/11\n필수 환경: (예: Python 없어도 실행 / .NET 필요 등)\n영상·설치 링크: 있으면 추가 (없어도 등록 가능)",
    },
    api: {
      title: "API·백엔드 — 이렇게 적으면 됩니다",
      easy: "서버 공개 주소가 없어도 됩니다. 요청·응답 예시면 OK.",
      steps: [
        "주요 엔드포인트 2~3개와 응답 예시를 글/코드 블록으로",
        "문서·영상 링크는 선택",
      ],
      example:
        "POST /v1/… → 200 { … }\nGET /v1/… → 목록\n문서·영상은 선택",
      fill:
        "주요 API:\n1) POST /… → 성공 시 … 반환\n2) GET /… → 목록 조회\n실행 방법: (로컬 / 도커 / 문서 참고)\n공개 문서·영상: 있으면 추가 (없어도 됨)",
    },
    game: {
      title: "게임 — 이렇게 적으면 됩니다",
      easy: "플레이 흐름을 글로 적어도 됩니다. 영상은 선택.",
      steps: [
        "시작 → 조작 → 한 판 결과 순서로 글",
        "플랫폼(PC/모바일) 한 줄",
      ],
      example:
        "1) 시작 화면\n2) 방향키로 이동·공격\n3) 스테이지 클리어/실패\nPC · 키보드",
      fill:
        "1) 시작하면 타이틀/스테이지 선택\n2) 조작: …\n3) 목표/클리어 조건: …\n플랫폼: PC (또는 모바일)\n영상 링크: 있으면 추가 (없어도 됨)",
    },
    other: {
      title: "기타 — 이렇게 적으면 됩니다",
      easy: "남이 읽고 이해할 수 있는 설명이면 됩니다. URL 필수는 아닙니다.",
      steps: [
        "무엇인지 · 어떻게 쓰는지 · 한계 3줄",
        "링크·영상은 선택",
      ],
      example:
        "무엇인지: …\n쓰는 방법: …\n한계: …",
      fill:
        "무엇인지: …\n쓰는 방법 1)\n2)\n3)\n한계: …\n링크·영상: 있으면 추가 (없어도 됨)",
    },
  };

  var DEFAULT = {
    title: "구매자가 알아볼 설명 (URL 필수 아님)",
    easy: "주소·영상 없어도 됩니다. 화면 순서를 글로 적어도 올릴 수 있어요.",
    steps: [
      "가장 쉬움: 1) 첫 화면 2) 핵심 기능 3) 결과 — 세 줄 글",
      "있으면: 영상 링크나 주소를 덧붙이기",
      "안 되는 건 「지금 안 되는 것」칸에",
    ],
    example: "1) …\n2) …\n3) …\n(링크는 선택)",
    fill:
      "1) 시작하면 이런 화면이 보임\n2) 핵심 기능(○○)을 하면 △△ 됨\n3) 결과로 □□ 가 보임\n지원: …\n주소·영상: 있으면 추가 (없어도 등록 가능)",
  };

  var FILLS = {
    screen: {
      label: "화면 글로 쓰기",
      text:
        "1) 시작하면 ○○ 화면이 보임\n2) △△ 버튼을 누르면 … 동작함\n3) 결과로 □□ 를 볼 수 있음\n지원 환경: …\n※ 주소·영상 링크 없음 (글 설명만)",
    },
    local: {
      label: "PC 실행 설명",
      text:
        "1) 실행 파일/배치로 켜면 메인 창이 뜸\n2) 핵심 기능: … 하면 … 됨\n3) 이어서 … 까지 가능\n지원: Windows 10/11\n※ 설치·소스는 성사·입금 후 이전. 공개 URL 없음.",
    },
    video: {
      label: "영상 있음 (링크 칸)",
      text:
        "1) 영상에서 메인 화면 → 핵심 기능 → 결과 순서로 보여 줌\n2) 영상 링크: (여기에 붙여 넣기)\n3) 지원 환경: …\n※ 링크 준비 전이면 「화면 글로 쓰기」를 쓰세요.",
    },
  };

  function tipFor(key) {
    return TIPS[key] || DEFAULT;
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderHtml(key) {
    var t = tipFor(key);
    var steps = (t.steps || [])
      .map(function (s, i) {
        return "<li><strong>" + (i + 1) + ".</strong> " + escapeHtml(s) + "</li>";
      })
      .join("");
    return (
      '<div class="demo-help-card">' +
      "<strong>" +
      escapeHtml(t.title) +
      "</strong>" +
      '<p class="demo-help-easy">' +
      escapeHtml(t.easy) +
      "</p>" +
      "<ol class='demo-help-steps'>" +
      steps +
      "</ol>" +
      (t.example
        ? '<p class="demo-help-label">데모 칸 예시 (복붙·수정 OK)</p><pre class="demo-help-example">' +
          escapeHtml(t.example) +
          "</pre>"
        : "") +
      '<p class="demo-help-foot muted fine"><strong>URL은 필수가 아닙니다.</strong> 글 설명만으로도 올릴 수 있어요. · <a class="text-link" href="/guide/demo.html" target="_blank" rel="noopener">자세히</a></p>' +
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
        textareaEl.placeholder =
          "URL 없이 글만 적어도 됩니다. 예)\n" + t.example;
      }
    }
  }

  function fillText(key) {
    var t = tipFor(key);
    return t.fill || t.example || DEFAULT.fill;
  }

  global.WakeAgainDemoHelp = {
    tips: TIPS,
    fills: FILLS,
    tipFor: tipFor,
    fillText: fillText,
    renderHtml: renderHtml,
    applyTo: applyTo,
  };
})(typeof window !== "undefined" ? window : globalThis);
