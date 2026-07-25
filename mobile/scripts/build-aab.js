/**
 * One-shot store AAB:
 *  1) public → www (Capacitor sync)
 *  2) Gradle bundleRelease (signed if keystore present)
 *  3) Copy AAB to mobile/dist/ (stable path for Play upload)
 *
 * Usage (PowerShell):
 *   $env:WAKEAGAIN_API_BASE = "https://wakeagain.com"
 *   npm run build:aab
 */
const { execSync, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const mobileRoot = path.join(__dirname, "..");
const androidRoot = path.join(mobileRoot, "android");
const distDir = path.join(mobileRoot, "dist");
const gradleOut = path.join(
  androidRoot,
  "app",
  "build",
  "outputs",
  "bundle",
  "release",
  "app-release.aab"
);

function run(cmd, opts = {}) {
  console.log("\n>", cmd);
  execSync(cmd, {
    cwd: opts.cwd || mobileRoot,
    stdio: "inherit",
    env: { ...process.env, ...opts.env },
    shell: true,
  });
}

function findJavaHome() {
  if (process.env.JAVA_HOME && fs.existsSync(process.env.JAVA_HOME)) {
    return process.env.JAVA_HOME;
  }
  const studioJbr = "C:\\Program Files\\Android\\Android Studio\\jbr";
  if (fs.existsSync(studioJbr)) return studioJbr;
  return null;
}

function main() {
  const api =
    process.env.WAKEAGAIN_API_BASE ||
    process.env.CAPACITOR_API_BASE ||
    "https://wakeagain.com";
  if (!/^https:\/\//i.test(api) || /localhost|127\.0\.0\.1|10\.0\.2\.2/i.test(api)) {
    console.error("Set a production HTTPS API, e.g.");
    console.error('  $env:WAKEAGAIN_API_BASE = "https://wakeagain.com"');
    process.exit(1);
  }
  process.env.WAKEAGAIN_API_BASE = api;

  const javaHome = findJavaHome();
  if (javaHome) {
    process.env.JAVA_HOME = javaHome;
    process.env.Path = path.join(javaHome, "bin") + path.delimiter + process.env.Path;
    console.log("JAVA_HOME =", javaHome);
  }
  if (!process.env.ANDROID_HOME && process.env.LOCALAPPDATA) {
    const sdk = path.join(process.env.LOCALAPPDATA, "Android", "Sdk");
    if (fs.existsSync(sdk)) {
      process.env.ANDROID_HOME = sdk;
      process.env.ANDROID_SDK_ROOT = sdk;
      console.log("ANDROID_HOME =", sdk);
    }
  }

  console.log("API =", api);
  run("npm run build:store:prep");

  const gradlew =
    process.platform === "win32"
      ? path.join(androidRoot, "gradlew.bat")
      : path.join(androidRoot, "gradlew");
  if (!fs.existsSync(gradlew)) {
    console.error("gradlew not found:", gradlew);
    process.exit(1);
  }
  run(`"${gradlew}" bundleRelease --no-daemon`, { cwd: androidRoot });

  if (!fs.existsSync(gradleOut)) {
    console.error("AAB not found after build:", gradleOut);
    process.exit(1);
  }

  fs.mkdirSync(distDir, { recursive: true });
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  const versioned = path.join(distDir, `wakeagain-release-${stamp}.aab`);
  const stable = path.join(distDir, "wakeagain-release.aab");
  fs.copyFileSync(gradleOut, versioned);
  fs.copyFileSync(gradleOut, stable);

  const st = fs.statSync(stable);
  console.log("\n=== AAB ready ===");
  console.log("Stable:  ", stable);
  console.log("Versioned:", versioned);
  console.log("Size:    ", Math.round(st.size / 1024), "KB");
  console.log("\nPlay Console → 내부 테스트 → 새 버전 → 이 파일 업로드");
}

main();
