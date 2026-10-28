# -*- coding: utf-8 -*-
import requests, json
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# cninfo
try:
    r = requests.post("http://www.cninfo.com.cn/new/hisAnnouncement/query",
        headers={**UA, "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
                 "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        data={"pageNum": 1, "pageSize": 5, "column": "sse", "tabName": "fulltext", "plate": "",
              "stock": "600105,gssh0600105", "searchkey": "", "secDate": "", "tDate": "",
              "type": "category_ndbg_szsh", "trade": "", "seDate": "", "sortName": "", "sortType": "",
              "isHLtitle": "true"}, timeout=30)
    j = r.json()
    print("cninfo", r.status_code, j.get("totalRecordNum"))
    for a in (j.get("announcements") or [])[:3]:
        print("  ", a["announcementTitle"], a["adjunctUrl"])
except Exception as e:
    print("cninfo FAIL", type(e).__name__, e)

# chinamoney LPR
try:
    r = requests.post("https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis",
        headers={**UA, "Referer": "https://www.chinamoney.com.cn/chinese/bkccpr/"},
        data={"lang": "CN", "startDate": "2025-01-01", "endDate": "2026-12-31", "pageNum": 1, "pageSize": 40},
        timeout=25)
    print("lpr", r.status_code, len(r.text), r.text[:150])
except Exception as e:
    print("lpr FAIL", type(e).__name__, e)

# 腾讯 不复权 分年
for q in ["sh600105,day,2019-01-01,2019-12-31,640", "sh600105,day,2019-01-01,2019-12-31,640,qfq"]:
    try:
        r = requests.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=" + q, headers=UA, timeout=25)
        j = r.json()
        d = j["data"]["sh600105"]
        key = [k for k in d.keys()]
        print(q, "keys:", key, "n=", len(d.get("day") or d.get("qfqday") or []))
        rows = d.get("day") or d.get("qfqday") or []
        print("   first", rows[0] if rows else None)
    except Exception as e:
        print(q, "FAIL", type(e).__name__, e)
