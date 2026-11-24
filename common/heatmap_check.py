r"""히트맵 HTML 기준일 검사(예약 실행용). 기준일이 그 시장 '있어야 할 마지막 종가'와 같으면 ok(종료 0).
오늘이 그 시장 휴장일이면 'holiday'(종료 2, 발송 안 함·알림 안 함). 다르면 [중단] 경고 문구 출력(종료 3).
사용: python common/heatmap_check.py out/heatmap_KR.html KR [manual]
manual = 수동 실제 발송: 휴장일이어도 건너뛰지 않고 기준일만 검사(옛 자료면 [중단]).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fresh

p, m = sys.argv[1], sys.argv[2]
mm = re.search(r"기준 (\d{4}-\d{2}-\d{2}) 종가", open(p, encoding="utf-8").read())
got = mm.group(1) if mm else "?"
manual = len(sys.argv) > 3 and sys.argv[3] == "manual"
if not manual and not fresh.today_is_trading(m):
    print(f"오늘 {m} 휴장일 → 발송 안 함"); sys.exit(2)
e = fresh.expected(m).isoformat()
if got == e:
    print(f"기준일 {got} 정상"); sys.exit(0)
print(f"[중단] 히트맵 {m}: 기준일 {got} ≠ 직전 거래일 {e} → 발송 안 함"); sys.exit(3)
