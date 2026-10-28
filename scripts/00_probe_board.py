# -*- coding: utf-8 -*-
"""获取全部板块代码 + 试探中债收益率"""
import json
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

boards = []
for pn in range(1, 6):
    u = ("https://push2.eastmoney.com/api/qt/clist/get?pn=%d&pz=100&po=1&np=1&fltt=2&invt=2"
         "&fid=f3&fs=m%%3A90%%2Bt%%3A2&fields=f12,f14" % pn)
    j = requests.get(u, headers=UA, timeout=25).json()
    diff = (j.get("data") or {}).get("diff") or []
    if not diff:
        break
    boards.extend(diff)

print("boards:", len(boards))
for b in boards:
    if any(k in str(b.get("f14")) for k in ["通信", "光", "电缆", "电网", "电子", "半导体"]):
        print("  ", b)

print("\n--- chinabond 尝试 ---")
for u in [
    "https://yield.chinabond.com.cn/cbweb-mn/yield_main/getYieldDataJson?workTime=2026-10-24&yqqxN=N&yqqxU=Y&zblx=1&zrlx=1",
    "https://yield.chinabond.com.cn/cbweb-mn/yield_main/getYieldDataForYear?workTime=2026-10-24&qxmc=中债国债到期收益率&yqqxN=N&yqqxU=Y&zblx=1&zrlx=1&wrjxCBFlag=0",
]:
    try:
        r = requests.get(u, headers=UA, timeout=20)
        print(r.status_code, len(r.text), r.text[:200].replace("\n", " "))
    except Exception as e:
        print("ERR", e)
