# -*- coding: utf-8 -*-
"""宏观数据接口探测"""
import json
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def probe(report_name, columns="ALL", extra="", size=3):
    params = {
        "reportName": report_name,
        "columns": columns,
        "pageNumber": 1,
        "pageSize": size,
        "sortColumns": "",
        "sortTypes": "",
        "source": "WEB",
        "client": "WEB",
    }
    url = BASE
    if extra:
        params["filter"] = extra
    try:
        r = requests.get(url, params=params, headers=UA, timeout=25)
        j = r.json()
        ok = j.get("success")
        data = (j.get("result") or {})
        rows = data.get("data")
        print(f"[{report_name}] success={ok} pages={data.get('pages')} count={len(rows) if rows else 0}")
        if rows:
            print("   keys:", list(rows[0].keys())[:12])
            print("   sample:", json.dumps(rows[0], ensure_ascii=False)[:280])
    except Exception as e:
        print(f"[{report_name}] ERROR {e.__class__.__name__}: {e}")


for rn in [
    "RPT_ECONOMY_GDP",
    "RPT_ECONOMY_CPI",
    "RPT_ECONOMY_PPI",
    "RPT_ECONOMY_PMI",
    "RPT_ECONOMY_CURRENCY_SUPPLY",
    "RPT_ECONOMY_FIXED_INVEST",
    "RPT_ECONOMY_TOTAL_RETAIL",
    "RPT_ECONOMY_LOAN",
    "RPT_ECONOMY_LPR",
    "RPT_ECONOMY_GNP",
    "RPT_ECONOMY_SOCIAL_FINANCING",
]:
    probe(rn)
