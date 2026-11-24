r"""텔레그램 파일 발송(리치봇). 토큰·방 번호는 깃허브 비밀값 TG_TOKEN·TG_CHATS(쉼표로 여러 방)에서만 읽고, 어디에도 원문 출력 안 함.
사용: python common/tg_send.py --file out/heatmap_KR.html --caption "■ 국내 히트맵 ..."
"""
import argparse, os, re, sys, time
import requests


def mask(s):
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", str(s))
    for chat in os.environ.get("TG_CHATS", "").split(","):
        if chat.strip():
            s = s.replace(chat.strip(), "***")
    return s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--file", required=True); ap.add_argument("--caption", default="")
    a = ap.parse_args()
    tok = os.environ.get("TG_TOKEN", "").strip()
    chats = [c.strip() for c in os.environ.get("TG_CHATS", "").split(",") if c.strip()]
    if not tok or not chats:
        print("TG_TOKEN/TG_CHATS 없음 → 발송 안 함"); return 1
    bad = 0
    for i, chat in enumerate(chats, 1):
        ok = False
        for k in range(3):
            try:
                with open(a.file, "rb") as f:
                    r = requests.post(f"https://api.telegram.org/bot{tok}/sendDocument", data={"chat_id": chat, "caption": a.caption[:1000]},
                                      files={"document": (os.path.basename(a.file), f, "text/html")}, timeout=120)
                ok = bool(r.ok and r.json().get("ok"))
                print(mask(f"방 {i}/{len(chats)} 발송 {'성공' if ok else '실패'} HTTP {r.status_code}"))
                if ok:
                    break
                if r.status_code == 429:
                    time.sleep(int(r.json().get("parameters", {}).get("retry_after", 5)) + 1); continue
                if r.status_code in (400, 403):
                    break  # 방 없음·권한 없음: 재시도 의미 없음
            except Exception as e:
                print(mask(f"방 {i}/{len(chats)} 발송 오류 {type(e).__name__}: {e}"))
            time.sleep(5 * (k + 1))
        bad += not ok
        time.sleep(1)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
