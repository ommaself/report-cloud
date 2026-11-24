r"""클릭형 히트맵 HTML(새 파일, 독립 실행). 핀비즈 접속·캡처·스크래핑 없음. 발송 기능 없음.

그림(배치·색·섹터/산업 머리줄·한글명)은 heatmap.py의 squarify·color·SECTOR_KO·constituents·quotes를 이 파일에 그대로 복사해 PNG와 같게 만든다.
2026-11-24 ma1124g: 칸 포커스 링(outline) 끔 — 확대 상태에서 칸을 누르거나 끌면 큰 둥근 테가 뜨던 문제. Tab 이동 때만 흰 테두리(화면 기준 굵기). 아래 안내문에 [+]·[−]·키보드 추가. 화면 CSS·문구만 바꿈.
2026-11-24 ma1124f: 오른쪽 위 [−] [+] [원위치 N×] 버튼(한 번에 1.5배, 1~5배, 지금 화면 가운데 기준), 키보드 +/− 같음. 화면 JS·HTML만 바꿈.
2026-11-24 ma1124e: 확대하면 작은 칸에도 글자(종목명·등락률). 화면상 칸 크기가 1배 글자 규칙(0.42×0.28칸)을 넘으면 보임,
  글자 화면 크기 = max(1배 때 크기, 칸에 맞는 크기(최대 11px)) → 확대해도 그 이상 커지지 않음.
  섹터·산업 머리글 글자 = max(1배 크기, 띠 높이에 맞는 크기(최대 13·11px)), 테두리 굵기 = 화면에서 1배 때 그대로. 화면 JS만 바꿈.
2026-11-24 ma1124d: 지도 확대·이동(Ctrl+휠·드래그·핀치, 1~5배, 더블클릭·Esc·[원위치] = 1배).
  + 이평을 일·주·월 모두 같게(국장 5·20·60·120·240, 미장 5·20·50·100·200, 봉 단위). 100봉 이상 이평은 파이썬에서 미리 계산해 화면 구간 값만 실음(짧은 이평은 앞 59봉 이하로 화면 계산).
    월봉 장기 자료 = 야후 월봉 전체 기간(period1=0, range=max는 분기봉이라 안 씀. 일봉 12년보다 앞의 달만 씀). 화면 구간에 값이 하나도 없는 선은 범례에 '(자료 부족)'.
2026-11-24 ma1124c: heatmap.py를 불러오지 않음(그 파일의 국장 시세 함수가 robots 금지 주소를 부르기 때문, 11/24 점검).
종목 칸을 누르면(휴대폰은 탭) 팝업으로 캔들 + 이평 + 거래량 + 한글명·티커·등락률. 버튼 3개(2026-11-24 ma1124):
  [일봉 1년]·[주봉 3년]·[월봉 10년] 모두 국장 5·20·60·120·240 / 미장 5·20·50·100·200(봉 단위),
'TradingView에서 열기' 링크(tradingview.com/symbols/거래소-티커/, 링크만, 자동 접속 없음).
데이터: 미국 = 위키 S&P500 목록(cache\sp500_list.json, 7일 지나면 위키백과 재조회), 한국 = cache\kr_universe.json 목록 파일만 읽음
  (코드·이름·시장·업종·상장주식수만 씀. 그 파일 안의 종가·등락률 칸은 안 씀. 목록을 새로 만들지 않음).
  봉은 두 시장 모두 야후 v8 일봉 12년 치 한 번 받아서 주봉·월봉을 직접 묶음(주 = 월~금, 월 = 달력 월. 마지막 주·월은 진행 중인 봉).
  이평 앞부분용 종가(앞 봉)를 같이 실어 화면에서 계산. 상장이 짧으면 있는 만큼만 그리고 빠진 선을 작게 표시.
접속 주소: 야후(fc.yahoo.com·query1/query2.finance.yahoo.com), 목록이 오래됐을 때만 위키백과. 그 밖의 주소 호출 코드 없음.
일봉은 HTML 안에 넣어 오프라인으로 열림. 외부 스크립트·폰트 없음(순수 JS + 캔버스).
한글명: 환경변수 KJ_KO_NAMES(시험) 또는 cache\us_ko_names.json(운영).
사용: python heatmap_web.py --market US|KR --date 2026-11-20 --out 파일.html
"""
import argparse, datetime as dt, html, io, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

import requests

AV = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
# 2026-11-24 ma1124: 보이는 봉 수·이평(대표 11/24 확정: 국장 5·20·60·120·240, 미장 5·20·50·100·200, 주 10·20·40, 월 10·20)
BARS = {"D": 252, "W": 156, "M": 120}   # 일봉 1년·주봉 3년·월봉 10년
MAS = {"KR": [5, 20, 60, 120, 240], "US": [5, 20, 50, 100, 200]}  # 2026-11-24 ma1124d: 일·주·월 같은 숫자(봉 단위)
MO = {}  # 종목 → 야후 월봉(전체 기간)
LONGMA = 100  # 이 봉 수 이상 이평 = 파이썬 계산값을 실음
LONG = {"KR": [120, 240], "US": [100, 200]}  # 일봉 가격 줄 '장기선 위/아래'
YEARS = 12        # 야후 일봉 받는 기간(월봉 10년 + 20개월선 앞부분)
FILT = {"US": [50, 200], "KR": [60, 120]}  # 히트맵 위 토글: [전체] [N일선 위] … (마지막 종가 > 이평 = 위)
W, H = 32.0, 18.0  # heatmap.py render()와 같은 좌표계(1칸 = 72pt)
YX = {"NMS": "NASDAQ", "NGM": "NASDAQ", "NCM": "NASDAQ", "NAS": "NASDAQ", "NYQ": "NYSE", "PCX": "AMEX", "ASE": "AMEX", "BTS": "CBOE"}


# ───────────── heatmap.py에서 복사(2026-11-23 판, 수정 없이) ─────────────
def _mask(s):  # 예외 출력에 섞일 수 있는 비밀값 가림(텔레그램 봇 토큰 꼴·야후 crumb)
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", str(s))
    return re.sub(r"crumb=[^&\s'\"]+", "crumb=***", s)


def _excepthook(t, v, tb):
    import traceback
    sys.stderr.write(_mask("".join(traceback.format_exception(t, v, tb))))


sys.excepthook = _excepthook

ET = ZoneInfo("America/New_York")
CACHE = os.path.join(AV, "cache", "sp500_list.json")
WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SAT = 3.0
SECTOR_KO = {"Information Technology": "기술", "Communication Services": "커뮤니케이션", "Consumer Discretionary": "임의소비재",
             "Consumer Staples": "필수소비재", "Health Care": "헬스케어", "Financials": "금융", "Industrials": "산업재",
             "Energy": "에너지", "Materials": "소재", "Utilities": "유틸리티", "Real Estate": "부동산"}
stats = {"calls": 0}


