# -*- coding: utf-8 -*-
"""补抓指数日线"""
import os, time
import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "market")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

frames = []
for code, nm in [("sh000001", "上证指数"), ("sh000300", "沪深300"), ("sz399006", "创业板指")]:
    rows = []
    for y in range(2016, 2027):
        url = ("https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param="
               f"{code},day,{y}-01-01,{y}-12-31,640")
        try:
            j = requests.get(url, headers=UA, timeout=30).json()
            arr = ((j.get("data") or {}).get(code) or {}).get("day") or []
            rows.extend(arr)
        except Exception as e:
            print(f"  {code} {y} 失败 {type(e).__name__}")
        time.sleep(0.2)
    df = pd.DataFrame(rows).iloc[:, :6]
    df.columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量(手)"]
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.drop_duplicates(subset=["日期"]).sort_values("日期")
    df["涨跌幅%"] = (df["收盘"].pct_change() * 100).round(3)
    df["指数"] = nm
    frames.append(df)
    print(f"  {nm}: {len(df)} 行 {df['日期'].min()}~{df['日期'].max()}")

out = pd.concat(frames)
out.to_csv(os.path.join(RAW, "指数日线.csv"), index=False, encoding="utf-8-sig")
print("已保存", out.shape)
