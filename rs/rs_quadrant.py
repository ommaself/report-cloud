# ETF 상대강도 4사분면 (벤치마크 SPY)
# X = 중기 3개월(63거래일) 초과수익 %p, Y = 단기 1개월(21거래일) 초과수익 %p
# 각 시점 값 = 그 시점 포함 최근 5거래일 RS 평균(평활)
# 꼬리 = 1주·2주·3주 전 위치 → 현재 (화살표), 오른쪽 = 사분면별 섹터 목록
import sys
import logging
import numpy as np
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.collections import LineCollection, PolyCollection
import matplotlib.patheffects as pe
import matplotlib.transforms
from adjustText import adjust_text

BENCH = "SPY"
BENCH_NAME = "SPY"          # 제목·축에 쓰는 벤치마크 이름
TITLE = "미국 섹터 ETF"
CLOSE = "미국 종가"
LABEL = {}                  # 차트 라벨(없으면 티커)
NAME_X, NAME_FS = .24, 10.5  # 오른쪽 목록 설명 칸 위치·글자 크기
SIDE_NAME = True            # 오른쪽 목록에 NAME 칸 표시
# 히트맵 표 앞쪽 글자 칸: name=NAME, label=LABEL(없으면 티커), etf=ETF_NAME, 끝에 *=사분면 색 굵게
TABLE_TEXT = ["name*", "label", "etf"]
TABLE_HEAD, TABLE_W = ("섹터", "티커", "ETF"), 13
TABLE_CX = [.03, .135, .195, .42, .50, .58, .66, .73, .80, .865]   # 글자 칸들 + 1주·1개월·3개월(vs 지수)·실제 3개월·50일선·사분면·변화
MA = 50                     # 절대 추세 필터 이동평균선(거래일, 단순·종가). 한국판은 60

def above_ma(px, t):
    # 평활 안 한 최신 종가 > MA일 단순이동평균
    return px[t].iloc[-1] > px[t].iloc[-MA:].mean()
ETF_NAME = {"XLK": "Technology SPDR", "SMH": "VanEck Semiconductor", "XSD": "SPDR S&P Semiconductor",
            "DRAM": "Roundhill Memory", "IGV": "iShares Software", "WCLD": "WisdomTree Cloud",
            "BUG": "Global X Cybersecurity", "XLF": "Financial SPDR", "KRE": "SPDR Regional Banking",
            "IAI": "iShares Broker-Dealers", "XLE": "Energy SPDR", "XOP": "SPDR Oil & Gas E&P",
            "OIH": "VanEck Oil Services", "XLV": "Health Care SPDR", "XBI": "SPDR Biotech",
            "XLI": "Industrial SPDR", "ITA": "iShares Aero & Defense", "PAVE": "Global X Infrastructure",
            "XLB": "Materials SPDR", "URA": "Global X Uranium", "XLU": "Utilities SPDR",
            "XLRE": "Real Estate SPDR", "ITB": "iShares Home Construction", "XLC": "Communication SPDR",
            "XLP": "Consumer Staples SPDR", "XLY": "Consumer Discr. SPDR", "GDX": "VanEck Gold Miners",
            "RSP": "Invesco S&P500 Equal Wt"}
ETFS = ["XLK","SMH","XSD","DRAM","IGV","WCLD","BUG",
        "XLF","KRE","IAI","XLE","XOP","OIH","XLV","XBI",
        "XLI","ITA","PAVE","XLB","URA","XLU","XLRE","ITB",
        "XLC","XLP"]
NAME = {"XLK": "기술", "SMH": "반도체(대형)", "XSD": "반도체(동일가중)", "DRAM": "메모리반도체",
        "IGV": "소프트웨어", "WCLD": "클라우드", "BUG": "사이버보안",
        "XLF": "금융", "KRE": "지역은행", "IAI": "증권·브로커",
        "XLE": "에너지", "XOP": "석유·가스 탐사", "OIH": "유전서비스",
        "XLV": "헬스케어", "XBI": "바이오", "XLI": "산업재", "ITA": "방산·항공",
        "PAVE": "인프라", "XLB": "소재", "URA": "우라늄·원전", "XLU": "유틸리티",
        "XLRE": "리츠", "ITB": "주택건설", "XLC": "커뮤니케이션", "XLP": "필수소비재",
        "XLY": "임의소비재", "GDX": "금광", "RSP": "S&P500 동일가중"}
