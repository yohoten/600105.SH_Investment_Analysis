# -*- coding: utf-8 -*-
"""探测巨潮年报检索参数组合"""
import requests, json, pandas as pd

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
      "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
      "Accept": "*/*"}

def q(**over):
    data = {"pageNum": 1, "pageSize": 50, "column": "sse", "tabName": "fulltext", "plate": "",
            "stock": "600105,gssh0600105", "searchkey": "", "secDate": "", "tDate": "",
            "type": "category_ndbg_szsh", "trade": "", "seDate": "", "sortName": "", "sortType": "",
            "isHLtitle": "true"}
    data.update(over)
    r = requests.post("http://www.cninfo.com.cn/new/hisAnnouncement/query", headers=UA, data=data, timeout=30)
    j = r.json()
    anns = j.get("announcements") or []
    print(f"{over} -> total={j.get('totalRecordNum')} n={len(anns)}")
    for a in anns[:6]:
        print("    ", a["announcementTitle"], a["adjunctUrl"])
    return anns

q(searchkey="年度报告", seDate="2016-01-01~2026-12-31")
q(searchkey="年度报告")
q(seDate="2016-01-01~2026-12-31", type="category_ndbg_szsh")
q(seDate="2016-01-01~2026-12-31", type="category_ndbg_szsh", searchkey="")