def constituents():
    c = None
    try:
        c = json.load(open(CACHE, encoding="utf-8"))
        if (dt.date.today() - dt.date.fromisoformat(c["fetched"])).days <= 7:
            return c
    except Exception:
        pass
    import pandas as pd
    t = requests.get(WIKI, headers={"User-Agent": UA}, timeout=30).text; stats["calls"] += 1
    df = pd.read_html(io.StringIO(t), attrs={"id": "constituents"})[0]
    rows = [{"symbol": str(r["Symbol"]).replace(".", "-"), "name": r["Security"], "sector": r["GICS Sector"],
             "industry": r["GICS Sub-Industry"]} for _, r in df.iterrows()]
    c = {"source": WIKI, "fetched": str(dt.date.today()), "n": len(rows), "rows": rows}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(c, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return c


def quotes(symbols):
    s = requests.Session(); s.headers.update({"User-Agent": UA})
    try:
        s.get("https://fc.yahoo.com", timeout=15)
    except requests.RequestException:
        pass
    crumb = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=15).text.strip(); stats["calls"] += 2
    out = {}
    for i in range(0, len(symbols), 50):
        part = symbols[i:i + 50]
        for k in range(3):
            try:
                r = s.get("https://query1.finance.yahoo.com/v7/finance/quote",
                          params={"symbols": ",".join(part), "crumb": crumb,
                                  "fields": "marketCap,regularMarketChangePercent,regularMarketTime,regularMarketPrice"}, timeout=20)
                stats["calls"] += 1
                if r.status_code == 429:
                    time.sleep(5 * (k + 1)); continue
                for q in r.json()["quoteResponse"]["result"]:
                    if q.get("marketCap") and q.get("regularMarketChangePercent") is not None:
                        tt = dt.datetime.fromtimestamp(q.get("regularMarketTime", 0), ET)
                        out[q["symbol"]] = {"cap": q["marketCap"], "chg": q["regularMarketChangePercent"],
                                            "t": tt.strftime("%Y-%m-%d"), "tm": tt.strftime("%H:%M"), "state": q.get("marketState", "")}
                break
            except Exception:
                time.sleep(2)
        time.sleep(0.3)
    return out


# squarified treemap (Bruls et al.) — 외부 패키지 없이
def _worst(row, w):
    s = sum(row)
    return max(max(w * w * r / (s * s), (s * s) / (w * w * r)) for r in row)


def squarify(vals, x, y, w, h):
    """vals(내림차순 양수) → [(x,y,w,h)] 같은 순서."""
    tot = sum(vals)
    if tot <= 0:
        return [(x, y, 0, 0)] * len(vals)
    vals = [v * w * h / tot for v in vals]
    rects, i = [], 0
    while i < len(vals):
        short = min(w, h)
        row = [vals[i]]; j = i + 1
        while j < len(vals) and _worst(row + [vals[j]], short) <= _worst(row, short):
            row.append(vals[j]); j += 1
        s = sum(row)
        if w >= h:  # 왼쪽에 세로 줄
            cw = s / h; cy = y
            for r in row:
                rects.append((x, cy, cw, r / cw)); cy += r / cw
            x += cw; w -= cw
        else:
            ch = s / w; cx = x
            for r in row:
                rects.append((cx, y, r / ch, ch)); cx += r / ch
            y += ch; h -= ch
        i = j
    return rects


def color(chg):
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("kj", ["#1d4ed8", "#3b5b8c", "#414554", "#8c3b3b", "#d61f1f"])
    return cm((max(-SAT, min(SAT, chg)) + SAT) / (2 * SAT))


KR_LIST = os.path.join(AV, "cache", "kr_universe.json")  # 목록 파일(읽기만)
KR_BUCKETS = os.path.join(AV, "cache", "kr_buckets.json")  # 코드 → [묶음, 근거]


class HM:  # 아래 코드가 HM.이름 으로 부르던 것을 이 파일 안 함수로 연결
    _mask, color, squarify, constituents, quotes = staticmethod(_mask), staticmethod(color), staticmethod(squarify), staticmethod(constituents), staticmethod(quotes)
    SECTOR_KO, KR_LIST, KR_BUCKETS = SECTOR_KO, KR_LIST, KR_BUCKETS


mask = HM._mask


def hexcolor(chg):
    r, g, b, _ = HM.color(chg)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


# ───────────── 일봉 ─────────────
def us_hist(sym, S, asof):
    for k in range(4):
        try:
            r = S.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}", params={"period1": int(time.time() - YEARS * 365.25 * 86400), "period2": int(time.time()) + 86400, "interval": "1d"}, timeout=20)
            if r.status_code == 429:
                time.sleep(4 * (k + 1)); continue
            res = r.json()["chart"]["result"][0]
            tz = ZoneInfo(res["meta"].get("exchangeTimezoneName", "America/New_York"))
            q = res["indicators"]["quote"][0]
            rows = []
            meta = res["meta"]
            mt, mp = meta.get("regularMarketTime"), meta.get("regularMarketPrice")
            mday = dt.datetime.fromtimestamp(mt, tz).strftime("%Y-%m-%d") if mt else None
            ts = res.get("timestamp") or []
            for i, t in enumerate(ts):
                day = dt.datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d")
                # 2026-11-24 fix: 장 마감 뒤 마지막 봉 close가 아직 None이면 meta.regularMarketPrice로 채움(그 봉 날짜 = regularMarketTime 날짜일 때만)
                # cloud 1125: 새벽 실행이면 currentTradingPeriod가 이미 다음 날 장으로 넘어가 있음 → 마지막 체결 시각이 지금 장 시작보다 앞이어도 '끝난 봉'
                reg = meta.get("currentTradingPeriod", {}).get("regular", {})
                if (i == len(ts) - 1 and q["close"][i] is None and mp and day == mday
                        and (reg.get("end", 0) <= time.time() or (mt and mt < reg.get("start", 0)))):
                    q["close"][i] = mp
                    q["high"][i] = max(x for x in (q["high"][i], q["open"][i], mp) if x is not None)
                    q["low"][i] = min(x for x in (q["low"][i], q["open"][i], mp) if x is not None)
                if None in (q["open"][i], q["high"][i], q["low"][i], q["close"][i]):
                    continue
                rows.append((dt.datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d"), q["open"][i], q["high"][i], q["low"][i], q["close"][i],
                             q["volume"][i] or 0))
            end = res["meta"].get("currentTradingPeriod", {}).get("regular", {}).get("end")
            if rows and end and time.time() < end and rows[-1][0] == dt.datetime.now(tz).strftime("%Y-%m-%d"):
                rows = rows[:-1]  # 장 안 끝난 오늘 봉 제외
            if asof:
                rows = [x for x in rows if x[0] <= asof]
            return rows, YX.get(res["meta"].get("exchangeName"), "")
        except Exception:
            time.sleep(1.5)
    return None, ""


def mo_hist(sym, S, asof):
    """야후 월봉 전체 기간(긴 월봉 이평용). range=max는 분기봉으로 바뀌어 와서(11/24 확인) period1=0으로 받음. 같은 달 봉이 두 개면 마지막 것만. 실패하면 []."""
    for k in range(4):
        try:
            r = S.get(f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}", params={"period1": 0, "period2": int(time.time()) + 86400, "interval": "1mo"}, timeout=30)
            if r.status_code == 429:
                time.sleep(4 * (k + 1)); continue
            res = r.json()["chart"]["result"][0]
            tz = ZoneInfo(res["meta"].get("exchangeTimezoneName", "America/New_York"))
            q = res["indicators"]["quote"][0]
            out = {}
            for i, t in enumerate(res.get("timestamp") or []):
                if None in (q["open"][i], q["high"][i], q["low"][i], q["close"][i]):
                    continue
                m = dt.datetime.fromtimestamp(t, tz).strftime("%Y-%m")
                out[m] = (m, q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i] or 0)
            return [out[m] for m in sorted(out) if not asof or m <= asof[:7]]
        except Exception:
            time.sleep(1.5)
    return []


def both(sym, S, asof):
    h = us_hist(sym, S, asof)
    MO[sym] = mo_hist(sym, S, asof) if h[0] else []
    return h


def num(v, p=6):
    """유효숫자 p자리. 정수면 정수로(파일 크기)."""
    x = float(f"{v:.{p}g}")
    return int(x) if x.is_integer() else x