SHORT, MID = 21, 63
TAIL = [15, 10, 5]          # 며칠 전 위치를 꼬리로 (3주·2주·1주 전)
SMOOTH = 5                  # 평활 기간(거래일)

rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]  # cloud 1125: 깃허브(우분투)는 나눔고딕
rcParams["axes.unicode_minus"] = False
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

def load():
    T = ETFS + [BENCH]
    raw = yf.download(T, period="1y", auto_adjust=True, progress=False)["Close"]
    # 야후가 장 마감 직후 마지막 날 일봉 종가를 빈 값으로 줄 때가 있음 → 1시간봉 마지막 값으로 채움
    if raw.iloc[-1].isna().any():
        h = yf.download(T, period="5d", interval="1h", auto_adjust=True, progress=False)["Close"]
        hh = h[h.index.date == raw.index[-1].date()]
        if len(hh): raw.iloc[-1] = raw.iloc[-1].fillna(hh.ffill().iloc[-1])
    return raw.dropna(how="all").ffill()

def bench_line(px):
    # 기준 지수 자체의 단순 수익률(평균 안 낸 값) → (글자, 3개월 수익률)
    b = px[BENCH]; r = lambda n: (b.iloc[-1] / b.iloc[-1 - n] - 1) * 100
    return f"{BENCH_NAME} 실제 수익률: 3개월 {r(MID):+.1f}% · 1개월 {r(SHORT):+.1f}% · 1주 {r(5):+.1f}%", r(MID)

def bench_color(v):          # 마이너스면 눈에 띄게 진한 빨강, 플러스면 진한 초록
    return "#B91C1C" if v < 0 else "#15803D"

def rs_raw(px, lag, n):
    # lag일 전 시점 기준 n일 초과수익(%p)
    end = len(px) - 1 - lag
    r = px.iloc[end] / px.iloc[end - n] - 1
    return (r - r[BENCH]) * 100

def rs(px, lag, n):
    # lag일 전 시점 포함 최근 SMOOTH일 RS 평균
    return sum(rs_raw(px, lag + k, n) for k in range(SMOOTH)) / SMOOTH

def quad(x, y):           # x=중기, y=단기
    if x >= 0 and y >= 0: return "주도"
    if x >= 0 and y < 0:  return "차익"
    if x < 0 and y < 0:   return "소외"
    return "부상"

def curve(xs, ys, k=12):
    # Catmull-Rom: 점들을 지나는 매끈한 곡선
    p = np.array([xs, ys], dtype=float).T
    p = np.vstack([p[0], p, p[-1]])
    pts = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i-1:i+3]
        for t in np.linspace(0, 1, k, endpoint=False):
            pts.append(.5 * (2*p1 + (p2-p0)*t + (2*p0-5*p1+4*p2-p3)*t*t + (3*p1-p0-3*p2+p3)*t**3))
    pts.append(p[-2])
    return [q[0] for q in pts], [q[1] for q in pts]

TAIL_STYLE = "line"         # line=주간 4점 직선, curve=곡선, arrow=N일 전→지금 화살표 하나, dots=주간 점+흐림
ARROW_FROM = 5              # arrow일 때 화살표 시작점·이동 비교 기준(거래일 전)

