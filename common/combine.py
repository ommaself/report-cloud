r"""국장·미장 히트맵 HTML 2개를 파일 하나로(11/25 대표 A안: 화면 위 [미국][국내] 버튼으로 선택). 텔레 1건 발송·사이드 Artifact 공용.
각 원본은 <script type="text/plain">에 그대로 넣고, 누를 때 iframe srcdoc으로 띄움(원본 화면·차트 그대로).
사용: python common/combine.py out/heatmap_US.html out/heatmap_KR.html out/heatmap.html
"""
import re, sys

us, kr, dst = sys.argv[1:4]
ESC = "</scr_ESC_ipt"  # 원본 안의 </script 를 잠시 바꿔 둠(JS에서 되돌림)


def load(p):
    s = open(p, encoding="utf-8").read()
    assert ESC not in s
    return re.sub(r"</script", ESC, s, flags=re.I)


def asof(p):
    m = re.search(r"기준 (\d{4}-\d{2}-\d{2}) 종가", open(p, encoding="utf-8").read())
    return m.group(1) if m else "?"


du, dk = asof(us), asof(kr)
page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>시장 히트맵 (미국 {du[5:]} · 국내 {dk[5:]})</title>
<style>html,body{{margin:0;height:100%;background:#111;color:#eee;font-family:system-ui,sans-serif}}
#bar{{display:flex;gap:6px;padding:6px 8px;align-items:center;background:#1b1b1b;border-bottom:1px solid #333}}
#bar button{{font-size:15px;padding:6px 14px;border-radius:6px;border:1px solid #555;background:#222;color:#ddd;cursor:pointer}}
#bar button.on{{background:#2f6fde;border-color:#2f6fde;color:#fff;font-weight:600}}
#bar span{{font-size:12px;color:#999;margin-left:auto}}
iframe{{border:0;width:100%;height:calc(100% - 46px);display:none;background:#fff}}</style></head><body>
<div id="bar"><button id="bUS" onclick="show('US')">미국</button><button id="bKR" onclick="show('KR')">국내</button>
<span>미국 {du} · 국내 {dk} 종가</span></div>
<iframe id="fUS" title="미국 히트맵"></iframe><iframe id="fKR" title="국내 히트맵"></iframe>
<script type="text/plain" id="sUS">{load(us)}</script>
<script type="text/plain" id="sKR">{load(kr)}</script>
<script>
function show(m){{for(const k of ["US","KR"]){{const f=document.getElementById("f"+k);
if(k===m&&!f.dataset.on){{f.srcdoc=document.getElementById("s"+k).textContent.split("{ESC}").join("</scr"+"ipt");f.dataset.on=1}}
f.style.display=k===m?"block":"none";document.getElementById("b"+k).className=k===m?"on":""}}
try{{history.replaceState(null,"","#"+m)}}catch(e){{}}}}
show(location.hash==="#KR"?"KR":"US");
</script></body></html>"""
open(dst, "w", encoding="utf-8").write(page)
print(f"합본 {dst}: 미국 {du} · 국내 {dk}")
