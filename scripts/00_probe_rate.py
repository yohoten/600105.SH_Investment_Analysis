# -*- coding: utf-8 -*-
"""探测 chinamoney LPR 与中债国债收益率"""
import json
import requests

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Referer": "https://www.chinamoney.com.cn/chinese/bkccpr/",
    "Accept": "application/json, text/plain, */*",
}

def try_get(name, url, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=25, **kw)
        print(f"[{name}] {r.status_code} len={len(r.text)} head={r.text[:240]}")
    except Exception as e:
        print(f"[{name}] ERR {e.__class__.__name__}")

try_post = lambda name, url, data: (
    lambda r: print(f"[{name}] {r.status_code} len={len(r.text)} head={r.text[:300]}")
)(requests.post(url, headers=UA, data=data, timeout=25))

# LPR 历史
try_post(
    "LPR-HIS",
    "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-shibor/LprHis",
    {"lang": "CN", "startDate": "2019-08-20", "endDate": "2026-10-27", "pageNum": 1, "pageSize": 15},
)
try_post(
    "LPR-HIS2",
    "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis",
    {"lang": "CN", "startDate": "2019-08-20", "endDate": "2026-10-27", "pageNum": 1, "pageSize": 15},
)
# 国债收益率曲线
try_post(
    "CURVE",
    "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ChinabondYieldCurve",
    {"lang": "CN", "startDate": "2026-10-01", "endDate": "2026-10-27", "pageNum": 1, "pageSize": 10},
)
try_get(
    "CB-YIELD-YEARS",
    "https://yield.chinabond.com.cn/cbweb-mn/yield_main/getYieldDataForYears?workTime=2026-10-24&qxmc=%E4%B8%AD%E5%80%BA%E5%9B%BD%E5%80%BA%E5%88%B0%E6%9C%9F%E6%94%B6%E7%9B%8A%E7%8E%87&yqqxN=N&yqqxU=Y&zblx=1&zrlx=1&wrjxCBFlag=0",
)
