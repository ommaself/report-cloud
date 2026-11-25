#!/usr/bin/env bash
# 히트맵 발송(검사 포함). 사용: heatmap_send.sh <KR|US|both> <방 목록> <schedule|manual>
#  KR/US = 그 시장 파일 1개, both = 합본 out/heatmap.html 1개(11/25 대표 A안, 화면 위 [미국][국내] 버튼)
# 종료: 0 보냄/휴장 건너뜀, 1 [중단](알림 보냄)·발송 실패
set -uo pipefail
M="$1"; ROOMS="$2"; EV="$3"
MODE=""; [ "$EV" != schedule ] && MODE=manual
check() {  # $1 시장 $2 모드 → 출력 문구, 반환 0 정상 2 휴장 3 옛 자료
  python -I common/heatmap_check.py "out/heatmap_$1.html" "$1" $2
}
if [ "$M" = both ]; then
  MU=$(check US "$MODE"); RU=$?; MK=$(check KR "$MODE"); RK=$?; echo "$MU"; echo "$MK"
  if [ $RU -eq 2 ] && [ $RK -eq 2 ]; then echo "두 시장 모두 휴장 → 안 보냄"; exit 0; fi
  # 한쪽만 휴장이면 그쪽은 날짜만 다시 검사(휴장 건너뛰기 없이)
  [ $RU -eq 2 ] && { MU=$(check US manual); RU=$?; echo "$MU"; }
  [ $RK -eq 2 ] && { MK=$(check KR manual); RK=$?; echo "$MK"; }
  if [ $RU -ne 0 ] || [ $RK -ne 0 ]; then
    T=""; [ $RU -ne 0 ] && T="$MU"; [ $RK -ne 0 ] && T="${T:+$T
}$MK"
    python -I common/tg_alert.py "$T"; exit 1
  fi
  python -I common/combine.py out/heatmap_US.html out/heatmap_KR.html out/heatmap.html out/index.html || exit 1
  python -I common/tg_send.py --file out/heatmap.html --rooms "$ROOMS" --caption "$(python -I common/caption2.py out/heatmap_US.html out/heatmap_KR.html)"
  exit $?
fi
MSG=$(check "$M" "$MODE"); RC=$?; echo "$MSG"
[ $RC -eq 2 ] && exit 0
[ $RC -ne 0 ] && { python -I common/tg_alert.py "$MSG"; exit 1; }
T='국내 히트맵'; [ "$M" = US ] && T='S&P500 히트맵'
python -I common/tg_send.py --file "out/heatmap_$M.html" --rooms "$ROOMS" --caption "$(python -I common/caption.py "out/heatmap_$M.html" "$T")"