ARROW_COLOR = "comet"       # arrow 표시: comet=점 색 혜성꼬리(기본), grey=점 색 가는 꼬리, glyph=선 없이 라벨 뒤 방향 기호, quad/dir=예전 색 화살표
THEME = "light"             # light(기본, 휴대폰용 밝은 화면) / dark(예전 어두운 화면)
THEMES = {
    # col=점·배지, tcol=글자, fill/falpha=사분면 바탕, weak=덜 강조할 사분면(점 80%, 라벨 보통 굵기)
    "light": dict(bg="#FFFFFF", title="#111827", sub="#6B7280", axis="#374151", tick="#6B7280",
                  zero="#9CA3AF", label=None, spine=None, fill_alpha=.11, tsize=11.5,
                  fill={"주도": "#DCFCE7", "차익": "#FEF9C3", "소외": "#F3F4F6", "부상": "#DBEAFE"},
                  falpha={"주도": .5, "차익": .3, "소외": .3, "부상": .5},
                  col={"주도": "#15803D", "차익": "#A16207", "소외": "#9CA3AF", "부상": "#1D4ED8"},
                  tcol={"주도": "#15803D", "차익": "#A16207", "소외": "#6B7280", "부상": "#1D4ED8"},
                  weak={"소외"}),
    "dark": dict(bg="#0f172a", title="white", sub="#94a3b8", axis="#cbd5e1", tick="#94a3b8",
                 zero="#64748b", label="white", spine="#334155", fill_alpha=.35, tsize=9,
                 fill={"주도": "#064e3b", "차익": "#713f12", "소외": "#7f1d1d", "부상": "#1e3a8a"},
                 col={"주도": "#10b981", "차익": "#f59e0b", "소외": "#ef4444", "부상": "#60a5fa"}),
}
DIR_COL = {"up": "#16A34A", "down": "#DC2626", "side": "#9CA3AF"}
QUADS = {"주도": (1, 1), "차익": (1, -1), "소외": (-1, -1), "부상": (-1, 1)}
# 화면에 보이는 사분면 이름(여기서만 바꾸면 차트·목록·표·이동 텍스트 모두 바뀜)
WEEK_COL = {5: "#2563EB", 20: "#7C3AED"}   # 기간 배지 색(1주·4주)
QNAME = {"주도": "장단기 우위", "차익": "단기열위(장기우위)", "소외": "장단기 열위", "부상": "단기우위(장기열위)"}
QSHORT = {"주도": "장단기우위", "차익": "단기열위", "소외": "장단기열위", "부상": "단기우위"}   # 차트 모서리·목록·표 칸
QSUB = {"차익": "(장기우위)", "부상": "(장기열위)"}                                           # 모서리 이름 아래 작은 줄
BENCH_DESC = "S&P500(SPY)"                                                                   # 우위·열위 기준 설명

def qnote():
    return f"우위·열위 = {BENCH_DESC} 대비 · 장기=3개월, 단기=1개월"

def faint_tail(ax, x0, y0, x1, y1, c, k=14):
    # 점 색 꼬리: 과거 쪽은 아주 가늘고 연하게 → 현재 점 쪽으로 갈수록 조금씩 굵고 진하게(화살촉·출발점 원 없음)
    f = np.linspace(0, 1, k + 1)
    px_, py_ = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
    segs = [[(px_[i], py_[i]), (px_[i+1], py_[i+1])] for i in range(k)]
    ax.add_collection(LineCollection(segs, colors=[matplotlib.colors.to_rgba(c, a) for a in np.linspace(.08, .5, k)],
                                     linewidths=np.linspace(.3, 1.6, k), capstyle="butt", zorder=1))

DOT = 70                    # 점 크기(scatter s)

def place_labels(ax, pts, fs, obstacles=()):
    # 라벨을 점에 붙여 배치: 점 오른쪽 바로 옆(알약 박스) → 겹치면 8방향·먼 거리 순으로 빈자리 → 옮긴 라벨은 점 색 가는 선으로 연결
    # pts = [(x, y, 글자, 색)], 레이아웃 확정 뒤에 불러야 함
    fig = ax.figure; rd = fig.canvas.get_renderer(); T = ax.transData
    r = np.sqrt(DOT) / 2 * fig.dpi / 72 + 1.5            # 점 반지름(픽셀, 흰 테두리 포함)
    dirs = [(1, 0, "left", "center"), (-1, 0, "right", "center"), (0, 1, "center", "bottom"), (0, -1, "center", "top"),
            (.75, .75, "left", "bottom"), (-.75, .75, "right", "bottom"), (.75, -.75, "left", "top"), (-.75, -.75, "right", "top")]
    area = ax.get_window_extent(rd)
    taken = [b.padded(2) for b in obstacles]
    dotbox = [matplotlib.transforms.Bbox.from_bounds(*(T.transform((x, y)) - r), 2*r, 2*r) for x, y, *_ in pts]
    for x, y, s, c, w in sorted(pts, key=lambda p: -p[1]):
        mine = matplotlib.transforms.Bbox.from_bounds(*(T.transform((x, y)) - r), 2*r, 2*r)
        best = None
        for ring, dist in enumerate([r + 5, r + 26, r + 48, r + 72]):
            for dx, dy, ha, va in dirs:
                a = ax.annotate(s, (x, y), xytext=(dx * dist, dy * dist), textcoords="offset pixels",
                                ha=ha, va=va, fontsize=fs, weight=w, color=c, zorder=10,
                                bbox=dict(boxstyle="round,pad=.22,rounding_size=.7", fc="white", ec=c, lw=1))
                bb = a.get_window_extent(rd).padded(4)            # 글자 + 박스 여백
                ok = (area.contains(bb.x0, bb.y0) and area.contains(bb.x1, bb.y1)
                      and not any(bb.overlaps(o) for o in taken)
                      and not any(bb.overlaps(d) for d in dotbox if not np.allclose(d.bounds, mine.bounds)))
                if ok:
                    best = a; break
                a.remove()
            if best: break
        if best is None:                                  # 빈자리가 없으면 기본 위치
            best = ax.annotate(s, (x, y), xytext=(r + 5, 0), textcoords="offset pixels", ha="left", va="center",
                               fontsize=fs, weight=w, color=c, zorder=10,
                               bbox=dict(boxstyle="round,pad=.22,rounding_size=.7", fc="white", ec=c, lw=1))
            ring, dx, dy = 0, 1, 0
        if (ring, dx, dy) != (0, 1, 0):                   # 옮긴 라벨: 점 → 박스 연결선
            ax.annotate("", (x, y), xytext=best.get_position(), textcoords="offset pixels",
                        arrowprops=dict(arrowstyle="-", color=c, lw=.8, shrinkA=0,
                                        shrinkB=np.sqrt(DOT) / 2 + 1, alpha=.9), zorder=9)
        taken.append(best.get_window_extent(rd).padded(3))

