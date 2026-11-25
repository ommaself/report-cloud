r"""잘못 보낸 리치봇 파일 메시지 지우기(11/25 대표 지시: 내 방 밖 히트맵 모두에게서 삭제).
message_id 기록이 없어서 찾기: editMessageReplyMarkup(바꿀 것 없음) 오류 문구로 '없음/남의 것/봇 것' 구분 → 봇 것만
내 방으로 전달해 파일 이름·원래 보낸 시각 확인 → 맞으면 원래 방에서 deleteMessage, 확인용 전달본도 내 방에서 지움.
토큰·방 ID는 출력 안 함(방 번호만).
사용: python common/tg_cleanup.py --rooms 2,3,4,5,6,7,8 --file heatmap_US.html --start 2026-11-25T04:58:00 --end 2026-11-25T05:02:00 [--dry]
"""
import argparse, datetime as dt, json, os, sys, time
import requests

ROOMS = {r["n"]: r for r in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rooms.json"), encoding="utf-8"))["rooms"]}
TOK = os.environ.get("TG_TOKEN", "").strip()
API = f"https://api.telegram.org/bot{TOK}/"
S = requests.Session()


def call(m, **p):
    for _ in range(6):
        try:
            r = S.post(API + m, data=p, timeout=30).json()
        except Exception as e:
            time.sleep(2); continue
        if not r.get("ok") and r.get("error_code") == 429:
            time.sleep(int(r.get("parameters", {}).get("retry_after", 3)) + 1); continue
        return r
    return {"ok": False, "description": "network"}


def probe(chat, mid):
    """'none' 없음 / 'other' 남의 메시지 / 'own' 봇 메시지"""
    r = call("editMessageReplyMarkup", chat_id=chat, message_id=mid)
    d = (r.get("description") or "").lower()
    global NDIAG
    if NDIAG > 0:
        NDIAG -= 1; print(f"  [점검] #{mid}: ok={r.get('ok')} {d[:90]}")
    if r.get("ok") or "not modified" in d:
        return "own"
    if "not found" in d or "message_id_invalid" in d:
        return "none"
    return "other"


NDIAG = int(os.environ.get("DIAG", "0"))
MISS = int(os.environ.get("TOP_MISS", "60"))


def top_super(chat):
    hi, k = 0, 1
    while k < 10_000_000:
        if probe(chat, k) != "none": hi = k
        k *= 2
    miss, m, top = 0, hi, hi
    while miss < MISS:
        m += 1
        if probe(chat, m) != "none": top, miss = m, 0
        else: miss += 1
        time.sleep(0.03)
    print(f"  위쪽 끝 찾기: 거듭제곱 탐색 {hi} → 끝 {top}(연속 없음 {MISS}개에서 멈춤)")
    return top


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rooms", required=True); ap.add_argument("--file", required=True)
    ap.add_argument("--start", required=True); ap.add_argument("--end", required=True)
    ap.add_argument("--span", type=int, default=6000); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    t0 = dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc).timestamp()
    t1 = dt.datetime.fromisoformat(a.end).replace(tzinfo=dt.timezone.utc).timestamp()
    me = ROOMS[1]["id"]
    r = call("sendMessage", chat_id=me, text=f"[정리 시작] 잘못 나간 {a.file} 찾아서 지우는 중(방 {a.rooms})")
    box_top = r.get("result", {}).get("message_id", 0)
    print(f"내 방 시작 메시지 ok={r.get('ok')} (기준 번호 {box_top})")
    report = {}
    for n in [int(x) for x in a.rooms.split(",") if x.strip()]:
        chat = ROOMS[n]["id"]
        typ = call("getChat", chat_id=chat).get("result", {}).get("type", "?")
        top = top_super(chat) if typ in ("supergroup", "channel") else box_top
        found, own_seen, oldest = [], 0, None
        for mid in range(top, max(top - a.span, 0), -1):
            if probe(chat, mid) != "own":
                time.sleep(0.03); continue
            own_seen += 1
            f = call("forwardMessage", chat_id=me, from_chat_id=chat, message_id=mid, disable_notification=True)
            res = f.get("result", {})
            fn = (res.get("document") or {}).get("file_name", "")
            od = (res.get("forward_origin") or {}).get("date") or res.get("forward_date") or 0
            if res.get("message_id"):
                call("deleteMessage", chat_id=me, message_id=res["message_id"])  # 확인용 전달본 지움
            oldest = od
            print(f"  봇 메시지 #{mid}: 파일 '{fn or '(파일 아님)'}' · 보낸 시각 {dt.datetime.fromtimestamp(od, dt.timezone.utc):%m-%d %H:%M:%S} UTC" if od else f"  봇 메시지 #{mid}: 전달 확인 실패 {(f.get('description') or '')[:80]}")
            if fn == a.file and t0 <= od <= t1:
                if a.dry:
                    found.append((mid, "dry"))
                else:
                    d = call("deleteMessage", chat_id=chat, message_id=mid)
                    found.append((mid, "삭제" if d.get("ok") else "실패:" + (d.get("description") or "")))
            if od and od < t0 - 600:
                break
            time.sleep(0.05)
        report[n] = {"name": ROOMS[n]["name"], "type": typ, "found": found, "own_checked": own_seen}
        print(f"방 {n}번 {ROOMS[n]['name']}({typ}): 찾음 {len(found)}건 {[s for _, s in found]} · 봇 메시지 {own_seen}개 확인")
    lines = [f"방 {n}번 {v['name']}: " + (", ".join(s for _, s in v["found"]) or "못 찾음") for n, v in report.items()]
    call("sendMessage", chat_id=me, text="[정리 결과] " + a.file + "\n" + "\n".join(lines))
    json.dump(report, open("cleanup_report.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ok = all(v["found"] and all(s == "삭제" or s == "dry" for _, s in v["found"]) for v in report.values())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
