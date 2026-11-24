r"""증시 자금(고객예탁금·신용잔고·반대매매) 리포트 — 깃허브판. PC ActiveETF\funds_report.py + buddy\funds.py(11/25) 기준. AI 안 씀.

- 자료: 금융투자협회 FreeSIS(공개, 키 불필요). 차트 배경 코스피 = 야후 ^KS11(PC판의 네이버 fchart·키움 대신)
- 예약 1번(15:10 KST)이 15:45까지 5분마다 확인 → 금투협이 직전 영업일로 갱신되면 그때 1번 보내고 끝(같은 날 두 번 안 감, 상태 파일 없음)
- 휴장일(한국 공휴일·주말·12/31)이면 건너뜀
- 11/25 대표 재발 금지 원칙: 15:45까지 금투협이 직전 영업일로 안 바뀌면 발송 중단 + 내 방 [중단] 경고, 발송 실패도 내 방 한 줄
- 방 = common/rooms.json 번호(--rooms), 토큰 = 비밀값 TG_TOKEN. 로그엔 토큰·방 ID 가림
사용: python funds/funds_cloud.py --rooms 1,2,5,3 [--dry] [--no-wait]
"""
import argparse, datetime as dt, io, json, os, re, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOMS = json.load(open(os.path.join(ROOT, "common", "rooms.json"), encoding="utf-8"))["rooms"]
URL = "https://freesis.kofia.or.kr/meta/getMetaDataList.do"
KST = dt.timezone(dt.timedelta(hours=9))


def mask(s):
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", str(s))
    for r in ROOMS:
        s = s.replace(str(r["id"]), "***")
    return s


def log(m):
    print(mask(m), flush=True)


# ───────── buddy/funds.py에서 복사(fetch·build), 코스피만 야후로 ─────────
def _get(obj, days=40):
    end = dt.datetime.now(KST).date()
    body = {"dmSearch": {"tmpV40": "1000000", "tmpV41": "1", "tmpV1": "D", "tmpV45": (end - dt.timedelta(days=days)).strftime("%Y%m%d"),
                         "tmpV46": end.strftime("%Y%m%d"), "OBJ_NM": obj}}
    for i in range(3):
        try:
            r = requests.post(URL, data=json.dumps(body), timeout=30,
                              headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json; charset=UTF-8", "Referer": "https://freesis.kofia.or.kr/"})
            return r.json().get("ds1") or []
        except requests.RequestException:
            if i == 2:
                raise
            time.sleep(10)


def fetch():
    dep = _get("STATSCU0100000060BO", days=190)
    cr = _get("STATSCU0100000070BO", days=190)
    if len(dep) < 2 or len(cr) < 2:
        return None
    return dep, cr


def jo(v):
    return f"{v / 1e6:,.1f}조"


def streak(vals):
    d = [vals[i] - vals[i + 1] for i in range(len(vals) - 1)]
    if not d or d[0] == 0:
        return 0
    n = 0
    for x in d:
        if (x > 0) == (d[0] > 0) and x != 0:
            n += 1
        else:
            break
    return n if d[0] > 0 else -n


def build(data):
    dep, cr = data
    d0, d1 = dep[0], dep[1]
    c0, c1 = cr[0], cr[1]
    day = d0["TMPV1"]
    s = streak([x["TMPV2"] for x in dep])
    trend = f", {abs(s)}일째 {'증가' if s > 0 else '감소'}" if abs(s) >= 3 else ""
    dchg = d0["TMPV2"] - d1["TMPV2"]
    cchg = c0["TMPV2"] - c1["TMPV2"]
    avg20 = sum(x["TMPV6"] for x in dep[1:21]) / max(1, len(dep[1:21]))
    warn = "⚠️ " if avg20 and d0["TMPV6"] >= avg20 * 2 else ""
    lines = [f"📊 증시 자금 ({day[4:6]}/{day[6:]} 기준·금투협)",
             f"• 고객예탁금 {jo(d0['TMPV2'])} ({'+' if dchg >= 0 else '−'}{abs(dchg) / 1e6:,.1f}조{trend})",
             f"• 신용잔고 {jo(c0['TMPV2'])} (코스피 {jo(c0['TMPV3'])}·코스닥 {jo(c0['TMPV4'])}, {'+' if cchg >= 0 else '−'}{abs(cchg) / 1e6:,.1f}조)",
             f"• {warn}반대매매 {d0['TMPV6'] / 100:,.0f}억 (미수금 대비 {d0['TMPV7']}%, 전일 {d1['TMPV6'] / 100:,.0f}억{'에서 증가' if d0['TMPV6'] > d1['TMPV6'] else '에서 감소' if d0['TMPV6'] < d1['TMPV6'] else '과 같음'})"]
    return day, "\n".join(lines)


def kospi_close():
    """코스피 일별 종가 {YYYYMMDD: 종가}. 야후 ^KS11 v8 일봉."""
    from zoneinfo import ZoneInfo
    r = requests.get("https://query2.finance.yahoo.com/v8/finance/chart/%5EKS11", params={"range": "1y", "interval": "1d"},
                     headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}, timeout=20)
    res = r.json()["chart"]["result"][0]
    tz = ZoneInfo(res["meta"].get("exchangeTimezoneName", "Asia/Seoul"))
    return {dt.datetime.fromtimestamp(t, tz).strftime("%Y%m%d"): c for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c}


