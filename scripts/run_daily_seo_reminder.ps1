$root = "C:\Users\hysoo\Projects\WakeAgain"
$prompt = Join-Path $root "docs\marketing\DAILY_SEO_PROMPT.md"
$logDir = Join-Path $root "docs\marketing\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$log = Join-Path $logDir "seo_trigger_$stamp.txt"
@"
WakeAgain Daily SEO Trigger
time: $(Get-Date -Format o)
prompt: $prompt
action: Run Grok with DAILY_SEO_PROMPT.md (or: 웨이크어게인 오늘 블로그 올려)
"@ | Set-Content -Path $log -Encoding UTF8
Write-Host "Logged -> $log"
