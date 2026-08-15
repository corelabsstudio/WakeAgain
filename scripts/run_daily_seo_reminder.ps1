# ⚠️ 폐기됨 (2026-08-15). 실행하지 말 것 — 아무 일도 하지 않는다.
#
# 이 스크립트는 로그 파일만 남기는 백업 알림이었고, 실제 SEO 발행은 하지 않았다.
# 원래 발행 주체였던 "Grok durable scheduler"는 폐기됐다.
#
# 현재 정본: Claude Code 클라우드 루틴 "WakeAgain Daily SEO" (매일 09:15 KST).
#   - 글 생성·커밋까지 클라우드 컨테이너 안에서 수행하고 GitHub에 push 한다.
#   - 이 로컬 PS1은 그 흐름에 전혀 관여하지 않는다.
#
# 이 스크립트를 돌리던 윈도우 작업 WakeAgain_Daily_SEO_Trigger / RoadLog_Daily_SEO_Trigger 는
# 폐기 대상이다. 정의 백업: docs/marketing/_deprecated_tasks_backup/*.xml
#
# ⚠️ 2026-08-15 시점 미해결 이슈 (이게 진짜 원인이었음):
#   클라우드 루틴의 GitHub App에 corelabsstudio/WakeAgain 에 대한 contents:write 권한이 없어
#   push 가 403(Resource not accessible by integration)으로 막혔다. 루틴 목록엔 "완료됨"으로
#   찍히지만 결과물은 컨테이너와 함께 사라진다. 실제로 docs/marketing/logs/*.md 리포트가
#   저장소에 들어온 적이 한 번도 없고, 블로그 글도 2026-08-11 이후 늘지 않았다.
#   → GitHub 조직 설정에서 Contents: Read and write 부여 필요 (사람이 해야 하는 작업).

Write-Host "이 스크립트는 폐기되었습니다. 아무 작업도 수행하지 않습니다."
Write-Host "SEO 발행은 Claude Code 클라우드 루틴 'WakeAgain Daily SEO'가 담당합니다."
exit 0