def plot(dep, cr, n=125):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    dep, cr = dep[:n][::-1], cr[:n][::-1]
    days = [dt.datetime.strptime(x["TMPV1"], "%Y%m%d") for x in dep]
    lab = [f"{d.month}/{d.day}" for d in days]
    x = list(range(len(dep)))
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.6, 6.4), dpi=150, sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    crd = {v["TMPV1"]: v for v in cr}
    last = dep[-1]
    title = f"증시 자금 ({lab[-1]} 기준·금투협)  예탁금 {last['TMPV2']/1e6:,.1f}조 · 신용 {crd.get(last['TMPV1'], {}).get('TMPV2', 0)/1e6:,.1f}조"
    axes = [a1]
    try:
        kc = kospi_close()
        kv = [kc.get(d["TMPV1"]) for d in dep]
        ok = [v for v in kv if v]
        if len(ok) > 20:
            c1 = a1.twinx()
            lo = min(ok) * 0.97
            c1.fill_between(x, [v or lo for v in kv], lo, color="#d1d5db", alpha=.28, lw=0)
            c1.plot(x, kv, color="#b8bec7", lw=0.9, label="코스피(배경)")
            c1.set_ylim(lo, max(ok) * 1.02)
            c1.spines["right"].set_position(("axes", 1.09))
            c1.set_ylabel("코스피", color="#9ca3af")
            c1.set_zorder(0); a1.set_zorder(1); a1.patch.set_visible(False)
            axes.append(c1)
            kd = max((d for d in kc if d <= last["TMPV1"]), default=None)
            if kd:
                title += f" · 코스피 {kc[kd]:,.0f}"
    except Exception as ex:
        log(f"코스피 배경 실패: {type(ex).__name__}")
    a1.plot(x, [v["TMPV2"] / 1e6 for v in dep], color="#2563eb", lw=2, label="고객예탁금")
    a1.set_ylabel("예탁금 (조)", color="#2563eb")
    b1 = a1.twinx()
    b1.plot(x, [crd[d["TMPV1"]]["TMPV2"] / 1e6 if d["TMPV1"] in crd else None for d in dep], color="#ea580c", lw=2, label="신용잔고")
    b1.set_ylabel("신용잔고 (조)", color="#ea580c")
    b1.set_zorder(2); b1.patch.set_visible(False)
    axes.insert(1, b1)
    a1.set_title(title, fontsize=10.5)
    hs = sum((ax.get_legend_handles_labels()[0] for ax in axes), []); ls = sum((ax.get_legend_handles_labels()[1] for ax in axes), [])
    b1.legend(hs, ls, loc="upper left", fontsize=8, frameon=False)
    a1.grid(alpha=.25)
    rev = [v["TMPV6"] / 100 for v in dep]
    avg = sum(rev[-21:-1]) / max(1, len(rev[-21:-1]))
    cols = ["#9ca3af"] * (len(rev) - 1) + ["#dc2626" if rev[-1] >= avg * 2 else "#4b5563"]
    a2.bar(x, rev, color=cols, width=.9)
    a2.axhline(avg, color="#dc2626", lw=1, ls="--", alpha=.6)
    a2.text(0, avg, f" 20일 평균 {avg:,.0f}억", color="#dc2626", fontsize=7, va="bottom")
    a2.annotate(f"{rev[-1]:,.0f}억", (len(rev) - 1, rev[-1]), fontsize=7, ha="right", va="bottom")
    a2.set_ylabel("반대매매 (억)")
    b2 = a2.twinx()
    b2.plot(x, [float(v["TMPV7"]) for v in dep], color="#7c3aed", lw=1.3)
    b2.set_ylabel("미수금 대비 (%)", color="#7c3aed")
    a2.grid(alpha=.25, axis="y")
    idx = [i for i in range(len(days)) if i == 0 or days[i].month != days[i - 1].month]
    a2.set_xticks(idx); a2.set_xticklabels([f"{days[i].year % 100}.{days[i].month}" for i in idx], fontsize=8)
    fig.tight_layout()
    buf = io.BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()


