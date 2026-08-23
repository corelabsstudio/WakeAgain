/**
 * footer-visitors.js 회귀 테스트 — 방문 집계에 실리는 유입 경로.
 *
 * 2026-08-23 버그: 첫 방문 때 localStorage에 "(direct)"를 저장하고, 그 값을 이후
 * 모든 방문의 utm_source로 보냈다. 서버는 utm을 referrer보다 우선하므로
 * **재방문이 전부 direct로 덮였다.** 아래 B·D가 그 회귀를 잡는다.
 *
 *   node _visit_source_front_test.js
 */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SRC = fs.readFileSync(path.join(__dirname, "public/js/footer-visitors.js"), "utf8");
const OK = [];
const FAIL = [];

function check(name, cond, extra) {
  (cond ? OK : FAIL).push(name);
  console.log((cond ? "  ok  " : " FAIL ") + name + (!cond && extra ? "  — " + extra : ""));
}

/** 브라우저 한 대를 흉내낸다. store는 방문 사이에 유지되는 localStorage. */
function visit(opts) {
  const store = Object.assign({}, opts.store || {});
  const posted = [];
  const mounted = [];
  const el = { id: "", className: "", innerHTML: "", setAttribute() {}, appendChild: (n) => mounted.push(n) };
  const scriptEl = {
    getAttribute: (k) => (k === "data-render" && opts.renderOff ? "off" : null),
  };
  const created = [];

  const sandbox = {
    console,
    URLSearchParams,
    crypto: { randomUUID: () => "11111111-2222-3333-4444-555555555555" },
    localStorage: {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => {
        store[k] = String(v);
      },
      removeItem: (k) => {
        delete store[k];
      },
    },
    fetch: (url, init) => {
      posted.push({ url: url, body: JSON.parse(init.body) });
      return Promise.resolve({ json: () => Promise.resolve({ visitors: 1, today_visitors: 1 }) });
    },
    document: {
      readyState: "complete",
      referrer: opts.referrer || "",
      cookie: "",
      currentScript: scriptEl,
      addEventListener() {},
      // 붙인 노드를 id로 되찾을 수 있어야 ensureEl이 실제 DOM처럼 한 번만 만든다
      getElementById: (id) => mounted.find((n) => n.id === id) || null,
      querySelector: (sel) => (sel === "footer" ? el : null),
      createElement: (t) => {
        const node = { tag: t, id: "", className: "", innerHTML: "", setAttribute() {}, appendChild() {} };
        created.push(node);
        return node;
      },
    },
  };
  sandbox.window = sandbox;
  sandbox.window.location = { search: opts.search || "", href: opts.href || "https://wakeagain.com/", pathname: opts.pathname || "/" };
  sandbox.localStorage = sandbox.localStorage; // 스크립트가 bare `localStorage`로 접근

  vm.createContext(sandbox);
  vm.runInContext(SRC, sandbox);

  return { store, posted, created, source: sandbox.window.WakeAgainSource.get() };
}

// A. 신규 방문 + 구글 리퍼러 → 표식은 비고, 리퍼러는 그대로 실려 서버가 판정한다
let r = visit({ referrer: "https://www.google.com/" });
check("A 신규+구글: utm_source 비어 있음", r.posted[0].body.utm_source === "", JSON.stringify(r.posted[0].body));
check("A 신규+구글: referrer 전달됨", r.posted[0].body.referrer === "https://www.google.com/");

// B. 레거시 "(direct)"를 물고 있는 재방문자 + 구글 리퍼러 (← 이번 버그의 핵심)
r = visit({ referrer: "https://www.google.com/", store: { wa_src: "(direct)", wa_vid: "abcdefgh1234" } });
check("B 재방문+구글: direct로 덮이지 않음", r.posted[0].body.utm_source === "", "utm_source=" + r.posted[0].body.utm_source);
check("B 재방문+구글: referrer 살아 있음", r.posted[0].body.referrer === "https://www.google.com/");

// C. URL에 표식이 붙어 온 방문 → 표식이 실리고 first-touch로 저장된다
r = visit({ search: "?utm_source=github", referrer: "" });
check("C 표식 방문: utm_source 전달", r.posted[0].body.utm_source === "github");
check("C 표식 방문: first-touch 저장", r.store.wa_src === "github");

// D. 예전에 github 표식으로 알게 됐지만 오늘은 구글로 들어온 재방문자
r = visit({ referrer: "https://www.google.com/", store: { wa_src: "github", wa_vid: "abcdefgh1234", wa_src_ref: "https://github.com/" } });
check("D 재방문: 오늘 집계는 이번 방문 기준(빈 표식)", r.posted[0].body.utm_source === "", "utm_source=" + r.posted[0].body.utm_source);
check("D 재방문: 가입 귀속은 first-touch 유지", r.source.source === "github");
check("D 재방문: first-touch 리퍼러 안 덮임", r.store.wa_src_ref === "https://github.com/");

// E. data-render="off" — 집계는 하되 푸터에 숫자를 그리지 않는다
r = visit({ referrer: "", renderOff: true });
check("E render=off: 집계는 그대로 전송", r.posted.length === 1);
check("E render=off: 카운터 DOM 미생성", r.created.length === 0, "created=" + r.created.length);

r = visit({ referrer: "" });
check("E' 기본: 카운터 DOM 생성됨", r.created.length === 1);

console.log("\n통과 " + OK.length + " / 실패 " + FAIL.length);
if (FAIL.length) {
  console.log("실패: " + FAIL.join(", "));
  process.exit(1);
}
