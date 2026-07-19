/** Fail store prep if API base is still emulator localhost. */
const base = process.env.WAKEAGAIN_API_BASE || process.env.CAPACITOR_API_BASE || "";
if (!base || !/^https:\/\//i.test(base)) {
  console.error("");
  console.error("스토어 빌드 전 HTTPS API 주소가 필요합니다:");
  console.error("  set WAKEAGAIN_API_BASE=https://your-api.example");
  console.error("  npm run build:store:prep");
  console.error("");
  process.exit(1);
}
if (/10\.0\.2\.2|127\.0\.0\.1|localhost/i.test(base)) {
  console.error("스토어 빌드에 로컬/에뮬레이터 API 주소를 쓸 수 없습니다:", base);
  process.exit(1);
}
console.log("OK production API:", base);
