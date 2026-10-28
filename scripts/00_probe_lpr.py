# -*- coding: utf-8 -*-
"""探测 LPR 多年份、行业板块代码"""
import json
import requests

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://www.chinamoney.com.cn/chinese/bkccpr/",
}

def lpr(year):
    r = requests.post(
        "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis",
        headers=UA,
        data={"lang": "CN", "startDate": f"{year}-01-01", "endDate": f"{year}-12-31", "pageNum": 1, "pageSize": 40},
        timeout=25,
    )
    j = r.json()
    return j.get("records"), (j.get("data") or {})

for y in [2019, 2020, 2022, 2026]:
    recs, meta = lpr(y)
    print(y, "n=", len(recs) if recs else 0, "| meta:", str(meta)[:120])
    if recs:
        print("   first:", recs[0], " last:", recs[-1])

print("\n--- 板块查询 ---")
try:
    u = ("https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=200&po=1&np=1&fltt=2&invt=2"
         "&fid=f3&fs=m%3A90%2Bt%3A2&fields=f12,f14")
    r = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
    j = r.json()
    items = (j.get("data") or {}).get("diff") or []
    hits = [i for i in items if any(k in str(i.get("f14")) for k in ["通信", "光", "电网", "电缆"])]
    print("total boards:", len(items))
    for h in hits:
        print("  ", h)
except Exception as e:
    print("ERR", e)