def comet(ax, x0, y0, x1, y1, c, n=48, dot=DOT):
    # 혜성꼬리: 출발점 폭 0 → 점 쪽으로 점 지름의 40%까지 곧게 넓어짐, 투명도 0.05 → 0.55
    # 화면 좌표로 수직 오프셋을 계산하므로 레이아웃(tight_layout)이 끝난 뒤 불러야 함
    T = ax.transData; inv = T.inverted()
    p0, p1 = T.transform((x0, y0)), T.transform((x1, y1))
    d = p1 - p0; L = np.hypot(*d)
    if L < 1: return
    nv = np.array([-d[1], d[0]]) / L
    W = .4 * np.sqrt(dot) * ax.figure.dpi / 72 / 2         # 끝 폭의 절반(픽셀)
    polys, cols = [], []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a, b = p0 + d * t0, p0 + d * t1
        q = [a + nv * W * t0, b + nv * W * t1, b - nv * W * t1, a - nv * W * t0]
        polys.append(inv.transform(q))
        cols.append(matplotlib.colors.to_rgba(c, .05 + .5 * (t0 + t1) / 2))
    ax.add_collection(PolyCollection(polys, facecolors=cols, edgecolors="none", linewidths=0, zorder=1))

GLYPH = ["→", "↗", "↑", "↖", "←", "↙", "↓", "↘"]

def gradient_arrow(ax, x0, y0, x1, y1, c, k=8):
    # 과거(흐리고 가늘게) → 현재(진하고 굵게), 화살촉은 현재 점 바로 앞에서 끝
    ax.scatter(x0, y0, s=14, facecolors="none", edgecolors=c, lw=.8, alpha=.35, zorder=2)
    f = np.linspace(0, .88, k + 1)
    px_, py_ = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
    segs = [[(px_[i], py_[i]), (px_[i+1], py_[i+1])] for i in range(k)]
    a = np.linspace(.12, .85, k)
    rgba = [matplotlib.colors.to_rgba(c, v) for v in a]
    ax.add_collection(LineCollection(segs, colors=rgba, linewidths=np.linspace(.4, 1.7, k), capstyle="round", zorder=2))
    ax.annotate("", xy=(x1, y1), xytext=(px_[-1], py_[-1]),
                arrowprops=dict(arrowstyle="-|>", color=c, lw=1.6, alpha=.85, mutation_scale=9,
                                shrinkA=0, shrinkB=4.5), zorder=2)

