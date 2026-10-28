# -*- coding: utf-8 -*-
import requests, json
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
params = {"secid": "1.600105", "klt": 101, "fqt": 1, "beg": "20160101", "end": "20261027",
          "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"}
try:
    r = requests.get(url, params=params, headers=UA, timeout=30)
    print("A", r.status_code, len(r.text), r.text[:150])
except Exception as e:
    print("A failed", type(e).__name__, e)

try:
    r = requests.get(url, params=params, headers=UA, timeout=30, proxies={"http": None, "https": None})
    print("B", r.status_code, len(r.text))
except Exception as e:
    print("B failed", type(e).__name__)

# 试 http 与不同域名
for u in ["http://push2his.eastmoney.com/api/qt/stock/kline/get",
          "https://push2his.eastmoney.com/api/qt/stock/kline/get"]:
    try:
        r = requests.get(u, params=params, headers={**UA, "Referer": "https://quote.eastmoney.com/"}, timeout=30)
        print("C", u[:40], r.status_code, len(r.text))
        if r.status_code == 200:
            print("   ", r.text[:120])
    except Exception as e:
        print("C failed", u[:40], type(e).__name__)

import os
print("proxy env:", {k: v for k, v in os.environ.items() if "PROXY" in k.upper() or "proxy" in k})
