# Backup log only. Primary: Grok durable scheduler (1d WakeAgain daily SEO).
$root = "C:\Users\hysoo\projects\WakeAgain"
if (-not (Test-Path "$root\docs\marketing\DAILY_SEO_PROMPT.md")) {
  $root = "C:\Users\hysoo\Projects\WakeAgain"
}
$prompt = Join-Path $root "docs\marketing\DAILY_SEO_PROMPT.md"
$logDir = Join-Path $root "docs\marketing\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$log = Join-Path $logDir "seo_trigger_$stamp.txt"
@"
WakeAgain Daily SEO Trigger (backup log only)
time: $(Get-Date -Format o)
prompt: $prompt
primary: Grok durable scheduler — daily SEO (not this PS1)
fallback: Open Grok and say: 웨이크어게인 오늘 블로그 올려
"@ | Set-Content -Path $log -Encoding UTF8
Write-Host "Logged backup -> $log"
