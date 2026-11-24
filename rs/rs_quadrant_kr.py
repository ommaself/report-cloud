# 국내 섹터·테마 ETF 상대강도 4사분면 (벤치마크 KODEX 200)
# 그리기는 rs_quadrant.py(미국판)를 그대로 쓰고, 종목·이름·데이터 소스만 바꿈
# cloud 1125: 데이터 = 야후 일봉(yfinance, 코드.KS). PC판의 네이버 fchart는 robots 금지라 안 씀. 장 마감(15:40) 전이면 오늘 줄은 뺌
import sys
import datetime as dt
import yfinance as yf
import rs_quadrant as rq

BENCH = "069500"
# 코드: (차트 라벨, ETF 이름) — PC판 2026-10-28 목록 그대로
ETFS = {
    "091160": ("반도체", "KODEX 반도체"),
    "455850": ("반도체소부장", "SOL AI반도체소부장"),
    "305720": ("2차전지", "KODEX 2차전지산업"),
    "091180": ("자동차", "KODEX 자동차"),
    "494670": ("조선", "TIGER 조선TOP10"),
    "449450": ("방산", "PLUS K방산"),
    "421320": ("우주항공", "PLUS 우주항공"),
    "433500": ("원전", "ACE 원자력TOP10"),
    "487240": ("전력설비", "KODEX AI전력핵심설비"),
    "117700": ("건설", "KODEX 건설"),
    "445290": ("로봇", "KODEX 로봇액티브"),
    "157490": ("소프트웨어", "TIGER 소프트웨어"),
    "091170": ("은행", "KODEX 은행"),
    "102970": ("증권", "KODEX 증권"),
    "140700": ("보험", "KODEX 보험"),
    "307520": ("지주", "TIGER 지주회사"),
    "161510": ("고배당", "PLUS 고배당주"),
    "329200": ("리츠", "TIGER 리츠부동산인프라"),
    "244580": ("바이오", "KODEX 바이오"),
    "228790": ("화장품", "TIGER 화장품"),
    "229200": ("코스닥150", "KODEX 코스닥150"),
}

def load():
    codes = list(ETFS) + [BENCH]
    raw = yf.download([c + ".KS" for c in codes], period="1y", auto_adjust=False, progress=False)["Close"]
    raw.columns = [c.replace(".KS", "") for c in raw.columns]
    raw.index = raw.index.tz_localize(None) if raw.index.tz is not None else raw.index
    px = raw[codes].sort_index().dropna(how="all").ffill()
    now = dt.datetime.utcnow() + dt.timedelta(hours=9)          # 한국 시간
    if px.index[-1].date() == now.date() and (now.hour, now.minute) < (15, 40):
        px = px.iloc[:-1]                                          # 장중·장전 줄 제외
    return px

def setup():
    rq.BENCH, rq.BENCH_NAME, rq.BENCH_DESC = BENCH, "KODEX 200", "KODEX 200"
    rq.ETFS = list(ETFS)
    rq.LABEL = {c: v[0] for c, v in ETFS.items()}
    rq.NAME = {c: v[1] for c, v in ETFS.items()}
    rq.TITLE, rq.CLOSE = "한국 섹터 ETF", "한국 종가"
    rq.NAME_X, rq.NAME_FS = .33, 9.5
    rq.SIDE_NAME = False
    rq.TABLE_TEXT = ["label*", "name"]
    rq.MA = 60
    rq.TABLE_HEAD, rq.TABLE_W = ("섹터", "ETF"), 11.5
    rq.TABLE_CX = [.03, .14, .385, .465, .545, .625, .695, .765, .85]
    rq.load = load