def agg(rows, kind):
    """일봉 → 주봉(W, ISO 주) / 월봉(M). 날짜 = 그 주 마지막 거래일 / 그 달(YYYY-MM)."""
    out, key0 = [], None
    for dd, o, h, l, c, v in rows:
        t = dt.date.fromisoformat(dd)
        key = t.isocalendar()[:2] if kind == "W" else (t.year, t.month)
        if key != key0:
            out.append([dd if kind == "W" else dd[:7], o, h, l, c, v]); key0 = key
        else:
            b = out[-1]
            b[0] = dd if kind == "W" else b[0]
            b[2], b[3], b[4], b[5] = max(b[2], h), min(b[3], l), c, b[5] + v
    return out


def above(rows, market):
    """토글용: 마지막 종가가 N일선보다 크면 1, 아니면 0, 봉이 모자라면 None."""
    c = [x[4] for x in rows]
    return [None if len(c) < n else int(c[-1] > sum(c[-n:]) / n) for n in FILT[market]]


def pack(rows, market, mo=None):
    """2026-11-24 ma1124d: 100봉 이상 긴 이평은 여기서 계산(전체 봉) → 화면 구간 값만 실음(m, 2차 차분).
    짧은 이평(100 미만)은 앞 봉 종가(p, 최대 59봉)를 실어 화면에서 계산(m 자리 = 0)."""
    res = {}
    for k in ("D", "W", "M"):
        r = rows if k == "D" else agg(rows, k)
        if k == "M" and mo and r:
            first = r[0][0]  # 일봉 첫 달(대개 중간부터라 불완전) → 그 달까지는 야후 월봉으로
            r = [list(x) for x in mo if x[0] <= first] + r[1:]
        mas = MAS[market]
        n, pre = BARS[k], max(p for p in mas if p < LONGMA) - 1
        vis, prev = r[-n:], r[-n - pre:-n] if len(r) > n else []
        e = enc(vis, prev, k)
        c = [x[4] for x in r]
        e["m"] = [mas_enc(c, p, len(vis), e["s"]) if p >= LONGMA else 0 for p in mas]
        res[k] = e
    return res


def mas_enc(c, p, nv, sc):
    """단순이평(전체 봉으로 계산) 중 마지막 nv개. [앞 빈칸 수, 첫 값(정수), 첫 차분, 2차 차분…], 하나도 없으면 None."""
    out, s0 = [], 0.0
    for i, v in enumerate(c):
        s0 += v
        if i >= p: s0 -= c[i - p]
        out.append(s0 / p if i >= p - 1 else None)
    out = out[-nv:]
    k = sum(1 for v in out if v is None)
    if k == len(out):
        return None
    q = [round(v * sc) for v in out[k:]]
    d1 = [b - a for a, b in zip(q, q[1:])]
    return [k, q[0]] + d1[:1] + [b - a for a, b in zip(d1, d1[1:])]


def enc(vis, prev, k):
    """2026-11-24 ma1124b 크기 줄이기(화면 JS dec()가 풂).
    s = 가격 배율(유효숫자 약 5자리가 정수가 되게), n = 앞 봉(이평 앞부분) 개수,
    c = 종가 정수 차분(앞 봉 포함, 첫 값은 그대로), o·h·l = 그 봉 종가 정수와의 차,
    d = 첫 날짜(YYMMDD, 월봉은 YYMM) + 날짜 간격(일, 월봉은 개월), v·e = 일봉만 거래량 앞 3자리와 10의 지수(주·월봉은 거래량 없음)."""
    allc = [x[4] for x in prev] + [x[4] for x in vis]
    mx = max(max(allc), max(x[2] for x in vis))
    sc = 10 ** max(0, 5 - (len(str(int(mx))) if mx >= 1 else 1))
    q = lambda v: round(v * sc)
    C = [q(v) for v in allc]
    cv = C[len(prev):]
    if k == "M":
        ym = [(int(x[0][:4]), int(x[0][5:7])) for x in vis]
        dd = [f"{ym[0][0] % 100:02d}{ym[0][1]:02d}"] + [(b[0] - a[0]) * 12 + b[1] - a[1] for a, b in zip(ym, ym[1:])]
    else:
        ds = [dt.date.fromisoformat(x[0]) for x in vis]
        dd = [ds[0].strftime("%y%m%d")] + [(b - a).days for a, b in zip(ds, ds[1:])]
    out = {"s": sc, "n": len(prev), "d": dd, "c": [C[0]] + [b - a for a, b in zip(C, C[1:])],
           "o": [q(x[1]) - c for x, c in zip(vis, cv)], "h": [q(x[2]) - c for x, c in zip(vis, cv)],
           "l": [q(x[3]) - c for x, c in zip(vis, cv)]}
    if k == "D":
        vm = max((x[5] for x in vis), default=0)
        e = max(0, len(str(int(vm))) - 3) if vm >= 1 else 0
        out["e"], out["v"] = e, [round(x[5] / 10 ** e) for x in vis]
    return out


def collect_us(asof):
    sp = HM.constituents()
    try:
        ko = json.load(open(os.environ.get("KJ_KO_NAMES") or os.path.join(AV, "cache", "us_ko_names.json"), encoding="utf-8"))["names"]
    except Exception:
        ko = {}
    syms = [r["symbol"] for r in sp["rows"]]
    try:
        q = HM.quotes(syms)  # 시총(칸 크기)
    except Exception:
        q = {}
    capnote = "야후"
    shares = {}
    if len(q) < len(syms) * 0.9:  # cloud 1125: 클라우드(데이터센터 IP)에선 야후 crumb·v7 시세가 막힘(429/401) → 주식 수(us_shares.json, 주 1회 갱신) × 종가
        sd = json.load(open(os.path.join(AV, "cache", "us_shares.json"), encoding="utf-8"))
        shares = sd["shares"]
        q = {k: {"cap": 0} for k in shares}
        capnote = f"주식 수({sd['src']}, {sd['asof']}) × 종가"
    S = requests.Session(); S.headers["User-Agent"] = UA
    with ThreadPoolExecutor(4) as ex:
        hs = list(ex.map(lambda s: both(s, S, asof), syms))
    items, fail = [], []
    for r, (h, exch) in zip(sp["rows"], hs):
        s = r["symbol"]
        if not h or len(h) < 2 or s not in q:
            fail.append(s); continue
        tv = s.replace("-", ".")
        cap = shares[s] * h[-1][4] if shares else q[s]["cap"]
        items.append({"s": s, "name": r["name"], "ko": ko.get(s, "") if ko.get(s) != s else "", "sec": r["sector"], "ind": r["industry"],
                      "cap": cap, "chg": round((h[-1][4] / h[-2][4] - 1) * 100, 2), "date": h[-1][0],
                      "tv": f"https://www.tradingview.com/symbols/{exch + '-' if exch else ''}{tv}/", "b": pack(h, "US", MO.get(s)), "f": above(h, "US")})
    return items, fail, {"title": "S&P500 히트맵", "src": f"구성: 위키백과 S&P500 목록({sp['fetched']}) · 봉: 야후 · 시총: {capnote}"}


