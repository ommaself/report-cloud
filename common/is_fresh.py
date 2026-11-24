"""휴장일 중복 발송 막기: 히트맵 기준일이 그 시장의 오늘 날짜면 'yes', 아니면 'no'(직전 종가 재발송 → 건너뜀)."""
import datetime as dt, re, sys
from zoneinfo import ZoneInfo
p, market = sys.argv[1], sys.argv[2]
m = re.search(r"기준 (\d{4}-\d{2}-\d{2}) 종가", open(p, encoding="utf-8").read())
tz = ZoneInfo("Asia/Seoul" if market == "KR" else "America/New_York")
print("yes" if m and m.group(1) == dt.datetime.now(tz).strftime("%Y-%m-%d") else "no")
