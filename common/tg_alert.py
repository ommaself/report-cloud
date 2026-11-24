r"""실패 알림 한 줄 → 내 방(비밀값 TG_ALERT_CHAT). 토큰·방 번호는 가림. 사용: python common/tg_alert.py "히트맵 실패: KR 만들기" """
import os, re, sys
import requests

tok, chat = os.environ.get("TG_TOKEN", "").strip(), os.environ.get("TG_ALERT_CHAT", "").strip()
msg = " ".join(sys.argv[1:])[:900]
if not tok or not chat:
    print("TG_TOKEN/TG_ALERT_CHAT 없음 → 알림 안 함"); sys.exit(0)
try:
    r = requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": msg}, timeout=30)
    print(f"알림 {'성공' if r.ok else '실패'} HTTP {r.status_code}")
except Exception as e:
    s = re.sub(r"bot\d+:[A-Za-z0-9_-]+|\b\d{6,}:[A-Za-z0-9_-]{30,}", "bot***", f"{type(e).__name__}: {e}")
    print("알림 오류 " + s.replace(chat, "***"))
