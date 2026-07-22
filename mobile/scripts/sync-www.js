/**
 * Copy WakeAgain web client into Capacitor www/ for Play Store & App Store.
 * - Full public/ mirror (same screens as the website)
 * - Landing page stays as index.html (homepage)
 * - App shell at app/index.html
 * - runtime-config.js injects WAKEAGAIN_API_BASE
 */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..", "..");
const publicDir = path.join(root, "public");
const www = path.join(__dirname, "..", "www");
const mobileRoot = path.join(__dirname, "..");

function rimraf(dir) {
  if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true });
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const name of fs.readdirSync(src)) {
    if (name === ".DS_Store") continue;
    const s = path.join(src, name);
    const d = path.join(dest, name);
    if (fs.statSync(s).isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function injectRuntime(html) {
  if (html.includes("runtime-config.js")) return html;
  // Prefer inject before api.js
  if (html.includes('src="/js/api.js"') || html.includes("src=\"/js/api.js\"")) {
    return html.replace(
      /<script src="\/js\/api\.js[^"]*"><\/script>/,
      '<script src="/js/runtime-config.js"></script>\n  <script src="/js/api.js"></script>\n  <script src="/js/native-bridge.js"></script>'
    );
  }
  if (html.includes('src="../js/api.js"')) {
    return html.replace(
      /<script src="\.\.\/js\/api\.js[^"]*"><\/script>/,
      '<script src="../js/runtime-config.js"></script>\n  <script src="../js/api.js"></script>\n  <script src="../js/native-bridge.js"></script>'
    );
  }
  // Fallback: inject before </head>
  if (html.includes("</head>")) {
    return html.replace(
      "</head>",
      '  <script src="/js/runtime-config.js"></script>\n  <script src="/js/native-bridge.js"></script>\n</head>'
    );
  }
  return html;
}

function rewriteAppShell(html) {
  let out = injectRuntime(html);
  // absolute → relative for packaged app under app/
  const pairs = [
    ['href="/styles.css', 'href="../styles.css'],
    ['href="/ux9.css', 'href="../ux9.css'],
    ['href="/app/app.css', 'href="app.css'],
    ['href="/favicon.ico"', 'href="../favicon.ico"'],
    ['href="/favicon.svg"', 'href="../favicon.svg"'],
    ['href="/manifest.webmanifest"', 'href="../manifest.webmanifest"'],
    ['src="/js/', 'src="../js/'],
    ['src="/app/app.js', 'src="app.js'],
    ['href="/app/"', 'href="./index.html"'],
    ['href="/app/#', 'href="./index.html#'],
    ['href="/buy.html"', 'href="../buy.html"'],
    ['href="/sell.html"', 'href="../sell.html"'],
    ['href="/legal/', 'href="../legal/'],
    ['href="/guide/', 'href="../guide/'],
    ['href="/showcase.html"', 'href="../showcase.html"'],
    ['href="/showcase-new.html"', 'href="../showcase-new.html"'],
    ['href="/diagnose.html"', 'href="../diagnose.html"'],
    ['href="/project.html', 'href="../project.html'],
    ['href="/review.html"', 'href="../review.html"'],
    ['href="/get-app.html"', 'href="../get-app.html"'],
    // Homepage (landing) — critical for "홈" from app shell
    ['href="/"', 'href="../index.html"'],
    ['href="/#"', 'href="../index.html#"'],
  ];
  for (const [a, b] of pairs) {
    out = out.split(a).join(b);
  }
  // data-nav-home links that were rewritten away: ensure brand/home work
  // viewport safe area for notched phones
  if (!out.includes("viewport-fit=cover")) {
    out = out.replace(
      "width=device-width, initial-scale=1",
      "width=device-width, initial-scale=1, viewport-fit=cover"
    );
  }
  return out;
}

function rewriteRootHtml(html) {
  let out = injectRuntime(html);
  // Capacitor https://localhost serves www as root — keep root-relative / paths.
  // Only ensure runtime-config + native-bridge are present.
  if (!out.includes("viewport-fit=cover")) {
    out = out.replace(
      "width=device-width, initial-scale=1",
      "width=device-width, initial-scale=1, viewport-fit=cover"
    );
  }
  // PWA auto-redirect to app login is for installed browser PWA, not store app —
  // skip forcing #login when channel is native (handled in page script if any)
  out = out.replace(
    'location.replace("/app/?source=pwa#login");',
    'if (!(window.WAKEAGAIN_CHANNEL === "native" || (window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform()))) { location.replace("/app/?source=pwa#login"); }'
  );
  return out;
}

function walkHtml(dir, fn) {
  if (!fs.existsSync(dir)) return;
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name);
    const st = fs.statSync(p);
    if (st.isDirectory()) {
      if (name === "assets" || name === "node_modules") continue;
      walkHtml(p, fn);
    } else if (name.endsWith(".html")) {
      fn(p);
    }
  }
}

// --- run ---
if (!fs.existsSync(publicDir)) {
  console.error("public/ not found:", publicDir);
  process.exit(1);
}

rimraf(www);
copyDir(publicDir, www);

// API host for native builds (required for store / device)
const apiBase =
  process.env.WAKEAGAIN_API_BASE ||
  process.env.CAPACITOR_API_BASE ||
  "http://10.0.2.2:8080";

const jsDir = path.join(www, "js");
fs.mkdirSync(jsDir, { recursive: true });

const cfg = `/* generated by sync-www.js — do not edit */
window.WAKEAGAIN_API_BASE = ${JSON.stringify(apiBase)};
window.WAKEAGAIN_CHANNEL = "native";
window.WAKEAGAIN_APP_VERSION = ${JSON.stringify(
  require(path.join(mobileRoot, "package.json")).version || "0.1.0"
)};
`;
fs.writeFileSync(path.join(jsDir, "runtime-config.js"), cfg, "utf8");

const bridgeSrc = path.join(__dirname, "native-bridge.js");
if (fs.existsSync(bridgeSrc)) {
  fs.copyFileSync(bridgeSrc, path.join(jsDir, "native-bridge.js"));
} else {
  fs.writeFileSync(path.join(jsDir, "native-bridge.js"), "/* native-bridge missing */\n", "utf8");
}

// Rewrite every HTML: root pages keep site structure; app shell gets relative assets
walkHtml(www, function (filePath) {
  const rel = path.relative(www, filePath).replace(/\\/g, "/");
  let html = fs.readFileSync(filePath, "utf8");
  if (rel === "app/index.html" || rel.startsWith("app/")) {
    html = rewriteAppShell(html);
  } else {
    html = rewriteRootHtml(html);
  }
  fs.writeFileSync(filePath, html, "utf8");
});

// Entry is the real landing (homepage) — same as website.
// Users open 홈 = listings / manifesto; 로그인 → /app/#login
console.log("synced public → mobile/www (full site + app shell)");
console.log("entry: index.html (landing homepage)");
console.log("WAKEAGAIN_API_BASE =", apiBase);
if (!process.env.WAKEAGAIN_API_BASE && !process.env.CAPACITOR_API_BASE) {
  console.log("(tip) 스토어 빌드 전: set WAKEAGAIN_API_BASE=https://your-api.example");
}
