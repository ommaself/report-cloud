r"""텔레그램 파일 발송(리치봇). 토큰·방 번호는 깃허브 비밀값 TG_TOKEN·TG_CHAT에서만 읽고, 어디에도 원문 출력 안 함.
사용: python common/tg_send.py --file out/heatmap_KR.html --caption "■ 국내 히트맵 ..."
"""
import argparse, os, re, sys, time
import requests


def mask(s):
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", str(s))
    chat = os.environ.get("TG_CHAT", "")
    return s.replace(chat, "***") if chat else s


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--file", required=True); ap.add_argument("--caption", default="")
    a = ap.parse_args()
    tok, chat = os.environ.get("TG_TOKEN", "").strip(), os.environ.get("TG_CHAT", "").strip()
    if not tok or not chat:
        print("TG_TOKEN/TG_CHAT 없음 → 발송 안 함"); return 1
    for k in range(3):
        try:
            with open(a.file, "rb") as f:
                r = requests.post(f"https://api.telegram.org/bot{tok}/sendDocument", data={"chat_id": chat, "caption": a.caption[:1000]},
                                  files={"document": (os.path.basename(a.file), f, "text/html")}, timeout=120)
            ok = r.ok and r.json().get("ok")
            print(mask(f"발송 {'성공' if ok else '실패'} {os.path.basename(a.file)} HTTP {r.status_code}"))
            if ok:
                return 0
            if r.status_code == 429:
                time.sleep(int(r.json().get("parameters", {}).get("retry_after", 5)) + 1); continue
        except Exception as e:
            print(mask(f"발송 오류 {type(e).__name__}: {e}"))
        time.sleep(5 * (k + 1))
    return 1


if __name__ == "__main__":
    sys.exit(main())
