# -*- coding: utf-8 -*-
"""宏观补充接口探测：利率、固投、社融、国债收益率"""
import json
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def probe(report_name, size=2):
    params = {
        "reportName": report_name,
        "columns": "ALL",
        "pageNumber": 1,
        "pageSize": size,
        "source": "WEB",
        "client": "WEB",
    }
    try:
        r = requests.get(BASE, params=params, headers=UA, timeout=25)
        j = r.json()
        data = j.get("result") or {}
        rows = data.get("data")
        print(f"[{report_name}] success={j.get('success')} msg={j.get('message')} count={len(rows) if rows else 0}")
        if rows:
            print("   keys:", list(rows[0].keys())[:14])
            print("   sample:", json.dumps(rows[0], ensure_ascii=False)[:260])
    except Exception as e:
        print(f"[{report_name}] ERROR {e.__class__.__name__}")


for rn in [
    "RPT_ECONOMY_FIXED_INVESTMENT",
    "RPT_ECONOMY_ASSET_INVEST",
    "RPT_ECONOMY_INVEST",
    "RPT_ECONOMY_LPR_RATE",
    "RPT_ECONOMY_INTEREST_RATE",
    "RPT_ECONOMY_DEPOSIT_RESERVE",
    "RPT_BOND_CHINA_YIELD",
    "RPT_BOND_YIELD",
    "RPT_ECONOMY_SOCIAL_FINANCE",
    "RPT_ECONOMY_SHIBOR",
    "RPT_ECONOMY_GDP_FOREIGN",
    "RPT_ECONOMY_CPI_YEAR",
]:
    probe(rn)

print("\n--- 国债收益率(中债) ---")
try:
    u = "https://yield.chinabond.com.cn/cbweb-mn/yc/searchYc"
    r = requests.get(u, headers=UA, timeout=20)
    print(r.status_code, len(r.text))
except Exception as e:
    print("chinabond ERROR", e)

print("\n--- 东方财富 利率一览 ---")
try:
    u = "https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_ECONOMY_INTEREST_RATE&columns=ALL&pageNumber=1&pageSize=2&source=WEB&client=WEB"
    r = requests.get(u, headers=UA, timeout=20)
    print(r.status_code, r.text[:300])
except Exception as e:
    print("ERR", e)
