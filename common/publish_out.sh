#!/usr/bin/env bash
# 실제로 보낸 히트맵을 비공개 브랜치(OUTB: main=out, 시험 브랜치=out-test)에 덮어씀 + build_시장.json (사이드 Artifact 연동, 11/25)
# 사용: publish_out.sh <KR|US|both> <방 목록>   환경: OUTB, GITHUB_RUN_ID, GITHUB_SHA
set -euo pipefail
M="$1"; ROOMS="$2"; [ "$M" = both ] && MS="KR US" || MS="$M"
git config user.name "report-cloud bot"; git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
rm -rf ../outb
if git fetch -q origin "$OUTB" 2>/dev/null; then
  git worktree add -q ../outb FETCH_HEAD
else
  git worktree add -q --detach ../outb
  (cd ../outb && git checkout -q --orphan "$OUTB" && git rm -rqf . >/dev/null 2>&1 || true)
fi
for m in $MS; do
  cp "out/heatmap_$m.html" "../outb/heatmap_$m.html"
  D=$(grep -oE "기준 [0-9]{4}-[0-9]{2}-[0-9]{2} 종가" "out/heatmap_$m.html" | head -1 | grep -oE "[0-9-]{10}" || echo "?")
  printf '{"market":"%s","run_id":"%s","commit":"%s","code_md5":"%s","asof":"%s","html_md5":"%s","rooms":"%s","built_utc":"%s"}\n' \
    "$m" "$GITHUB_RUN_ID" "$GITHUB_SHA" "$(md5sum heatmap/heatmap_web.py | cut -c1-32)" "$D" "$(md5sum "out/heatmap_$m.html" | cut -c1-32)" \
    "$ROOMS" "$(date -u +%FT%TZ)" > "../outb/build_$m.json"
done
if [ "$M" = both ] && [ -f out/heatmap.html ]; then  # 합본(텔레 발송 파일 = 사이드 게시 파일)
  cp out/heatmap.html ../outb/heatmap.html
  [ -f out/index.html ] && cp out/index.html ../outb/index.html  # 사이드용 껍데기(합본과 같은 버튼·문구)
  printf '{"file":"heatmap.html","run_id":"%s","commit":"%s","code_md5":"%s","html_md5":"%s","index_md5":"%s","rooms":"%s","built_utc":"%s"}\n' \
    "$GITHUB_RUN_ID" "$GITHUB_SHA" "$(md5sum heatmap/heatmap_web.py | cut -c1-32)" "$(md5sum out/heatmap.html | cut -c1-32)" "$(md5sum out/index.html 2>/dev/null | cut -c1-32)" "$ROOMS" "$(date -u +%FT%TZ)" > ../outb/build.json
fi
cd ../outb
git add -A
git commit -qm "히트맵 $MS run $GITHUB_RUN_ID"
git push -q origin "HEAD:refs/heads/$OUTB"
echo "out 저장: $OUTB ($MS)"