def collect_kr(asof):
    import warnings
    warnings.filterwarnings("ignore")
    u = json.load(open(HM.KR_LIST, encoding="utf-8"))
    try:
        bk = json.load(open(HM.KR_BUCKETS, encoding="utf-8"))
    except Exception:
        bk = {}
    S = requests.Session(); S.headers["User-Agent"] = UA
    sfx = lambda r: r["code"] + (".KQ" if r.get("market") == "KOSDAQ" else ".KS")
    with ThreadPoolExecutor(4) as ex:
        hs = [x[0] for x in ex.map(lambda r: both(sfx(r), S, asof), u["rows"])]
    items, fail = [], []
    for r, h in zip(u["rows"], hs):
        if not h or len(h) < 2:
            fail.append(r["name"]); continue
        items.append({"s": r["code"], "name": r["name"], "ko": "", "sec": (bk.get(r["code"]) or ["기타"])[0],
                      "ind": (r.get("industry") or "기타")[:18], "cap": h[-1][4] * r["shares"],
                      "chg": round((h[-1][4] / h[-2][4] - 1) * 100, 2), "date": h[-1][0],
                      "tv": f"https://www.tradingview.com/symbols/KRX-{r['code']}/", "b": pack(h, "KR", MO.get(sfx(r))), "f": above(h, "KR")})
    return items, fail, {"title": "국내 히트맵", "src": f"구성: {u.get('method', '')} · 분류: 투자자 묶음 → KRX 업종 · 봉: 야후 · 국내 종가는 야후 기준(임시), 공식 종가와 다를 수 있음 · 증자 등 권리락 미반영"}


# ───────────── 배치(heatmap.render와 같은 계산) ─────────────
def layout(items, us):
    tree = {}
    for i, it in enumerate(items):
        tree.setdefault(it["sec"], {}).setdefault(it["ind"], []).append(i)
    cap = lambda ids: sum(items[i]["cap"] for i in ids)
    capsum = lambda inds: sum(cap(v) for v in inds.values())
    secs = sorted(tree.items(), key=lambda kv: -capsum(kv[1]))
    S, I, T = [], [], []
    for (sec, inds), (sx, sy, sw, sh) in zip(secs, HM.squarify([capsum(s[1]) for s in secs], 0, 0, W, H)):
        pad, top = 0.04, 0.32
        ilist = sorted(inds.items(), key=lambda kv: -cap(kv[1]))
        irect = HM.squarify([cap(i[1]) for i in ilist], sx + pad, sy + top, sw - 2 * pad, sh - top - pad)
        for (ind, ids), (ix, iy, iw, ih) in zip(ilist, irect):
            ids = sorted(ids, key=lambda i: -items[i]["cap"])
            hd = 0.2 if (iw > 1.0 and ih > 0.9) else 0
            if hd:
                lb = ind.upper() if us else ind; n = max(3, int((iw - 0.1) * 16))
                I.append([round(ix, 4), round(iy, 4), round(iw, 4), hd, lb if len(lb) <= n else lb[:n - 1] + "…"])
            for i, (x, y, w, h) in zip(ids, HM.squarify([items[i]["cap"] for i in ids], ix, iy + hd, iw, ih - hd)):
                it = items[i]
                lab = None
                if w > 0.42 and h > 0.28:  # heatmap.render와 같은 글자 규칙
                    fs = max(5, min(22, 7 * min(w, h * 1.8) ** 0.8))
                    first = it["s"] if us else it["name"]
                    lines = [first, f"{it['chg']:+.2f}%"]
                    if us and it["ko"] and w > 1.1 and h > 0.75:
                        lines.insert(1, it["ko"])
                    em = max(sum(1.0 if "가" <= ch <= "힣" else 0.62 for ch in ln) for ln in lines)
                    fs = min(fs, 0.88 * w * 72 / max(em, 1), 0.85 * h * 72 / (len(lines) * 1.1))
                    lab = [lines, round(fs / 72, 4)] if fs >= 4 else None
                T.append([round(x, 4), round(y, 4), round(w, 4), round(h, 4), hexcolor(it["chg"]), i, lab])
        S.append([round(sx, 4), round(sy, 4), round(sw, 4), round(sh, 4), f"{HM.SECTOR_KO.get(sec, sec)} ({sec})" if us else sec])
    return S, I, T


PAGE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>__TITLE__</title>
<style>
/* 한 화면 지도: PNG와 같은 어두운 바탕. 지도는 폭에 맞춰 늘고, 휴대폰은 확대 버튼으로 가로 스크롤 */
:root { --bg:#262931; --panel:#1b1d24; --line:#0b0c10; --fg:#e5e7eb; --muted:#9ca3af; --up:#d61f1f; --down:#1d4ed8;
        --font: "Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",system-ui,sans-serif;
        color-scheme: dark; }
html,body { margin:0; background:var(--bg); color:var(--fg); font-family:var(--font); }
header { display:flex; flex-wrap:wrap; gap:8px 16px; align-items:center; padding-block:10px;
         padding-left:max(12px, env(safe-area-inset-left,0px)); padding-right:max(12px, env(safe-area-inset-right,0px)); }
