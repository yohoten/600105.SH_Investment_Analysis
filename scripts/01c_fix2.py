# -*- coding: utf-8 -*-
"""补抓 2015-2020 年报正本"""
import os, re, time
import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "reports")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}
H = {**UA, "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

meta = []
for page in range(1, 8):
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
    time.sleep(0.4)

recs, seen = [], set()
for a in meta:
    if a["announcementId"] in seen:
        continue
    seen.add(a["announcementId"])
    t = re.sub(r"<[^>]+>", "", a["announcementTitle"]).strip()
    recs.append({"标题": t, "公告日期": pd.to_datetime(a["announcementTime"], unit="ms").strftime("%Y-%m-%d"),
                 "下载地址": "http://static.cninfo.com.cn/" + a["adjunctUrl"], "公告ID": a["announcementId"]})
m = pd.DataFrame(recs)
m.to_csv(os.path.join(RAW, "年报公告清单_全量.csv"), index=False, encoding="utf-8-sig")
print("公告总数:", len(m))

m["年度"] = m["标题"].str.extract(r"(20\d{2})年年度报告$")[0]
nd = m[m["标题"].str.match(r"^(永鼎股份)?20\d{2}年年度报告$", na=False)].copy()
nd["年度"] = nd["年度"].astype(int)
# 同一年度保留最早披露的一份正本
nd = nd.sort_values(["年度", "公告日期"]).drop_duplicates(subset=["年度"], keep="first")
print("正本年度:", list(nd["年度"]))

saved = []
for _, row in nd.iterrows():
    fn = f"永鼎股份_{row['年度']}年年度报告_披露{row['公告日期']}.pdf"
    path = os.path.join(RAW, fn)
    if os.path.exists(path) and os.path.getsize(path) > 500_000:
        print(f"  {row['年度']} 已存在"); continue
    try:
        with requests.get(row["下载地址"], headers=UA, timeout=180, stream=True) as rr:
            rr.raise_for_status()
            with open(path, "wb") as f:
                for chunk in rr.iter_content(65536):
                    f.write(chunk)
        print(f"  {row['年度']} ✓ {os.path.getsize(path)/1024:.0f}KB")
        saved.append((row["年度"], fn, os.path.getsize(path)))
    except Exception as e:
        print(f"  {row['年度']} ✗ {e}")
    time.sleep(1.0)

lst = sorted([(f, os.path.getsize(os.path.join(RAW, f))) for f in os.listdir(RAW) if f.lower().endswith(".pdf")])
print("\n现有 PDF:")
for f, s in lst:
    print(f"  {f}  {s/1024/1024:.1f}MB")
