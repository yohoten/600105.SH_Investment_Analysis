# -*- coding: utf-8 -*-
import requests
UA = {"User-Agent": "Mozilla/5.0"}

def show(url, tag):
    try:
        j = requests.get(url, headers=UA, timeout=25).json()
        d = j.get("data", {})
        if isinstance(d, dict):
            for code, v in d.items():
                if isinstance(v, dict):
                    keys = list(v.keys())
                    arr = v.get("day") or v.get("qfqday") or []
                    print(f"{tag} {code} keys={keys} n={len(arr)} first={arr[0] if arr else None}")
                    return
        print(tag, "no data", str(j)[:150])
    except Exception as e:
        print(tag, "FAIL", type(e).__name__, e)

show("https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param=sh600105,day,2019-01-01,2019-12-31,640", "不复权")
show("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,2026-01-01,2026-10-27,640,qfq", "上证指数")
show("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000300,day,2026-01-01,2026-10-27,640,qfq", "沪深300")
show("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz399006,day,2026-01-01,2026-10-27,640,qfq", "创业板指")
show("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh601869,day,2026-01-01,2026-10-27,640,qfq", "长飞光纤")
