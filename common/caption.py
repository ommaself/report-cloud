"""히트맵 HTML에서 기준일·종목 수를 읽어 발송 문구 만들기(이모지 없음, ■ 제목)."""
import re, sys
p, title = sys.argv[1], sys.argv[2]
s = open(p, encoding="utf-8").read()
m = re.search(r"기준 (\d{4}-\d{2}-\d{2}) 종가 · (\d+)종목([^<\"]*)", s)
d, n, rest = (m.group(1), m.group(2), m.group(3)) if m else ("?", "?", "")
print(f"■ {title} ({d[5:].replace('-', '/')} 종가)\n━━━━━━━━━━\n{n}종목{rest} · 파일을 열면 칸을 눌러 차트 확인")