# ───────── funds_report.py에서 복사(one_line·make) ─────────
def one_line(data):
    dep, cr = data
    d0, d1, c0, c1 = dep[0], dep[1], cr[0], cr[1]
    dchg = d0["TMPV2"] - d1["TMPV2"]
    cchg = c0["TMPV2"] - c1["TMPV2"]
    avg20 = sum(x["TMPV6"] for x in dep[1:21]) / max(1, len(dep[1:21]))

    def word(chg, base, small):
        if chg == 0:
            return "보합"
        w = "증가" if chg > 0 else "감소"
        return ("소폭 " + w) if base and abs(chg) / base < small else w

    dep_w = word(dchg, d1["TMPV2"], 0.01)
    cr_w = word(cchg, c1["TMPV2"], 0.005)
    rev = d0["TMPV6"]
    if avg20 and rev >= avg20 * 2:
        tail = "반대매매 평균 2배 이상 급증으로 수급 경계"
    elif rev > avg20:
        tail = "반대매매 평균 상회로 수급 부담 확대"
    elif rev < avg20:
        tail = "반대매매 평균 하회로 수급 부담 완화"
    else:
        tail = "반대매매 평균 수준으로 수급 부담 보통"
    return f"■ 한 줄: 예탁금 {dep_w}·신용 {cr_w}, {tail}"


def make(data):
    day, text = build(data)
    return day, text + "\n" + one_line(data)


sys.path.insert(0, os.path.join(ROOT, "common"))
import fresh  # noqa: E402

is_trading = lambda d: fresh.is_trading("KR", d)
prev_trading = lambda d: fresh.prev_trading("KR", d)


def alert(text):
    tok = os.environ.get("TG_TOKEN", "").strip()
    log("알림: " + text)
    if not tok:
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": ROOMS[0]["id"], "text": text[:900]}, timeout=30)
        log(f"알림 발송 {'성공' if r.ok else '실패'} HTTP {r.status_code}")
    except Exception as e:
        log(f"알림 발송 오류 {type(e).__name__}: {e}")


def send(tok, chats, text, png):
    api = "https://api.telegram.org/bot" + tok
    fails = []
    for n, cid in chats:
        r = {}
        try:
            if png:
                r = requests.post(api + "/sendPhoto", data={"chat_id": cid, "caption": text},
                                  files={"photo": ("funds.png", png, "image/png")}, timeout=60).json()
            if not r.get("ok"):
                if png:
                    log(f"방 {n}번 sendPhoto 실패 → 글로 대신: {r.get('description')}")
                r = requests.post(api + "/sendMessage", data={"chat_id": cid, "text": text}, timeout=30).json()
        except Exception as ex:
            r = {"ok": False, "description": f"{type(ex).__name__}: {ex}"}
        log(f"방 {n}번 발송 {'성공' if r.get('ok') else '실패 ' + str(r.get('description'))}")
        if not r.get("ok"):
            fails.append(n)
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", default="1")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-wait", action="store_true", help="금투협 갱신 안 기다림(수동 시험)")
    ap.add_argument("--until", default="15:45", help="이 시각(KST)까지 5분마다 다시 확인")
    a = ap.parse_args()
    try:
        return run(a)
    except Exception as e:
        log(f"실행 실패 {type(e).__name__}: {e}")
        if not a.dry: alert(f"[깃허브] 증시 자금 실행 실패 {type(e).__name__} · 오늘 발송 안 됨")
        return 1


def run(a):
    today = dt.datetime.now(KST).date()
    if not a.no_wait:
        if not is_trading(today):
            log(f"{today} 휴장일 → 건너뜀"); return 0
        prev = prev_trading(today).strftime("%Y%m%d")
    while True:
        data = fetch()
        day = data[0][0]["TMPV1"] if data else None
        log(f"금투협 기준일 {day}")
        if data and (a.no_wait or day >= prev):
            break
        if dt.datetime.now(KST).strftime("%H:%M") >= a.until:
            msg = f"[중단] 증시 자금: 금투협 기준일 {day} ≠ 직전 영업일 {prev} ({a.until}까지 확인) → 오늘 발송 안 함"
            log(msg)
            if not a.dry: alert(msg)
            return 3
        time.sleep(300)
    day, text = make(data)
    log(text)
    try:
        png = plot(*data)
    except Exception as ex:
        log(f"차트 실패 → 글만: {type(ex).__name__}: {ex}"); png = None
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    if png:
        open(os.path.join(ROOT, "out", f"funds_{day}.png"), "wb").write(png)
    want = [int(x) for x in a.rooms.split(",") if x.strip()]
    chats = [(r["n"], str(r["id"])) for n in want for r in ROOMS if r["n"] == n]
    log("받는 방: " + ", ".join(f"{n}번" for n, _ in chats))
    if a.dry:
        if png and os.environ.get("PREVIEW_B64") == "1":  # 검수용: 그림을 실행 기록에 base64로(내려받기 막힌 환경용)
            import base64
            print("PNG_B64_BEGIN\n" + base64.b64encode(png).decode() + "\nPNG_B64_END", flush=True)
        log("dry → 안 보냄"); return 0
    tok = os.environ.get("TG_TOKEN", "").strip()
    if not tok:
        log("TG_TOKEN 없음 → 안 보냄"); return 1
    fails = send(tok, chats, text, png)
    if fails:
        alert("[깃허브] 증시 자금 발송 실패: " + ", ".join(f"방 {n}번" for n in fails))
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        open(os.path.join(ROOT, "out", "send_fail.txt"), "a", encoding="utf-8").write("".join(f"증시 자금 방 {n}번 실패\n" for n in fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
