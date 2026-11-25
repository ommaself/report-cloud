"""합본 히트맵 발송 문구(11/25 대표: 텔레에 '화면 위 버튼으로 선택' 기재). 이모지 없음, ■ 제목."""
import re, sys
def d(p):
    m = re.search(r"기준 (\d{4}-\d{2}-\d{2}) 종가", open(p, encoding="utf-8").read())
    return m.group(1)[5:].replace("-", "/") if m else "?"
us, kr = sys.argv[1:3]
print(f"■ 시장 히트맵 (미국 {d(us)} · 국내 {d(kr)} 종가)\n━━━━━━━━━━━━\n파일을 열고 화면 위 [미국] [국내] 버튼으로 선택 · 칸을 누르면 차트")