def main(out="rs_quadrant.png", style=None, lag=None, theme=None, px=None, acol=None):
    style = style or TAIL_STYLE
    acol = acol or ARROW_COLOR
    th = THEMES[theme or THEME]; col = th["col"]
    mv = (lag or ARROW_FROM) if style == "arrow" else 5
    px = load() if px is None else px
    now_x, now_y = rs(px, 0, MID), rs(px, 0, SHORT)
    lags = [mv] if style == "arrow" else TAIL
    hist = [(rs(px, l, MID), rs(px, l, SHORT)) for l in lags]
    day = lambda lag: px.index[-1 - lag].strftime("%m/%d")
    md = lambda lag: f"{px.index[-1 - lag].month}/{px.index[-1 - lag].day}"

    fig, (ax, side) = plt.subplots(1, 2, figsize=(14, 7.5), dpi=160,
                                   gridspec_kw={"width_ratios": [10, 3.8]})
    for o in (fig.patch, ax, side): o.set_facecolor(th["bg"])
    clean = style == "arrow" and acol in ("grey", "glyph", "comet")    # 현재 점 기준 축(과거 꼬리는 잘려도 됨)
    lim_x = max([abs(now_x[ETFS]).max()] + ([] if clean else [abs(h[0][ETFS]).max() for h in hist])) * (1.28 if clean else 1.15)
    lim_y = max([abs(now_y[ETFS]).max()] + ([] if clean else [abs(h[1][ETFS]).max() for h in hist])) * (1.28 if clean else 1.15)
    def fit(v):               # 점 범위에 맞추되 0선은 늘 보이고 양쪽 사분면이 최소 12%는 보이게
        lo, hi = min(v.min(), 0), max(v.max(), 0); sp = hi - lo; pad = sp * .12
        return min(lo - pad, -.12 * sp), max(hi + pad, .12 * sp)
    (xlo, xhi), (ylo, yhi) = (fit(now_x[ETFS]), fit(now_y[ETFS])) if clean else ((-lim_x, lim_x), (-lim_y, lim_y))
    lim_x, lim_y = (xhi - xlo) / 2, (yhi - ylo) / 2      # 이동 거리 비교용 반폭
    ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
    tc = th.get("tcol", col); weak = th.get("weak", set())
    qtexts = []
    for k, (sx, sy) in QUADS.items():
        ex, ey = (xhi if sx > 0 else xlo), (yhi if sy > 0 else ylo)
        ax.fill_between([0, ex], 0, ey, color=th["fill"][k], alpha=th.get("falpha", {}).get(k, th["fill_alpha"]),
                        lw=0, zorder=0)
        qx, qy = ex - sx * (xhi - xlo) * .015, ey - sy * (yhi - ylo) * .02
        ha, va = ("right" if sx > 0 else "left"), ("top" if sy > 0 else "bottom")
        sub = QSUB.get(k)   # 작은 줄은 위쪽 사분면이면 큰 이름 아래, 아래쪽이면 모서리 쪽(큰 이름은 그 위)
        qtexts.append(ax.annotate(QSHORT[k], (qx, qy), xytext=(0, 15 if sub and sy < 0 else 0),
                                  textcoords="offset points", color=tc[k], fontsize=16, weight="bold", alpha=.75,
                                  zorder=.5, ha=ha, va=va))
        if sub:
            qtexts.append(ax.annotate(sub, (qx, qy), xytext=(0, -22 if sy > 0 else 0), textcoords="offset points",
                                      color=tc[k], fontsize=11, weight="bold", alpha=.65, zorder=.5, ha=ha, va=va))
    ax.axhline(0, color=th["zero"], lw=1, ls=":"); ax.axvline(0, color=th["zero"], lw=1, ls=":")

    labels, comets, pins = [], [], []
    for t in ETFS:
        q = quad(now_x[t], now_y[t])
        xs = [h[0][t] for h in hist] + [now_x[t]]
        ys = [h[1][t] for h in hist] + [now_y[t]]
        mark = ""
        if style == "arrow":
            dx, dy = xs[-1] - xs[0], ys[-1] - ys[0]
            far = ((dx / (2*lim_x))**2 + (dy / (2*lim_y))**2) ** .5
            if acol == "comet":
                if far >= .02: comets.append((xs[0], ys[0], xs[-1], ys[-1], col[q]))
            elif acol == "glyph":                                 # 8방향 기호, 아주 작은 이동은 기호 없음
                if far >= .03: mark = " " + GLYPH[round(np.degrees(np.arctan2(dy / lim_y, dx / lim_x)) / 45) % 8]
            elif acol == "grey":
                if far >= .02: faint_tail(ax, xs[0], ys[0], xs[-1], ys[-1], col[q])
            elif far >= .02:                                    # 아주 작은 이동은 점만
                c = col[q] if acol == "quad" else DIR_COL["up" if dx > 0 and dy > 0 else
                                                          "down" if dx < 0 and dy < 0 else "side"]
                gradient_arrow(ax, xs[0], ys[0], xs[-1], ys[-1], c)
        elif style == "dots":     # 오래된 구간일수록 흐리게
            n = len(xs) - 1
            for i in range(n):
                a = .15 + .6 * i / max(n - 1, 1)
                ax.plot(xs[i:i+2], ys[i:i+2], color=col[q], lw=1.2, alpha=a)
                ax.scatter(xs[i], ys[i], s=12, color=col[q], alpha=a, zorder=2)
        else:
            if style == "curve": xs, ys = curve(xs, ys)
            ax.plot(xs, ys, color=col[q], lw=1, alpha=.45)
        if style != "arrow":
            ax.annotate("", xy=(xs[-1], ys[-1]), xytext=(xs[-2], ys[-2]),
                        arrowprops=dict(arrowstyle="->", color=col[q], lw=1.2, alpha=.8))
        if clean:                 # 라벨은 레이아웃 뒤 place_labels로 붙임
            up = above_ma(px, t)                          # 이평선 위 = 꽉 찬 점, 아래 = 속 빈 점
            ax.scatter(xs[-1], ys[-1], s=DOT * (.8 if q in weak else 1), zorder=6,
                       facecolors=col[q] if up else th["bg"], edgecolors=th["bg"] if up else col[q],
                       linewidths=1.5 if up else 1.8)
            pins.append((xs[-1], ys[-1], f"{LABEL.get(t, t)}{mark}", th["label"] or tc[q],
                         "normal" if q in weak else "bold"))
            continue
        ax.scatter(xs[-1], ys[-1], s=55, color=col[q], edgecolors=th["bg"], linewidths=.8, zorder=5)
        labels.append(ax.text(xs[-1], ys[-1], f" {LABEL.get(t, t)}{mark}", color=th["label"] or col[q],
                              fontsize=th["tsize"], weight="bold", ha="left", va="center", zorder=10,
                              path_effects=[pe.withStroke(linewidth=3, foreground=th["bg"])]))
    # 겹칠 때만 조금 비켜 놓기(연결선 없음)
    if labels:
        adjust_text(labels, x=list(now_x[ETFS]), y=list(now_y[ETFS]), ax=ax,
                    expand=(1.05, 1.2), max_move=(15, 15))

    wk = f"{round(mv / 5)}주"
    head = f"{TITLE} 상대강도 · {wk} 변화" if style == "arrow" else \
        f"{TITLE} 상대강도 4사분면 (vs {BENCH_NAME}, {px.index[-1]:%Y-%m-%d})"
    fig.suptitle(head, color=th["title"], fontsize=17, weight="bold")
    if style == "arrow":      # 오른쪽 위 기간 배지
        fig.text(.985, .975, f" {wk} 변화 ", color="white", fontsize=15, weight="bold", ha="right", va="top",
                 bbox=dict(boxstyle="round,pad=.35", fc=WEEK_COL.get(mv, "#475569"), ec="none"))
    if style == "arrow":
        sub = f"화살표: {md(mv)} → {md(0)} ({wk})  ·  vs {BENCH_NAME}  ·  {CLOSE}  ·  {SMOOTH}일 평균"
        if acol == "dir": sub += "  ·  화살표 초록=↗좋아짐 빨강=↙나빠짐 회색=그 밖"
        if acol == "glyph": sub = sub.replace("화살표:", "방향 기호:")
        if acol in ("grey", "comet"): sub = sub.replace("화살표:", "꼬리:")
    else:
        tail = f"꼬리 {day(15)}→{day(10)}→{day(5)}" + ("(곡선)" if style == "curve" else "")
        sub = f"점={day(0)} · {tail} · 이동={day(5)}→{day(0)} ({CLOSE}, {SMOOTH}일 평균)"
    bl, b3 = bench_line(px)
    ax.set_title(f"{sub}\n{qnote()}", color=th["sub"], fontsize=11, pad=24, linespacing=1.5)
    ax.text(.5, 1.012, bl, transform=ax.transAxes, ha="center", va="bottom", fontsize=11, weight="bold",
            color=bench_color(b3))
    ax.set_xlabel(f"중기 추세: 3개월 초과수익 vs {BENCH_NAME} (%p) →", color=th["axis"], fontsize=11)
    ax.set_ylabel(f"단기 모멘텀: 1개월 초과수익 vs {BENCH_NAME} (%p) →", color=th["axis"], fontsize=11)
    ax.tick_params(colors=th["tick"], length=0)
    for s in ax.spines.values():
        s.set_visible(th["spine"] is not None)
        if th["spine"]: s.set_color(th["spine"])

    # 오른쪽 목록: 사분면별, 3개월 RS 높은 순 (티커 | 섹터 | 3M/1M 오른쪽 정렬)
    side.axis("off")
    rows = []
    for q in ["주도", "차익", "부상", "소외"]:
        ts = sorted((t for t in ETFS if quad(now_x[t], now_y[t]) == q), key=lambda t: -now_x[t])
        if not ts: continue
        rows.append(("H", q, len(ts)))
        rows += [("R", q, t) for t in ts]
    step = min(.038, .95 / len(rows))
    tr = side.transAxes
    side.text(1, 1.0, "3M / 1M %p", color=th["sub"], fontsize=10, transform=tr, va="top", ha="right")
    for i, (kind, q, v) in enumerate(rows):
        y = .965 - i*step
        if kind == "H":
            side.text(0, y, f" {QSHORT[q]} {v} ", color="white", fontsize=10.5, weight="bold", transform=tr, va="top",
                      bbox=dict(boxstyle="round,pad=.2", fc=col[q], ec="none"))
        else:
            side.text(0, y, LABEL.get(v, v), color=tc[q], fontsize=10.5, transform=tr, va="top",
                      weight="normal" if q in weak else "bold")
            if SIDE_NAME:
                side.text(NAME_X, y, NAME.get(v, ""), color=th["axis"], fontsize=NAME_FS, transform=tr, va="top")
            side.text(1, y, f"{now_x[v]:+.0f} / {now_y[v]:+.0f}", color=th["axis"], fontsize=10.5,
                      transform=tr, va="top", ha="right")

    fig.tight_layout(rect=(0, .045, 1, 1) if clean else (0, 0, 1, 1))
    if clean:                 # 맨 아래 로직 설명
        fig.text(.012, .014, f"상대강도 = ETF 수익률 − 지수({BENCH_NAME}) 수익률(%p). 가로 3개월, 세로 1개월, 최근 {SMOOTH}거래일 평균.  "
            f"● 꽉 찬 점 = {MA}일선 위(상승 추세), ○ 빈 점 = {MA}일선 아래. 상대강도가 높아도 빈 점이면 '덜 빠졌을 뿐'일 수 있음.", fontsize=9.5, color="#6B7280", ha="left", va="bottom")
    for cm_ in comets: comet(ax, *cm_)            # 레이아웃 확정 뒤에 그려야 폭이 정확함
    if pins:
        rd = fig.canvas.get_renderer()
        place_labels(ax, pins, th["tsize"], [q_.get_window_extent(rd) for q_ in qtexts])
    fig.savefig(out, facecolor=fig.get_facecolor())
    plt.close(fig)

    # mv일 전 대비 사분면 바뀐 ETF
    wx, wy = rs(px, mv, MID), rs(px, mv, SHORT)
    moves = [f"{t}: {QNAME[quad(wx[t], wy[t])]} → {QNAME[quad(now_x[t], now_y[t])]}"
             for t in ETFS if quad(wx[t], wy[t]) != quad(now_x[t], now_y[t])]
    print("\n".join(moves) or "사분면 이동 없음")
    return out, moves

