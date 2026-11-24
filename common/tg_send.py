r"""텔레그램 파일 발송(리치봇). 토큰은 깃허브 비밀값 TG_TOKEN에서만, 방은 common/rooms.json(--rooms 1,2,… 순서 번호)에서 읽고, 어디에도 원문 출력 안 함.
사용: python common/tg_send.py --file out/heatmap_KR.html --caption "■ 국내 히트맵 ..."
"""
import argparse, json, os, re, sys, time
import requests

ROOMS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rooms.json"), encoding="utf-8"))["rooms"]


def mask(s):
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", str(s))
    for r in ROOMS:
        s = s.replace(str(r["id"]), "***")
    return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--file", required=True); ap.add_argument("--caption", default=""); ap.add_argument("--rooms", default="1")
    a = ap.parse_args()
    tok = os.environ.get("TG_TOKEN", "").strip()
    want = [int(x) for x in a.rooms.split(",") if x.strip()]
    chats = [str(r["id"]) for n in want for r in ROOMS if r["n"] == n]
    if not tok or not chats:
        print("TG_TOKEN 없음 또는 방 없음 → 발송 안 함"); return 1
    if not re.fullmatch(r"\d{6,}:[A-Za-z0-9_-]{30,}", tok):  # 값은 안 찍고 모양만
        print(f"TG_TOKEN 모양이 봇 토큰이 아님(길이 {len(tok)}, 콜론 {'있음' if ':' in tok else '없음'}) → 비밀값 다시 넣기 필요")
    bad = 0
    for i, chat in zip(want, chats):
        ok = False
        for k in range(3):
            try:
                with open(a.file, "rb") as f:
                    r = requests.post(f"https://api.telegram.org/bot{tok}/sendDocument", data={"chat_id": chat, "caption": a.caption[:1000]},
                                      files={"document": (os.path.basename(a.file), f, "text/html")}, timeout=120)
                ok = bool(r.ok and r.json().get("ok"))
                print(mask(f"방 {i}번 발송 {'성공' if ok else '실패'} HTTP {r.status_code}"))
                if ok:
                    break
                if r.status_code == 429:
                    time.sleep(int(r.json().get("parameters", {}).get("retry_after", 5)) + 1); continue
                if r.status_code in (400, 403):
                    break  # 방 없음·권한 없음: 재시도 의미 없음
            except Exception as e:
                print(mask(f"방 {i}번 발송 오류 {type(e).__name__}: {e}"))
            time.sleep(5 * (k + 1))
        if not ok:
            bad += 1
            with open(os.environ.get("TG_FAIL_FILE", "out/send_fail.txt"), "a", encoding="utf-8") as f:
                f.write(f"{os.path.basename(a.file)} 방 {i}번 실패\n")  # 방 번호(순서)만, 실제 방 ID 안 씀
        time.sleep(1)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
