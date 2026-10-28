# -*- coding: utf-8 -*-
"""补抓：不复权日线 + 2016-2025 年报 PDF（巨潮）"""
from __future__ import annotations
import os, time, re
import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

# ---------------- 1. 不复权日线
print("[1] 不复权日线")
rows = []
for y in range(2016, 2027):
    url = ("https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param="
           f"sh600105,day,{y}-01-01,{y}-12-31,640")
    try:
        j = requests.get(url, headers=UA, timeout=30).json()
        arr = ((j.get("data") or {}).get("sh600105") or {}).get("day") or []
        rows.extend(arr)
    except Exception as e:
        print(f"   {y} 失败 {type(e).__name__}")
    time.sleep(0.25)

df = pd.DataFrame(rows).iloc[:, :6]
df.columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量(手)"]
for c in df.columns[1:]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.drop_duplicates(subset=["日期"]).sort_values("日期").reset_index(drop=True)
df["涨跌幅%"] = (df["收盘"].pct_change() * 100).round(3)
out = os.path.join(RAW, "market", "600105_日线_不复权.csv")
df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"   {len(df)} 行 {df['日期'].min()}~{df['日期'].max()} 末日收盘={df['收盘'].iloc[-1]}")

# ---------------- 2. 年报清单
print("\n[2] 巨潮年报清单（searchkey 检索）")
H = {**UA, "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
meta = []
for page in range(1, 5):
    r = requests.post("http://www.cninfo.com.cn/new/hisAnnouncement/query", headers=H,
                      data={"pageNum": page, "pageSize": 30, "column": "sse", "tabName": "fulltext",
                            "plate": "", "stock": "600105,gssh0600105", "searchkey": "年度报告",
                            "secDate": "", "tDate": "", "type": "category_ndbg_szsh", "trade": "",
                            "seDate": "2015-01-01~2026-12-31", "sortName": "", "sortType": "",
                            "isHLtitle": "false"}, timeout=30)
    anns = r.json().get("announcements") or []
    if not anns:
        break
    meta.extend(anns)
    time.sleep(0.5)

recs = []
for a in meta:
    t = re.sub(r"<[^>]+>", "", a["announcementTitle"])
    ts = pd.to_datetime(a["announcementTime"], unit="ms")
    recs.append({"标题": t, "公告日期": ts.strftime("%Y-%m-%d"),
                 "下载地址": "http://static.cninfo.com.cn/" + a["adjunctUrl"],
                 "公告ID": a["announcementId"], "大小KB": a.get("adjunctSize")})
m = pd.DataFrame(recs).drop_duplicates(subset=["公告ID"])
m.to_csv(os.path.join(RAW, "reports", "年报公告清单.csv"), index=False, encoding="utf-8-sig")
print(f"   共 {len(m)} 条公告")

# 仅取「XXXX年年度报告」正本
m["年度"] = m["标题"].str.extract(r"(20\d{2})年年度报告")[0]
nd = m[m["标题"].str.match(r"^永鼎股份20\d{2}年年度报告$", na=False)].copy()
nd["年度"] = nd["年度"].astype(int)
nd = nd.sort_values("年度")
print("   匹配到年度报告正本：", list(nd["年度"]))

# ---------------- 3. 下载
print("\n[3] 下载 PDF")
saved = []
for _, row in nd.iterrows():
    fn = f"永鼎股份_{row['年度']}年年度报告_披露{row['公告日期']}.pdf"
    path = os.path.join(RAW, "reports", fn)
    if os.path.exists(path) and os.path.getsize(path) > 500_000:
        saved.append((row["年度"], fn, os.path.getsize(path), "已存在"))
        print(f"   {row['年度']} 已存在")
        continue
    try:
        with requests.get(row["下载地址"], headers=UA, timeout=180, stream=True) as rr:
            rr.raise_for_status()
            with open(path, "wb") as f:
                for chunk in rr.iter_content(65536):
                    f.write(chunk)
        sz = os.path.getsize(path)
        saved.append((row["年度"], fn, sz, "新下载"))
        print(f"   {row['年度']} ✓ {sz/1024:.0f}KB")
    except Exception as e:
        print(f"   {row['年度']} ✗ {type(e).__name__} {e}")
    time.sleep(1.0)

pd.DataFrame(saved, columns=["年度", "文件", "字节", "方式"]).to_csv(
    os.path.join(RAW, "reports", "已下载年报清单.csv"), index=False, encoding="utf-8-sig")
print(f"\n完成，年报 PDF {len(saved)} 份")
