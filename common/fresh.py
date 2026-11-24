r"""기준일 검사(11/25 대표 '절대 재발 금지' 원칙: 기준일이 직전 거래일이 아니면 발송 중단 + 내 방 [중단] 경고).

expected(market): 지금 시각 기준으로 '있어야 할 마지막 종가 날짜'.
  그 시장 현지 시각이 장 마감 뒤(KR 15:40·US 16:15)이고 오늘이 거래일이면 오늘, 아니면 직전 거래일.
  거래일 = 평일 + 공휴일 아님(KR: holidays.KR + 12/31 휴장, US: holidays.NYSE).
사용(명령줄): python common/fresh.py KR 2026-11-24  → 'ok' / 'stale 기대 2026-11-25' / 'holiday'(오늘이 휴장일)
"""
import datetime as dt, sys
from zoneinfo import ZoneInfo
import holidays

TZ = {"KR": ZoneInfo("Asia/Seoul"), "US": ZoneInfo("America/New_York")}
CLOSE = {"KR": dt.time(15, 40), "US": dt.time(16, 15)}


def is_trading(market, d):
    if d.weekday() >= 5:
        return False
    if market == "KR":
        return d not in holidays.KR(years=d.year) and (d.month, d.day) != (12, 31)
    return d not in holidays.NYSE(years=d.year)


def prev_trading(market, d):
    d -= dt.timedelta(days=1)
    while not is_trading(market, d):
        d -= dt.timedelta(days=1)
    return d


def expected(market, now=None):
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(TZ[market])
    d = now.date()
    if is_trading(market, d) and now.time() >= CLOSE[market]:
        return d
    return prev_trading(market, d)


def today_is_trading(market, now=None):
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(TZ[market])
    return is_trading(market, now.date())


if __name__ == "__main__":
    m, got = sys.argv[1], sys.argv[2]
    e = expected(m).isoformat()
    print("ok" if got == e else f"stale 기대 {e}")
