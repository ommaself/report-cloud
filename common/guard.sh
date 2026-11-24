#!/usr/bin/env bash
# 예약 누락 대비(11/25: 깃허브 예약이 늦거나 빠짐) — 같은 워크플로를 예비 시각에도 걸어두고,
# 최근 WINDOW분 안에 먼저 시작한 예약 실행이 있으면 이번 실행은 건너뜀(먼저 시작한 쪽 = 실행 번호가 작은 쪽만 일함).
# 사용: guard.sh <workflow 파일명> <분>   출력: GITHUB_OUTPUT go=1|0
set -euo pipefail
WF="$1"; WIN="${2:-150}"
if [ "${GITHUB_EVENT_NAME}" != "schedule" ]; then echo "go=1" >> "$GITHUB_OUTPUT"; echo "수동 실행 → 그대로 진행"; exit 0; fi
SINCE=$(date -u -d "-${WIN} minutes" +%Y-%m-%dT%H:%M:%SZ)
N=$(gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/${WF}/runs?event=schedule&created=%3E%3D${SINCE}&per_page=50" \
  --jq "[.workflow_runs[] | select(.id < ${GITHUB_RUN_ID}) | select(.conclusion != \"skipped\")] | length") || { echo "go=1" >> "$GITHUB_OUTPUT"; echo "실행 목록 조회 실패 → 빠뜨리지 않게 진행(중복 가능성은 감수)"; exit 0; }
if [ "$N" -gt 0 ]; then
  echo "go=0" >> "$GITHUB_OUTPUT"; echo "최근 ${WIN}분 안에 먼저 시작한 예약 실행 ${N}개 → 이번(예비) 실행은 건너뜀"
else
  echo "go=1" >> "$GITHUB_OUTPUT"; echo "먼저 시작한 예약 실행 없음 → 진행"
fi
