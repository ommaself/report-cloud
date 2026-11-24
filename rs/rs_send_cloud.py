r"""섹터 ETF 상대강도(미국 vs SPY · 한국 vs KODEX 200) 차트 → 리치봇 앨범 발송. 깃허브판(PC rs_send.py 2026-11-25 판 기준).

방마다 앨범 2개(미국 → 한국, 사이 3초). 캡션·그림 만드는 부분은 PC판 그대로.
PC판과 다른 점: 방 = common/rooms.json 번호(--rooms 1,2,…), 토큰 = 깃허브 비밀값 TG_TOKEN, 상태 파일 없음
(--first-trading-day는 '오늘이 이번 주 첫 한국 거래일'만 봄. 예약은 하루 한 번이라 같은 주 두 번 안 감).
알림(11/25 대표 '절대 재발 금지' 원칙이 11/14 '알림 끔'보다 우선): 기준일이 직전 거래일이 아니면 발송 중단 + 내 방 [중단] 경고,
만들기·발송 실패도 내 방에 한 줄(조용한 실패 금지). 완료·휴일 알림은 계속 꺼짐.
사용: python rs/rs_send_cloud.py --rooms 1,2,3,4,5,6,7 --first-trading-day [--dry] [--date YYYY-MM-DD] [--set auto|monday|weekday]
"""
import argparse, datetime as dt, json, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rs_quadrant as rq
import rs_quadrant_kr as kr
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "common"))
import fresh  # 기준일 검사(11/25 대표 재발 금지 원칙)

OUT = os.path.join(os.path.dirname(HERE), "out")
ROOMS = json.load(open(os.path.join(os.path.dirname(HERE), "common", "rooms.json"), encoding="utf-8"))["rooms"]
W1, W4 = 5, 20


def mask(s):
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", str(s))
    for r in ROOMS:
        s = s.replace(str(r["id"]), "***")
    return s


def log(msg):
    print(mask(msg))


def moves_summary(px, names, lag, top=4):
    nx, ny = rq.rs(px, 0, rq.MID), rq.rs(px, 0, rq.SHORT)
    wx, wy = rq.rs(px, lag, rq.MID), rq.rs(px, lag, rq.SHORT)
    to = {}
    for t in rq.ETFS:
        a, b = rq.quad(wx[t], wy[t]), rq.quad(nx[t], ny[t])
        if a != b: to.setdefault(b, []).append(names.get(t, t))
    lines = []
    for q in ["주도", "부상", "차익", "소외"]:
        if q in to:
            ns = to[q]
            lines.append(f"→ {rq.QNAME[q]}: {', '.join(ns[:top])}" + (f" 외 {len(ns) - top}" if len(ns) > top else ""))
    return lines or ["사분면 이동 없음"]


def build_market(px, names, title, tag, kind):
    d = dt.date.today().isoformat()
    f = lambda n: os.path.join(OUT, f"rs_send_{d}_{tag}_{n}.png")
    md = lambda lag=0: f"{px.index[-1 - lag].month}/{px.index[-1 - lag].day}"
    files = []
    if kind == "monday": files.append(rq.main(f("4w"), "arrow", W4, px=px)[0])
    files.append(rq.main(f("1w"), "arrow", W1, px=px)[0])
    files.append(rq.table(f("table"), px=px))
    cap = f"{title}\n기준: {px.index[-1]:%Y-%m-%d} 종가\n{rq.bench_line(px)[0]}"
    if kind == "monday":
        cap += f"\n\n4주 사이 사분면 이동({md(W4)}→{md()})\n" + "\n".join(moves_summary(px, names, W4))
    cap += f"\n\n1주 사이 사분면 이동({md(W1)}→{md()})\n" + "\n".join(moves_summary(px, names, W1))
    cap += f"\n\n● {rq.MA}일선 위 · ○ {rq.MA}일선 아래\n{rq.qnote()}"
    return files, cap[:1024]


class Stale(Exception):
    pass


def check_date(px, market):
    got, e = px.index[-1].date(), fresh.expected(market)
    if got != e:
        raise Stale(f"[중단] 섹터 상대강도 {'미국' if market == 'US' else '한국'}: 기준일 {got} ≠ 직전 거래일 {e} → 이번 주 발송 안 함")