def table(out="rs_table.png", px=None):
    # 순위 히트맵 표: 3개월 RS 높은 순, 1주(원값)·1개월·3개월(5일 평균) vs SPY
    from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
    col, tc, weak = THEMES["light"]["col"], THEMES["light"]["tcol"], THEMES["light"]["weak"]
    px = load() if px is None else px
    w1, m1, m3 = rs_raw(px, 0, 5), rs(px, 0, SHORT), rs(px, 0, MID)
    p1, p3 = rs(px, 5, SHORT), rs(px, 5, MID)
    ts = sorted(ETFS, key=lambda t: -m3[t])
    cmap = LinearSegmentedColormap.from_list("rg", ["#FCA5A5", "#FFFFFF", "#22C55E"])
    n, RH = len(ts), .42
    FOOT = .45                                     # 아래 설명 줄 높이
    H = 1.85 + RH * n + FOOT
    fig = plt.figure(figsize=(TABLE_W, H), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    yy = lambda r: 1 - (1.55 + RH * r) / H         # r행 중심(0=헤더)
    cx = TABLE_CX
    ax.text(.04, 1 - .33 / H, f"{TITLE} 상대강도 순위 (vs {BENCH_NAME})", fontsize=16, weight="bold",
            color="#111827", va="center")
    d = lambda i: f"{px.index[i].month}/{px.index[i].day}"
    ax.text(.04, 1 - .72 / H, f"{px.index[-1]:%Y-%m-%d} {CLOSE} · %p · 1주=원값, 1·3개월={SMOOTH}일 평균 · "
            f"변화={d(-6)}→{d(-1)} · {qnote()}", fontsize=10, color="#6B7280", va="center")
    bl, b3 = bench_line(px)
    ax.text(.04, 1 - 1.05 / H, bl, fontsize=11, weight="bold", color=bench_color(b3), va="center")
    raw3 = {t: (px[t].iloc[-1] / px[t].iloc[-1 - MID] - 1) * 100 for t in ETFS}   # ETF 자체 3개월(평균 안 냄)
    above = {t: above_ma(px, t) for t in ETFS}
    k = len(TABLE_TEXT)
    for x, h, ha in zip(cx, [*TABLE_HEAD, "1주\n(vs 지수)", "1개월\n(vs 지수)", "3개월\n(vs 지수)", "실제\n3개월",
                             f"{MA}일선", "사분면", "사분면 변화(1주)"],
                        ["left"] * k + ["center", "center", "center", "center", "center", "center", "left"]):
        ax.text(x, yy(0), h, fontsize=10, weight="bold", color="#374151", ha=ha, va="center", linespacing=1.1)
    ax.plot([.03, .97], [yy(.5)] * 2, color="#E5E7EB", lw=1)
    cw, ch = min(.105, (cx[k+1] - cx[k]) * .93), .34 / H
    src = {"name": lambda t: NAME.get(t, ""), "label": lambda t: LABEL.get(t, t), "etf": lambda t: ETF_NAME.get(t, "")}
    for r, t in enumerate(ts, 1):
        y = yy(r); q = quad(m3[t], m1[t]); pq = quad(p3[t], p1[t])
        for x, key in zip(cx, TABLE_TEXT):
            strong = key.endswith("*")
            ax.text(x, y, src[key.rstrip("*")](t), va="center", fontsize=11 if strong else min(NAME_FS, 10),
                    weight="bold" if strong and q not in weak else "normal", color=tc[q] if strong else "#374151")
        for x, v, lim in [(cx[k], w1[t], 6), (cx[k+1], m1[t], 15), (cx[k+2], m3[t], 25)]:
            c = cmap(TwoSlopeNorm(0, -lim, lim)(max(-lim, min(lim, v))))
            ax.add_patch(plt.Rectangle((x - cw/2, y - ch/2), cw, ch, color=c, lw=0))
            ax.text(x, y, f"{v:+.1f}", fontsize=10.5, ha="center", va="center",
                    color="#111827", weight="bold" if abs(v) >= lim * .6 else "normal")
        rv = raw3[t]                                  # 실제 3개월: 색칠 없이 연한 빨강/초록 글자
        ax.text(cx[k+3], y, f"{rv:+.1f}%", fontsize=10.5, ha="center", va="center",
                color="#E06666" if rv < 0 else "#4CAF7A")
        ax.text(cx[k+4], y, "●" if above[t] else "○", fontsize=14, ha="center", va="center",
                color="#15803D" if above[t] else "#9CA3AF")
        ax.text(cx[k+5], y, f" {QSHORT[q]} ", fontsize=10, weight="bold", color="white", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=.25", fc=col[q], ec="none"))
        if pq != q:
            ax.text(cx[k+6], y, f"{QSHORT[pq]}→{QSHORT[q]}", fontsize=10, color=tc[q], weight="bold", va="center")
        else:
            ax.text(cx[k+6] + .05, y, "–", fontsize=10, color="#9CA3AF", va="center")
    ax.text(.04, FOOT * .55 / H,
            f"※ 상대강도(vs 지수) = ETF 수익률 − 지수({BENCH_NAME}) 수익률(%p), 1·3개월은 최근 {SMOOTH}거래일 평균. 실제 3개월 = ETF 자체 수익률.\n"
            f"※ {MA}일선 ● = 종가가 {MA}일 이동평균선 위(상승 추세), ○ = 아래. 상대강도가 높아도 ○이면 '덜 빠졌을 뿐'일 수 있음.",
            fontsize=9.5, color="#6B7280", va="center", linespacing=1.5)
    fig.savefig(out, facecolor="#FFFFFF")
    plt.close(fig)
    return out

if __name__ == "__main__":
    # 예: out.png arrow 20 light  /  table out.png
    a = sys.argv[1:]
    if a and a[0] == "table":
        table(a[1] if len(a) > 1 else "rs_table.png")
    else:
        main(a[0] if a else "rs_quadrant.png", a[1] if len(a) > 1 else None,
             int(a[2]) if len(a) > 2 else None, a[3] if len(a) > 3 else None)
