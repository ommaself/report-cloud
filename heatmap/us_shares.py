r"""미장 주식 수(시총 = 주식 수 × 종가) 주 1회 갱신. 클라우드에선 야후 시총 조회가 막혀서 씀.

1) 처음(us_shares.json 없음): cache/us_caps_ref.json(PC가 받은 야후 시총, 기준일 t) ÷ 그날 야후 종가 → 종목별 주식 수
2) 매주: 미국 SEC 공시(companyfacts, dei:EntityCommonStockSharesOutstanding) 회사 전체 주식 수를 받아
   지난번 대비 변화율만큼 종목별 주식 수를 조정(같은 회사 여러 종류 주식 GOOGL·GOOG 등도 비율로 맞춤).
   변화율이 ±30% 밖이면(분할·자료 오류 의심) 그 종목은 안 바꾸고 로그만.
SEC 접속엔 연락처가 있는 User-Agent가 필요 → 환경변수 SEC_UA(깃허브 비밀값). 없으면 2) 건너뜀. 값은 어디에도 출력 안 함.
접속 주소: www.sec.gov(티커 목록)·data.sec.gov(공시 수치)·query2.finance.yahoo.com(처음 1회 종가). 그 밖 없음.
"""
import datetime as dt, json, os, sys, time
import requests

AV = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(AV, "cache")
OUT = os.path.join(C, "us_shares.json")
UA_Y = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def close_on(sym, day):
    t0 = int(dt.datetime.fromisoformat(day).timestamp()) - 6 * 86400
    r = requests.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}", headers={"User-Agent": UA_Y},
                     params={"period1": t0, "period2": t0 + 10 * 86400, "interval": "1d"}, timeout=20)
    res = r.json()["chart"]["result"][0]
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName", "America/New_York"))
    best = None
    for t, c in zip(res.get("timestamp") or [], res["indicators"]["quote"][0]["close"]):
        d = dt.datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d")
        if c and d <= day:
            best = c
    return best


def bootstrap():
    ref = json.load(open(os.path.join(C, "us_caps_ref.json"), encoding="utf-8"))["quotes"]
    sh, miss = {}, []
    for s, v in ref.items():
        try:
            c = close_on(s, v["t"])
        except Exception:
            c = None
        if c:
            sh[s] = round(v["cap"] / c)
        else:
            miss.append(s)
        time.sleep(0.1)
    return {"asof": min(v["t"] for v in ref.values()), "src": "야후 시총 ÷ 종가", "shares": sh, "sec": {}}, miss


def sec_totals(syms, ua):
    H = {"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}
    tick = requests.get("https://www.sec.gov/files/company_tickers.json", headers=H, timeout=30).json()
    cik = {v["ticker"].upper().replace(".", "-"): int(v["cik_str"]) for v in tick.values()}
    tot, ciks = {}, {}
    for s in syms:
        c = cik.get(s)
        if not c:
            continue
        ciks[s] = c
        if c in tot:
            continue
        try:
            f = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{c:010d}.json", headers=H, timeout=30).json()
            u = f["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"]
            last = max(x["end"] for x in u)
            accn = max((x for x in u if x["end"] == last), key=lambda x: x["filed"])["accn"]
            tot[c] = {"n": sum(x["val"] for x in u if x["end"] == last and x["accn"] == accn), "end": last}
        except Exception:
            pass
        time.sleep(0.15)  # SEC 초당 10회 제한 아래
    return ciks, tot


def main():
    log = []
    if os.path.exists(OUT):
        d = json.load(open(OUT, encoding="utf-8"))
    else:
        d, miss = bootstrap()
        log.append(f"처음 만들기 {len(d['shares'])}종목, 종가 못 받음 {len(miss)}: {miss[:10]}")
    ua = os.environ.get("SEC_UA", "").strip()
    if ua:
        ciks, tot = sec_totals(list(d["shares"]), ua)
        prev = d.get("sec", {})
        ch = skip = 0
        for s, c in ciks.items():
            k = str(c)
            if k not in {str(x) for x in tot}:
                continue
            new = tot[c]["n"]
            old = prev.get(k, {}).get("n")
            if old and new != old:
                r = new / old
                if 0.7 <= r <= 1.3:
                    d["shares"][s] = round(d["shares"][s] * r); ch += 1
                else:
                    skip += 1; log.append(f"{s} 변화율 {r:.2f} 건너뜀")
        d["sec"] = {str(c): v for c, v in tot.items()}
        d["asof"] = dt.date.today().isoformat(); d["src"] = "야후 기준 시총 + SEC 주식 수 변화"
        log.append(f"SEC {len(tot)}개 회사, 조정 {ch}종목, 건너뜀 {skip}")
    else:
        log.append("SEC_UA 없음 → SEC 건너뜀")
    json.dump(d, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("\n".join(log))


if __name__ == "__main__":
    main()