h1 { font-size:16px; margin:0; }
.meta { color:var(--muted); font-size:12px; }
.zoom { margin-left:auto; display:flex; gap:4px; }
.flt { display:flex; gap:4px; }
.flt button { background:var(--panel); color:var(--fg); border:1px solid #3a3f4b; border-radius:6px; padding:6px 10px; font:inherit; font-size:13px; cursor:pointer; }
.flt button[aria-pressed="true"] { border-color:var(--fg); background:#323642; }
.cnt { font-size:13px; font-variant-numeric:tabular-nums; }
.zoom button { background:var(--panel); color:var(--fg); border:1px solid #3a3f4b; border-radius:6px; padding:6px 10px; font:inherit; font-size:13px; cursor:pointer; }
.zoom button[aria-pressed="true"] { border-color:var(--fg); }
.zoom button:disabled { opacity:.4; cursor:default; }
#zi, #zo { min-width:34px; font-size:16px; line-height:1; }
#wrap { overflow:hidden; }
#map { display:block; width:100%; height:auto; touch-action:pan-y; user-select:none; -webkit-user-select:none; }
#map.zm { touch-action:none; cursor:grab; }
#map.dg { cursor:grabbing; }
#map .t { cursor:pointer; }
#map .t:hover rect { stroke:#fff; stroke-width:.03; }
#map .t, #map .t:focus, #map .t:focus-visible { outline:none; }  /* 2026-11-24 ma1124g: 브라우저 포커스 링이 확대 배율만큼 커져 큰 원으로 보이던 것 끔 */
#map .t:focus-visible rect { stroke:#fff; stroke-width:2px; vector-effect:non-scaling-stroke; }  /* 키보드(Tab) 이동 때만 흰 테두리, 화면 기준 굵기 */
footer { color:var(--muted); font-size:11px; padding-block:8px 16px; padding-left:max(12px, env(safe-area-inset-left,0px)); padding-right:max(12px, env(safe-area-inset-right,0px)); line-height:1.5; }
#pop[hidden] { display:none; }
#pop { position:fixed; inset:0; background:rgba(0,0,0,.55); display:flex; align-items:center; justify-content:center; z-index:9;
       padding:max(8px, env(safe-area-inset-top,0px)) max(8px, env(safe-area-inset-right,0px)) max(8px, env(safe-area-inset-bottom,0px)) max(8px, env(safe-area-inset-left,0px)); }
.card { background:var(--panel); border:1px solid #3a3f4b; border-radius:10px; width:min(760px, 100%); max-height:100%; overflow:auto; padding:12px 14px; box-sizing:border-box; }
.top { display:flex; align-items:baseline; gap:10px; flex-wrap:wrap; }
.top b { font-size:18px; }
.top .tk { color:var(--muted); font-size:13px; }
.top .chg { font-size:16px; font-variant-numeric:tabular-nums; }
.top .x { margin-left:auto; background:none; border:0; color:var(--fg); font-size:22px; line-height:1; cursor:pointer; padding:4px 8px; }
.sub { color:var(--muted); font-size:12px; margin:2px 0 8px; }
.trend { font-size:13px; margin:6px 0; line-height:1.5; }
canvas { width:100%; display:block; touch-action:pan-y; }
.legend { display:flex; gap:12px; flex-wrap:wrap; font-size:12px; color:var(--muted); margin-top:6px; }
.legend i { display:inline-block; width:14px; height:3px; vertical-align:middle; margin-right:4px; }
.tabs { display:flex; gap:6px; margin:0 0 6px; }
.tabs button { background:#262931; color:var(--fg); border:1px solid #3a3f4b; border-radius:6px; padding:5px 10px; font:inherit; font-size:13px; cursor:pointer; }
.tabs button[aria-pressed="true"] { border-color:var(--fg); background:#323642; }
.note { color:var(--muted); font-size:11px; margin:2px 0; }
.card a { color:#93c5fd; font-size:13px; }
</style></head><body>
<header><h1>__TITLE__</h1><span class="meta">__META__</span>
<div class="flt" role="group" aria-label="이평 위 종목만 보기">__FBTN__</div><span class="cnt" id="cnt"></span>
<div class="zoom" role="group" aria-label="지도 확대"><button id="zo" aria-label="축소" title="축소(키보드 −)">−</button><button id="zi" aria-label="확대" title="확대(키보드 +)">+</button><button id="zb" aria-pressed="true" title="1배로 돌아가기(더블클릭·Esc도 같음)">원위치 (1×)</button></div></header>
<div id="wrap"><svg id="map" viewBox="0 0 32 18" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="__TITLE__"></svg></div>
<footer>칸 = 시가총액, 색 = 전일 등락률(빨강 상승·파랑 하락, ±3% 포화). 종목 칸을 누르면 일봉 1년·주봉 3년·월봉 10년 차트가 열립니다. 위 버튼 = 마지막 종가가 그 이평보다 높은 종목만 밝게(나머지는 회색). 확대: [+]·[−] 버튼, 키보드 +/−, Ctrl+마우스 휠(폰은 두 손가락), 최대 5배 · 확대 뒤 끌어서 이동 · 더블클릭·Esc·[원위치] = 처음 크기. __SRC__ · 개인 학습용, 투자 권유 아님</footer>
<div id="pop" hidden><div class="card" role="dialog" aria-modal="true" aria-labelledby="pn">
<div class="top"><b id="pn"></b><span class="tk" id="pt"></span><span class="chg" id="pc"></span><button class="x" id="px" aria-label="닫기">×</button></div>
<div class="sub" id="ps"></div>
<div class="tabs" role="group" aria-label="봉 종류"><button data-k="D" aria-pressed="true">일봉 1년</button><button data-k="W" aria-pressed="false">주봉 3년</button><button data-k="M" aria-pressed="false">월봉 10년</button></div>
<canvas id="cv" width="720" height="400"></canvas>
<div class="legend" id="lg"></div>
<div class="note" id="nt"></div>
<div class="trend" id="pr"></div>
<a id="pl" href="#" target="_blank" rel="noopener noreferrer">TradingView에서 열기</a>
</div></div>
<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
"use strict";
var D = JSON.parse(document.getElementById("data").textContent);
var FILT = __FILT__, TILES = [], SECS = [], HDR = [], SR = [];
var CFG = __CFG__, COLS = ["#f59e0b","#22c55e","#e879f9","#38bdf8","#f8fafc"], mode = "D";
var NS = "http://www.w3.org/2000/svg", svg = document.getElementById("map");
function el(t, a, p){ var e = document.createElementNS(NS, t); for (var k in a) e.setAttribute(k, a[k]); (p||svg).appendChild(e); return e; }
D.T.forEach(function(t){
  var g = el("g", {"class":"t", tabindex:"0", "data-i":t[5]});
  var r = el("rect", {x:t[0], y:t[1], width:t[2], height:t[3], fill:t[4], stroke:"#262931", "stroke-width":"0.0056"}, g);
  var TT = {g:g, r:r, fill:t[4], i:t[5], cx:t[0]+t[2]/2, cy:t[1]+t[3]/2, x:t[0], y:t[1], w:t[2], h:t[3]};
  TILES.push(TT);
  var cp = el("clipPath", {id:"c"+t[5]}, g); el("rect", {x:t[0], y:t[1], width:t[2], height:t[3]}, cp);
  var it = D.items[t[5]];
  var lines = t[6] ? t[6][0] : [it.s.match(/^\d{6}$/) ? it.name : it.s, (it.chg >= 0 ? "+" : "") + it.chg.toFixed(2) + "%"];
  var fs = t[6] ? t[6][1] : 0.1, lh = fs*1.05, y0 = t[1] + t[3]/2 - (lines.length-1)*lh/2;
  var tx = el("text", {x:t[0]+t[2]/2, "font-size":fs, fill:"#fff", "text-anchor":"middle", "dominant-baseline":"central", "clip-path":"url(#c"+t[5]+")", "pointer-events":"none"}, g);
  TT.ts = lines.map(function(s, k){ var ts = el("tspan", {x:t[0]+t[2]/2, y:y0 + k*lh}, tx); ts.textContent = s; return ts; });
  TT.tx = tx; TT.lines = lines; TT.py = t[6] ? fs : 0;  // py = 1배 글자 크기(칸 단위), 0 = 확대 때만 보이는 새 글자
  if (!t[6]) tx.style.display = "none";
});
D.I.forEach(function(i){
  el("rect", {x:i[0], y:i[1], width:i[2], height:i[3], fill:"#1b1d24", "pointer-events":"none"});
  var cp = el("clipPath", {id:"i"+i[0]+"_"+i[1]}); el("rect", {x:i[0], y:i[1], width:i[2], height:i[3]}, cp);
  var tx = el("text", {x:i[0]+0.05, y:i[1]+i[3]/2, "font-size":7/72, fill:"#cbd5e1", "dominant-baseline":"central", "clip-path":"url(#i"+i[0]+"_"+i[1]+")", "pointer-events":"none"}); tx.textContent = i[4];
  HDR.push({e:tx, fs:7/72, band:i[3], cap:11});
});
D.S.forEach(function(s){
  SR.push(el("rect", {x:s[0], y:s[1], width:s[2], height:s[3], fill:"none", stroke:"#0b0c10", "stroke-width":"0.042", "pointer-events":"none"}));
  var tx = el("text", {x:s[0]+0.08, y:s[1]+0.04, "font-size":(s[2]>3?11:8)/72, fill:"#e5e7eb", "font-weight":"bold", "dominant-baseline":"hanging", "pointer-events":"none"}); tx.textContent = s[4];
  HDR.push({e:tx, fs:(s[2]>3?11:8)/72, band:0.28, cap:13});
  var tr = el("tspan", {"font-weight":"normal", fill:"#cbd5e1"}, tx); SECS.push({s:s, t:tr});
});
// 토글: 조건 밖 종목은 회색·투명도 25%(지우지 않음, 배치 그대로). 섹터 제목 옆에 섹터별 '위' 비율
function filt(k){
  document.querySelectorAll(".flt button").forEach(function(x){ x.setAttribute("aria-pressed", Number(x.dataset.f)===k ? "true" : "false"); });
  var on = 0;
  TILES.forEach(function(t){ var ok = k<0 || D.items[t.i].f[k]===1; if (ok) on++;
    t.r.setAttribute("fill", ok ? t.fill : "#6b7280"); t.g.style.opacity = ok ? "" : "0.25"; });
  var N = TILES.length;
  document.getElementById("cnt").textContent = k<0 ? "" : on + "/" + N + " (" + Math.round(on/N*100) + "%)";
  SECS.forEach(function(q){ var s = q.s, a = 0, m = 0;
    if (k>=0) TILES.forEach(function(t){ if (t.cx>=s[0] && t.cx<=s[0]+s[2] && t.cy>=s[1] && t.cy<=s[1]+s[3]){ m++; if (D.items[t.i].f[k]===1) a++; } });
    q.t.textContent = (k<0 || !m) ? "" : "  " + a + "/" + m + " (" + Math.round(a/m*100) + "%)"; });
}
document.querySelectorAll(".flt button").forEach(function(b){ b.addEventListener("click", function(){ filt(Number(b.dataset.f)); }); });
// 2026-11-24 ma1124d 확대·이동: viewBox만 바꿈(벡터 그대로라 확대해도 글자·테두리 선명)
var VW = 32, VH = 18, MAXZ = 5, V = {x:0, y:0, z:1}, zb = document.getElementById("zb");
function vapply(){
  var w = VW/V.z, h = VH/V.z;
  V.x = Math.max(0, Math.min(VW - w, V.x)); V.y = Math.max(0, Math.min(VH - h, V.y));  // 지도 밖으로 못 나감
  svg.setAttribute("viewBox", V.x + " " + V.y + " " + w + " " + h);
  svg.classList.toggle("zm", V.z > 1.001);
  zb.textContent = "원위치 (" + (Math.round(V.z*10)/10) + "×)";
  zb.setAttribute("aria-pressed", V.z > 1.001 ? "false" : "true");
  if (zi){ zi.disabled = V.z >= MAXZ - 0.001; zo.disabled = V.z <= 1.001; }
  relabelSoon();
}
function zoomAt(z, fx, fy){  // fx·fy = 화면 안 위치(0~1), 그 점이 손가락·마우스 밑에 그대로 남게
  z = Math.max(1, Math.min(MAXZ, z));
  var mx = V.x + fx*VW/V.z, my = V.y + fy*VH/V.z;
  V.z = z; V.x = mx - fx*VW/z; V.y = my - fy*VH/z; vapply();
}
function vreset(){ V.x = 0; V.y = 0; V.z = 1; vapply(); }
// 2026-11-24 ma1124e: 글자를 화면 크기 기준으로 다시 맞춤(확대해도 글자 크기 그대로, 칸이 커지면 새 글자 보임)
var FSMAX = 11, FSMIN = 8, rlq = false;
function emw(t){ var e = 0; for (var k=0;k<t.length;k++){ var c = t.charCodeAt(k); e += (c >= 0xAC00 && c <= 0xD7A3) ? 1 : 0.62; } return e; }
function setLines(T, lines, fsU){
  var lh = fsU*1.05, y0 = T.y + T.h/2 - (lines.length-1)*lh/2;
  T.tx.setAttribute("font-size", fsU);
  T.ts.forEach(function(ts, k){ if (k < lines.length){ ts.style.display = ""; ts.setAttribute("y", y0 + k*lh); if (ts.textContent !== lines[k]) ts.textContent = lines[k]; } else ts.style.display = "none"; });
}
function relabel(){
  rlq = false;
  var W1 = svg.getBoundingClientRect().width; if (!W1) return;
  var U1 = W1/VW, U = U1*V.z;
  HDR.forEach(function(h){ h.e.setAttribute("font-size", Math.max(h.fs*U1, Math.min(h.cap, h.band*U*0.6))/U); });  // 머리글: 1배 크기 이상, 띠 높이에 맞춰 최대 11·13px
  SR.forEach(function(r){ r.setAttribute("stroke-width", 0.042/V.z); });
  var U1 = W1/VW, U = U1*V.z;  // U1 = 1배 때 1칸의 픽셀, U = 지금 1칸의 픽셀
  TILES.forEach(function(T){
    var wp = T.w*U, hp = T.h*U, show = null, f = 0;
    T.r.setAttribute("stroke-width", 0.0056/V.z);  // 테두리 굵기 화면에서 그대로
    if (T.py){  // 기존 글자: 1배 때 화면 크기 이상, 칸이 커지면 최대 11px까지
      var em0 = Math.max.apply(null, T.lines.map(emw));
      var fit = Math.min(FSMAX, 0.88*wp/Math.max(em0,1), 0.85*hp/(T.lines.length*1.1));
      setLines(T, T.lines, Math.max(T.py*U1, fit)/U); return;
    }
    if (wp > 0.42*U1 && hp > 0.28*U1){  // 1배 글자 규칙과 같은 기준(칸 단위 → 1배 픽셀)
      [T.lines, T.lines.slice(0,1)].some(function(ln){
        var em = Math.max.apply(null, ln.map(emw));
        f = Math.min(FSMAX, 0.88*wp/Math.max(em,1), 0.85*hp/(ln.length*1.1));
        if (f >= FSMIN){ show = ln; return true; } return false; });
      if (!show && hp*0.85/1.1 >= FSMIN){  // 이름이 길면 '…'로 줄임(최소 2글자)
        var room = 0.88*wp/FSMIN, nm = "", e = 0, full = T.lines[0];
        for (var k=0;k<full.length;k++){ var c = emw(full[k]); if (e + c + 1 > room) break; nm += full[k]; e += c; }
        if (nm.length >= 2){ show = 0.85*hp/(2*1.1) >= FSMIN ? [nm + "…", T.lines[1]] : [nm + "…"]; f = FSMIN; }
      }
    }
    if (!show){ T.tx.style.display = "none"; return; }
    T.tx.style.display = ""; setLines(T, show, f/U);
  });
}
function relabelSoon(){ if (!rlq){ rlq = true; requestAnimationFrame(relabel); } }
window.addEventListener("resize", relabelSoon);
function frac(cx, cy){ var r = svg.getBoundingClientRect(); return [(cx - r.left)/r.width, (cy - r.top)/r.height]; }
svg.addEventListener("wheel", function(e){  // Ctrl 없는 휠 = 페이지 스크롤 그대로
  if (!e.ctrlKey) return;
  e.preventDefault(); var f = frac(e.clientX, e.clientY); zoomAt(V.z*Math.exp(-e.deltaY*0.002), f[0], f[1]);
}, {passive:false});
var PT = {}, drag = null, moved = false, pinch = null;
svg.addEventListener("pointerdown", function(e){
  PT[e.pointerId] = {x:e.clientX, y:e.clientY};
  var ids = Object.keys(PT);
  if (ids.length === 1){ drag = {x:e.clientX, y:e.clientY, vx:V.x, vy:V.y, id:e.pointerId}; moved = false; }
  else if (ids.length === 2){ var a = PT[ids[0]], b = PT[ids[1]]; pinch = {d:Math.hypot(a.x - b.x, a.y - b.y), z:V.z}; drag = null; moved = true; }
});
svg.addEventListener("pointermove", function(e){
  if (!PT[e.pointerId]) return;
  PT[e.pointerId] = {x:e.clientX, y:e.clientY};
  var ids = Object.keys(PT);
  if (pinch && ids.length === 2){
    var a = PT[ids[0]], b = PT[ids[1]], f = frac((a.x + b.x)/2, (a.y + b.y)/2);
    zoomAt(pinch.z*Math.hypot(a.x - b.x, a.y - b.y)/Math.max(1, pinch.d), f[0], f[1]); return;
  }
  if (!drag || drag.id !== e.pointerId) return;
  var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (!moved && Math.hypot(dx, dy) > 5){ moved = true; try { svg.setPointerCapture(e.pointerId); } catch(_){} }  // 5px 넘으면 드래그
  if (moved && V.z > 1.001){
    var r = svg.getBoundingClientRect(); svg.classList.add("dg");
    V.x = drag.vx - dx/r.width*VW/V.z; V.y = drag.vy - dy/r.height*VH/V.z; vapply();
  }
});
function pend(e){ delete PT[e.pointerId]; if (Object.keys(PT).length < 2) pinch = null; if (!Object.keys(PT).length){ drag = null; svg.classList.remove("dg"); } }
svg.addEventListener("pointerup", pend); svg.addEventListener("pointercancel", pend);
svg.addEventListener("dblclick", function(e){ e.preventDefault(); clearTimeout(ctm); vreset(); });
zb.addEventListener("click", vreset);
// 2026-11-24 ma1124f: [+]·[−] 버튼과 키보드 +/−, 한 번에 1.5배, 지금 화면 가운데 기준
var ZSTEP = 1.5, zi = document.getElementById("zi"), zo = document.getElementById("zo");
function zstep(k){ zoomAt(V.z*Math.pow(ZSTEP, k), 0.5, 0.5); }
zo.disabled = V.z <= 1.001; zi.disabled = V.z >= MAXZ - 0.001;
zi.addEventListener("click", function(){ zstep(1); });
zo.addEventListener("click", function(){ zstep(-1); });
document.addEventListener("keydown", function(e){
  if (e.ctrlKey || e.metaKey || e.altKey || !pop.hidden) return;  // Ctrl+± = 브라우저 확대 그대로, 팝업 열려 있으면 무시
  var t = e.target && e.target.tagName; if (t === "INPUT" || t === "TEXTAREA") return;
  if (e.key === "+" || e.key === "=" || e.code === "NumpadAdd"){ e.preventDefault(); zstep(1); }
  else if (e.key === "-" || e.key === "_" || e.code === "NumpadSubtract"){ e.preventDefault(); zstep(-1); }
});
var ctm = null;
relabel();
function sma(c, n){ var o=[], s=0; for (var i=0;i<c.length;i++){ s+=c[i]; if(i>=n) s-=c[i-n]; o.push(i>=n-1 ? s/n : null);} return o; }
function pad(x){ return (x<10 ? "0" : "") + x; }
function dec(e, k){
  var sc = e.s, CI = [], a = 0, i;
  for (i=0;i<e.c.length;i++){ a = i ? a + e.c[i] : e.c[0]; CI.push(a); }
  var n0 = e.n, cv = CI.slice(n0), dd = [];
  if (k==="M"){ var y = 2000 + Number(e.d[0].slice(0,2)), m = Number(e.d[0].slice(2,4));
    for (i=0;i<cv.length;i++){ if (i){ m += e.d[i]; while (m>12){ m -= 12; y++; } } dd.push(pad(y%100) + pad(m)); } }
  else { var t = Date.UTC(2000 + Number(e.d[0].slice(0,2)), Number(e.d[0].slice(2,4)) - 1, Number(e.d[0].slice(4,6)));
    for (i=0;i<cv.length;i++){ if (i) t += e.d[i]*864e5; var D = new Date(t); dd.push(pad(D.getUTCFullYear()%100) + pad(D.getUTCMonth()+1) + pad(D.getUTCDate())); } }
  var f = function(arr){ return arr.map(function(x,j){ return (cv[j] + x)/sc; }); };
  var mm = (e.m || []).map(function(a){ if (a===0) return 0; if (!a) return null;  // 0 = 화면 계산, null = 자료 부족
    var o = [], v = a[1], dl = 0, j; for (j=0;j<a[0];j++) o.push(null); o.push(v/sc);
    for (j=2;j<a.length;j++){ dl = j===2 ? a[2] : dl + a[j]; v += dl; o.push(v/sc); } return o; });
  return {d:dd, m:mm, p:CI.slice(0,n0).map(function(x){ return x/sc; }), c:cv.map(function(x){ return x/sc; }), o:f(e.o), h:f(e.h), l:f(e.l),
          v: e.v ? e.v.map(function(x){ return x*Math.pow(10, e.e); }) : null};
}
function fmt(v){ return v>=1000 ? v.toLocaleString("ko-KR",{maximumFractionDigits:0}) : v.toLocaleString("ko-KR",{maximumFractionDigits:2}); }
var pop = document.getElementById("pop"), cur = null;
function open(i){
  var it = D.items[i]; cur = it;
  document.getElementById("pn").textContent = it.ko || it.name;
  document.getElementById("pt").textContent = it.ko ? it.s + " · " + it.name : it.s;
  var pc = document.getElementById("pc"); pc.textContent = (it.chg>0?"+":"") + it.chg.toFixed(2) + "%"; pc.style.color = it.chg>=0 ? "var(--up)" : "var(--down)";
  document.getElementById("ps").textContent = it.date + " 종가 · " + it.ind;
  document.getElementById("pl").href = it.tv;
  setMode("D"); pop.hidden = false; document.getElementById("px").focus();
}
function close(){ pop.hidden = true; cur = null; }
svg.addEventListener("click", function(e){
  if (moved){ moved = false; return; }  // 드래그·핀치 뒤 클릭 = 팝업 안 엶
  var g = e.target.closest && e.target.closest(".t"); if (!g) return;
  clearTimeout(ctm); if (e.detail > 1) return;
  ctm = setTimeout(function(){ open(Number(g.dataset.i)); }, 230);
});
svg.addEventListener("keydown", function(e){ if (e.key==="Enter"||e.key===" "){ var g = e.target.closest(".t"); if (g){ e.preventDefault(); open(Number(g.dataset.i)); } } });
document.getElementById("px").addEventListener("click", close);
pop.addEventListener("click", function(e){ if (e.target===pop) close(); });
document.addEventListener("keydown", function(e){ if (e.key==="Escape"){ if (!pop.hidden) close(); else vreset(); } });
window.addEventListener("resize", function(){ if (cur) draw(); });
function setMode(k){ mode = k; document.querySelectorAll(".tabs button").forEach(function(x){ x.setAttribute("aria-pressed", x.dataset.k===k ? "true" : "false"); }); draw(); }
document.querySelectorAll(".tabs button").forEach(function(bt){ bt.addEventListener("click", function(){ setMode(bt.dataset.k); }); });
function draw(){
  cur.z = cur.z || {}; var b = cur.z[mode] || (cur.z[mode] = dec(cur.b[mode], mode)), cf = CFG[mode], n = b.c.length, k0 = 0, u = cf.unit;
  var all = b.p.concat(b.c), off = b.p.length;  // 2026-11-24 ma1124d: 긴 이평 = 파이썬 계산값(b.m), 짧은 이평 = 화면 계산
  var M = cf.mas.map(function(p,j){ var a = b.m ? b.m[j] : 0; if (a===0) return sma(all, p).slice(off); return a || b.c.map(function(){ return null; }); });
  var lg = cf.mas.map(function(p,j){ var none = M[j].every(function(v){ return v==null; });
    return '<span><i style="background:' + COLS[j] + '"></i>' + p + u + '선' + (none ? '(자료 부족)' : '') + '</span>'; }).join("") + (b.v ? "<span>아래 막대 = 거래량</span>" : "");
  document.getElementById("lg").innerHTML = lg;
  var cv = document.getElementById("cv"), dpr = window.devicePixelRatio || 1, cw = cv.clientWidth || 700, ch = Math.round(Math.min(420, Math.max(260, cw*0.56)));
  cv.width = cw*dpr; cv.height = ch*dpr; cv.style.height = ch + "px";
  var x = cv.getContext("2d"); x.setTransform(dpr,0,0,dpr,0,0); x.clearRect(0,0,cw,ch);
  var L = 6, R = 54, T = 8, VH = b.v ? Math.round(ch*0.2) : 0, PH = ch - T - VH - 26, cnt = n - k0, bw = (cw-L-R)/cnt;
  var hi = -Infinity, lo = Infinity, vmax = 0;
  for (var i=k0;i<n;i++){ hi=Math.max(hi,b.h[i]); lo=Math.min(lo,b.l[i]); M.forEach(function(a){ var v=a[i]; if(v!=null){hi=Math.max(hi,v);lo=Math.min(lo,v);} }); if (b.v) vmax=Math.max(vmax,b.v[i]); }
  var pad=(hi-lo)*0.04||1; hi+=pad; lo-=pad;
  var Y = function(v){ return T + (hi-v)/(hi-lo)*PH; }, X = function(i){ return L + (i-k0+0.5)*bw; };
  x.font = "11px " + getComputedStyle(document.body).fontFamily; x.fillStyle = "#9ca3af"; x.strokeStyle = "rgba(255,255,255,.07)"; x.lineWidth = 1;
  for (var g=0; g<=4; g++){ var v = lo + (hi-lo)*g/4, yy = Math.round(Y(v))+.5; x.beginPath(); x.moveTo(L,yy); x.lineTo(cw-R,yy); x.stroke(); x.fillText(fmt(v), cw-R+4, yy+4); }
  // 아래 눈금: 일봉 = 달, 주봉 = 반년(1월·7월), 월봉 = 해
  var key = function(d){ var yy = d.slice(0,2), mm = Number(d.slice(2,4)); return mode==="D" ? d.slice(2,4) : (mode==="W" ? yy + (mm<=6 ? "a" : "b") : yy); };
  var lab = function(d){ var yy = d.slice(0,2), mm = Number(d.slice(2,4)); return mode==="D" ? mm + "월" : (mode==="W" ? (mm<=6 ? "'" + yy : "7월") : "'" + yy); };
  var last = ""; x.textAlign = "center";
  for (var i=k0;i<n;i++){ var kk = key(b.d[i]); if (kk!==last){ if (last) { x.fillText(lab(b.d[i]), X(i), ch-6); x.beginPath(); x.moveTo(Math.round(X(i))+.5,T); x.lineTo(Math.round(X(i))+.5,T+PH+VH+4); x.stroke(); } last = kk; } }
  x.textAlign = "left";
  for (var i=k0;i<n;i++){
    var up = b.c[i] >= b.o[i], col = up ? "#d61f1f" : "#3b82f6", cx = X(i);
    x.strokeStyle = col; x.fillStyle = col; x.beginPath(); x.moveTo(cx, Y(b.h[i])); x.lineTo(cx, Y(b.l[i])); x.stroke();
    var y1 = Y(Math.max(b.o[i],b.c[i])), y2 = Y(Math.min(b.o[i],b.c[i])); x.fillRect(cx-Math.max(1,bw*0.35), y1, Math.max(2,bw*0.7), Math.max(1,y2-y1));
    var vh = (b.v && vmax) ? b.v[i]/vmax*VH : 0; x.globalAlpha = .55; x.fillRect(cx-Math.max(1,bw*0.35), T+PH+VH+4-vh, Math.max(2,bw*0.7), vh); x.globalAlpha = 1;
  }
  M.forEach(function(a,j){
    x.strokeStyle = COLS[j]; x.lineWidth = 1.5; x.beginPath(); var st = false;
    for (var i=k0;i<n;i++){ var v = a[i]; if (v==null) continue; if (!st){ x.moveTo(X(i),Y(v)); st = true; } else x.lineTo(X(i),Y(v)); }
    x.stroke();
  });
  x.lineWidth = 1;
  // 상장 기간이 짧아 모자란 부분 표시
  var notes = [];
  if (all.length < cf.bars) notes.push("자료 " + n + "봉뿐(자료 기간이 짧아 있는 만큼만 그림)");
  cf.mas.forEach(function(p,j){ var miss = M[j].filter(function(v){ return v==null; }).length;
    if (miss>0 && miss<n) notes.push(p + u + "선 앞부분 " + miss + "봉 없음(자료 기간 짧음)"); });
  document.getElementById("nt").textContent = notes.join(" · ");
  var c = b.c[n-1], s = function(m){ return m[n-1]==null ? "계산 불가" : (c>=m[n-1] ? "위" : "아래") + " (" + ((c/m[n-1]-1)*100).toFixed(1) + "%)"; };
  var ch1 = function(k){ return n>k ? ((c/b.c[n-1-k]-1)*100).toFixed(1) : (all.length>k ? ((c/all[all.length-1-k]-1)*100).toFixed(1) : "-"); };
  var q = cf.mas.slice(0,3).map(function(p,j){ return M[j][n-1]; }), qs = cf.mas.slice(0,3);
  var order = q.every(function(v){ return v!=null; }) ? (q.every(function(v,j){ return j===0 || q[j-1]>v; }) ? "정배열(" + qs.join(">") + ")" : (q.every(function(v,j){ return j===0 || q[j-1]<v; }) ? "역배열(" + qs.join("<") + ")" : "섞임")) : "계산 불가";
  var txt = "종가 " + fmt(c) + " · " + cf.mas.map(function(p,j){ return p + u + "선 " + s(M[j]); }).join(" · ") + " · 이평 " + order;
  if (cf.long) txt += " · 장기선 " + cf.long.map(function(p){ var m = M[cf.mas.indexOf(p)]; return p + u + "선 " + (m[n-1]==null ? "계산 불가" : (c>=m[n-1] ? "위" : "아래")); }).join("·");
  txt += " · " + cf.chg.map(function(k){ return k[1] + " " + ch1(k[0]) + "%"; }).join(" · ");
  document.getElementById("pr").textContent = txt;
}
})();
</script></body></html>
"""


def build(market, asof, out):
    t0 = time.time()
    items, fail, info = collect_us(asof) if market == "US" else collect_kr(asof)
    S, I, T = layout(items, market == "US")
    days = [x["date"] for x in items]
    d0 = max(set(days), key=days.count) if days else "?"
    mixed = sum(1 for x in days if x != d0)
    meta = f"기준 {d0} 종가 · {len(items)}종목" + (f" · 기준일 혼재 {mixed}종목" if mixed else "") + (f" · 일봉 실패 {len(fail)}개" if fail else "")
    data = {"S": S, "I": I, "T": T, "items": [{k: it[k] for k in ("s", "name", "ko", "ind", "chg", "date", "tv", "b", "f")} for it in items]}
    js = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (PAGE.replace("__TITLE__", html.escape(info["title"])).replace("__META__", html.escape(meta))
            .replace("__SRC__", html.escape(info["src"])).replace("__CFG__", json.dumps({
                "D": {"mas": MAS[market], "unit": "일", "bars": BARS["D"], "long": LONG[market], "chg": [[5, "5일"], [20, "20일"]]},
                "W": {"mas": MAS[market], "unit": "주", "bars": BARS["W"], "chg": [[4, "4주"], [13, "13주"]]},
                "M": {"mas": MAS[market], "unit": "개월", "bars": BARS["M"], "chg": [[3, "3개월"], [12, "12개월"]]}}, ensure_ascii=False))
            .replace("__FILT__", json.dumps(FILT[market]))
            .replace("__FBTN__", '<button data-f="-1" aria-pressed="true">전체</button>'
                     + "".join(f'<button data-f="{j}" aria-pressed="false">{n}일선 위</button>' for j, n in enumerate(FILT[market])))
            .replace("__DATA__", js))
    page = mask(page)  # 비밀값 꼴 가림(토큰·crumb는 쓰지 않지만 안전장치)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page)
    return {"market": market, "asof": d0, "mixed": mixed, "shown": len(items), "fail": len(fail), "fail_list": fail[:20],
            "bytes": os.path.getsize(out), "seconds": round(time.time() - t0, 1), "out": out}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(); ap.add_argument("--market", default="US", choices=["US", "KR"])
    ap.add_argument("--date"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(mask(json.dumps(build(a.market, a.date, a.out), ensure_ascii=False)))