def alert(text):
    """내 방(rooms.json 1번)에 한 줄. 토큰·방 ID는 로그에 안 찍음."""
    tok = os.environ.get("TG_TOKEN", "").strip()
    log("알림: " + text)
    if not tok:
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": ROOMS[0]["id"], "text": text[:900]}, timeout=30)
        log(f"알림 발송 {'성공' if r.ok else '실패'} HTTP {r.status_code}")
        if r.ok:
            gh = os.environ.get("GITHUB_ENV")  # 한 사건엔 알림 하나: 이미 알렸으면 yml 'alert on crash'가 또 안 보냄
            if gh: open(gh, "a").write("ALERTED=1\n")
    except Exception as e:
        log(f"알림 발송 오류 {type(e).__name__}: {e}")


def build(kind, check=False):
    os.makedirs(OUT, exist_ok=True)
    us = rq.load()
    if check: check_date(us, "US")
    usa = build_market(us, dict(rq.NAME), "미국 섹터 ETF 상대강도 (vs SPY)", "us", kind)
    kr.setup()
    kp = kr.load()
    if check: check_date(kp, "KR")
    kra = build_market(kp, {c: v[0] for c, v in kr.ETFS.items()}, "한국 섹터 ETF 상대강도 (vs KODEX 200)", "kr", kind)
    kra = (kra[0], (kra[1] + "\n국내 시세: 야후 기준(임시), 공식 종가와 조금 다를 수 있음")[:1024])  # cloud 1125: PC판은 네이버, 클라우드는 야후
    return [("미국", *usa), ("한국", *kra)]


def is_trading(d):
    return fresh.is_trading("KR", d)


def send_album(tok, chat_id, files, cap):
    media = [{"type": "photo", "media": f"attach://p{i}"} for i in range(len(files))]
    media[0]["caption"] = cap
    fh = {f"p{i}": open(p, "rb") for i, p in enumerate(files)}
    try:
        return requests.post(f"https://api.telegram.org/bot{tok}/sendMediaGroup",
                             data={"chat_id": chat_id, "media": json.dumps(media, ensure_ascii=False)}, files=fh, timeout=120).json()
    finally:
        for h in fh.values(): h.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", default="1")
    ap.add_argument("--set", dest="kind", choices=["auto", "monday", "weekday"], default="auto")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--first-trading-day", dest="first_day", action="store_true")
    ap.add_argument("--date")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date) if a.date else (dt.datetime.utcnow() + dt.timedelta(hours=9)).date()
    if a.first_day:
        if not is_trading(today):
            log(f"{today} 거래일 아님 → 안 보냄"); return 0
        if any(is_trading(today - dt.timedelta(days=i)) for i in range(1, today.weekday() + 1)):
            log(f"{today} 이번 주 첫 거래일이 이미 지남 → 안 보냄"); return 0
    if a.kind == "auto":
        a.kind = "monday" if (a.first_day or today.weekday() == 0) else "weekday"
    try:
        albums = build(a.kind, check=a.first_day or not a.dry)  # 실제로 보내는 경로는 수동이라도 전부 기준일 검사(11/25 검수 B16)
    except Stale as e:
        log(str(e))
        if not a.dry: alert(str(e))
        return 3
    except Exception as e:
        log(f"만들기 실패 {type(e).__name__}: {e}")
        if not a.dry: alert(f"[깃허브] 섹터 상대강도 만들기 실패 {type(e).__name__} · 이번 주 발송 안 됨")
        return 1
    want = [int(x) for x in a.rooms.split(",") if x.strip()]
    targets = [(r["n"], r["name"], str(r["id"])) for n in want for r in ROOMS if r["n"] == n]
    log("받는 방: " + ", ".join(f"{n}번 {nm}" for n, nm, _ in targets))
    for mk, files, cap in albums:
        log(f"만듦 set={a.kind} {mk} {len(files)}장\n{cap}")
    if a.dry:
        return 0
    tok = os.environ.get("TG_TOKEN", "").strip()
    if not tok:
        log("TG_TOKEN 없음 → 안 보냄"); return 1  # 토큰 없으면 알림도 못 보냄(실행 기록에만)
    fails = []
    for n, nm, cid in targets:
        for mk, files, cap in albums:
            try:
                r = send_album(tok, cid, files, cap)
                ok = r.get("ok")
                log(f"보냄 방 {n}번 {mk} ok={ok} {r.get('description', '')}")
                if not ok: fails.append(f"방 {n}번 {mk}")
            except Exception as e:
                log(f"보냄 방 {n}번 {mk} 오류 {type(e).__name__}: {e}"); fails.append(f"방 {n}번 {mk}")
            time.sleep(3)
    if fails:
        log("실패: " + ", ".join(fails))
        alert("[깃허브] 섹터 상대강도 발송 실패: " + ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
