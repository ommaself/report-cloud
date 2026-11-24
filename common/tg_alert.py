r"""실패 알림 한 줄 → 내 방(rooms.json 1번). 토큰·방 번호는 가림. 사용: python common/tg_alert.py "히트맵 실패: KR 만들기" """
import json, os, re, sys
import requests

chat = str(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rooms.json"), encoding="utf-8"))["rooms"][0]["id"])
tok = os.environ.get("TG_TOKEN", "").strip()
msg = " ".join(sys.argv[1:])
if os.path.exists("out/send_fail.txt"):  # 발송 실패한 방 순서(rooms.json 순서)
    msg += "\n" + open("out/send_fail.txt", encoding="utf-8").read().strip()
msg = msg[:900]
if not tok or not chat:
    print("TG_TOKEN 없음 → 알림 안 함"); sys.exit(0)
try:
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": msg}, timeout=30)
    print(f"알림 {'성공' if r.ok else '실패'} HTTP {r.status_code}")
except Exception as e:
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", f"{type(e).__name__}: {e}")
    print("알림 오류 " + s.replace(chat, "***"))
