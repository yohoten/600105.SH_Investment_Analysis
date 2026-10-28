# -*- coding: utf-8 -*-
"""
永鼎股份(600105.SH) 投资分析 —— 数据抓取主脚本 v2
覆盖期间：2016-01-01 ~ 2026-10-27（日行情）；2015-12-31 ~ 2026-09-30（财报，含2015年末作期初均值）

数据源与分工（均经连通性验证）：
  1) 腾讯财经 web.ifzq.gtimg.cn   日K线（前复权 + 不复权）、指数、同业行情
  2) 东方财富 datacenter           F10 三大报表 / 核心指标 / 主营构成 / 宏观 / 分红
  3) 中国货币网 chinamoney         LPR 报价
  4) 巨潮资讯网 cninfo             年度报告 / 季度报告 PDF 及公告清单

输出：data/raw/** 与抓取日志 data/raw/_fetch_log.csv
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
for sub in ["market", "financials", "indicators", "peers", "macro", "industry", "reports", "_json"]:
    os.makedirs(os.path.join(RAW, sub), exist_ok=True)

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
DC = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
LOG: list[dict] = []


def log(name: str, rows: int, status: str, note: str = ""):
    LOG.append({"接口/文件": name, "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "记录数": rows, "状态": status, "备注": note})
    flag = "OK  " if status == "成功" else "FAIL"
    print(f"  [{flag}] {name} → {rows} 行 {note}")


def get_json(url: str, params=None, tries: int = 4, sleep: float = 1.0, method: str = "GET", **kw):
    last = None
    for i in range(tries):
        try:
            fn = requests.get if method == "GET" else requests.post
            r = fn(url, params=params if method == "GET" else None, headers={**UA, **kw.pop("headers", {})},
                   timeout=35, **kw)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last = e.__class__.__name__
        time.sleep(sleep * (i + 1))
    raise RuntimeError(f"{url} ({last})")


# ------------------------------------------------------------------ 行情（腾讯）
TENCENT_K = "https://web.ifzq.gtimg.cn/appstock/app/{kind}/get"
YEARS = list(range(2016, 2027))


def tx_kline(code: str, qfq: bool = True) -> pd.DataFrame:
    """按年窗口抓取，规避单次 640 条上限"""
    out = []
    tail = "fqkline/get" if qfq else "kline/kline"
    for y in YEARS:
        beg, end = f"{y}-01-01", f"{y}-12-31"
        url = f"https://web.ifzq.gtimg.cn/appstock/app/{tail}?param={code},day,{beg},{end},640{',qfq' if qfq else ''}"
        try:
            j = get_json(url)
            node = (j.get("data") or {}).get(code) or {}
            arr = node.get("qfqday") or node.get("day") or []
            out.extend(arr)
        except Exception as e:  # noqa: BLE001
            log(f"{code} {y} 行情", 0, "失败", str(e)[:50])
        time.sleep(0.25)
    if not out:
        return pd.DataFrame()
    df = pd.DataFrame(out)
    df = df.iloc[:, :6]
    df.columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量(手)"]
    for c in ["开盘", "收盘", "最高", "最低", "成交量(手)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.drop_duplicates(subset=["日期"]).sort_values("日期").reset_index(drop=True)
    df["成交额(元)"] = df["收盘"] * df["成交量(手)"] * 100
    df["涨跌幅%"] = (df["收盘"].pct_change() * 100).round(3)
    return df


def main_market():
    print("\n[1/6] 日行情（腾讯财经）")
    for qfq, tag in [(True, "前复权"), (False, "不复权")]:
        df = tx_kline("sh600105", qfq=qfq)
        df.to_csv(os.path.join(RAW, "market", f"600105_日线_{tag}.csv"), index=False, encoding="utf-8-sig")
        log(f"600105 日线({tag})", len(df), "成功" if len(df) else "失败",
            f"{df['日期'].min()}~{df['日期'].max()}" if len(df) else "")

    frames = []
    for code, nm in [("sh000001", "上证指数"), ("sh000300", "沪深300"), ("sz399006", "创业板指")]:
        d = tx_kline(code, qfq=False)
        if len(d):
            d["指数"] = nm
            frames.append(d)
            log(f"指数 {nm}", len(d), "成功")
    if frames:
        pd.concat(frames).to_csv(os.path.join(RAW, "market", "指数日线.csv"), index=False, encoding="utf-8-sig")

    # 实时快照（用于交叉校验收盘价与市值）
    try:
        r = requests.get("https://qt.gtimg.cn/q=sh600105", headers=UA, timeout=20)
        r.encoding = "gbk"
        txt = r.text
        arr = txt.split("=")[1].strip('";\n').split("~")
        snap = {
            "抓取时间": datetime.now().isoformat(),
            "原始字段": arr,
            "名称": arr[1], "代码": arr[2], "最新价": arr[3], "昨收": arr[4], "今开": arr[5],
            "涨跌": arr[31], "涨跌幅%": arr[32], "最高": arr[33], "最低": arr[34],
            "成交额(万元)": arr[37], "换手率%": arr[38], "PE_TTM": arr[39],
            "流通市值(亿)": arr[44], "总市值(亿)": arr[45], "PB": arr[46],
        }
        with open(os.path.join(RAW, "market", "实时快照.json"), "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        log("实时快照", 1, "成功", f"最新价={snap['最新价']} 总市值={snap['总市值(亿)']}亿 PE={snap['PE_TTM']} PB={snap['PB']}")
    except Exception as e:  # noqa: BLE001
        log("实时快照", 0, "失败", str(e)[:60])


# ------------------------------------------------------------------ 财报（东财）
STATEMENTS = {"资产负债表": "RPT_F10_FINANCE_GBALANCE",
              "利润表": "RPT_F10_FINANCE_GINCOME",
              "现金流量表": "RPT_F10_FINANCE_GCASHFLOW"}


def sec_of(code: str) -> str:
    return f"{code}.SH" if code[0] in "69" else f"{code}.SZ"


def fetch_all_pages(report_name: str, filt: str, size: int = 500):
    params = {"reportName": report_name, "columns": "ALL", "filter": filt, "pageNumber": 1,
              "pageSize": size, "source": "HSF10", "client": "PC"}
    j = get_json(DC, params)
    if not j.get("success"):
        raise RuntimeError(j.get("message", "unknown"))
    res = j.get("result") or {}
    rows = list(res.get("data") or [])
    for p in range(2, (res.get("pages") or 1) + 1):
        pp = dict(params, pageNumber=p)
        jj = get_json(DC, pp)
        rows.extend(((jj.get("result") or {}).get("data")) or [])
        time.sleep(0.3)
    return rows


def fetch_statements(code: str):
    sec = sec_of(code)
    for nm, rn in STATEMENTS.items():
        try:
            rows = fetch_all_pages(rn, f'(SECUCODE="{sec}")(REPORT_DATE>=\'2015-12-31\')')
            df = pd.DataFrame(rows).drop(columns=[c for c in (rows[0].keys() if rows else []) if c.startswith("_")],
                                         errors="ignore")
            df.to_csv(os.path.join(RAW, "financials", f"{code}_{nm}.csv"), index=False, encoding="utf-8-sig")
            log(f"{code} {nm}", len(df), "成功" if len(df) else "失败")
        except Exception as e:  # noqa: BLE001
            log(f"{code} {nm}", 0, "失败", str(e)[:60])
        time.sleep(0.4)


def fetch_indicators(code: str):
    try:
        rows = fetch_all_pages("RPT_F10_FINANCE_MAINFINADATA", f'(SECUCODE="{sec_of(code)}")')
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(RAW, "indicators", f"{code}_核心财务指标.csv"), index=False, encoding="utf-8-sig")
        log(f"{code} 核心财务指标", len(df), "成功")
    except Exception as e:  # noqa: BLE001
        log(f"{code} 核心财务指标", 0, "失败", str(e)[:60])


def fetch_mainop(code: str):
    for rn in ["RPT_F10_FN_MAINOP", "RPT_F10_FN_MAINOPINCOME"]:
        try:
            rows = fetch_all_pages(rn, f'(SECUCODE="{sec_of(code)}")')
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(os.path.join(RAW, "financials", f"{code}_主营构成.csv"), index=False, encoding="utf-8-sig")
                log(f"{code} 主营构成", len(df), "成功", f"{df['REPORT_DATE'].nunique()} 期")
                return
        except Exception as e:  # noqa: BLE001
            msg = str(e)[:50]
    log(f"{code} 主营构成", 0, "失败", msg if "msg" in dir() else "")


def fetch_dividend(code: str):
    for rn in ["RPT_SHAREBONUS_DET", "RPT_F10_DIVIDEND"]:
        try:
            rows = fetch_all_pages(rn, f'(SECURITY_CODE="{code}")' if rn == "RPT_SHAREBONUS_DET" else f'(SECUCODE="{sec_of(code)}")')
            if rows:
                pd.DataFrame(rows).to_csv(os.path.join(RAW, "financials", f"{code}_分红送配.csv"),
                                          index=False, encoding="utf-8-sig")
                log(f"{code} 分红送配", len(rows), "成功")
                return
        except Exception as e:  # noqa: BLE001
            pass
    log(f"{code} 分红送配", 0, "失败", "接口不可用")


# ------------------------------------------------------------------ 同业
PEERS = {"601869": "长飞光纤", "600487": "亨通光电", "600522": "中天科技",
         "600498": "烽火通信", "300308": "中际旭创", "002491": "通鼎互联"}


def main_peers():
    print("\n[3/6] 同业公司")
    frames, inds = [], []
    for code, nm in PEERS.items():
        tx = ("sh" if code[0] in "69" else "sz") + code
        d = tx_kline(tx, qfq=True)
        if len(d):
            d["名称"] = nm
            frames.append(d)
            log(f"同业 {code} {nm} 日线", len(d), "成功")
        try:
            rows = fetch_all_pages("RPT_F10_FINANCE_MAINFINADATA", f'(SECUCODE="{sec_of(code)}")')
            if rows:
                dd = pd.DataFrame(rows)
                dd["名称"] = nm
                inds.append(dd)
                log(f"同业 {code} {nm} 指标", len(dd), "成功")
        except Exception as e:  # noqa: BLE001
            log(f"同业 {code} {nm} 指标", 0, "失败", str(e)[:50])
        time.sleep(0.3)
    if frames:
        pd.concat(frames).to_csv(os.path.join(RAW, "peers", "同业日线_前复权.csv"), index=False, encoding="utf-8-sig")
    if inds:
        pd.concat(inds).to_csv(os.path.join(RAW, "peers", "同业核心指标.csv"), index=False, encoding="utf-8-sig")

    for code in PEERS:
        fetch_statements(code)


# ------------------------------------------------------------------ 宏观
MACRO = {"GDP": "RPT_ECONOMY_GDP", "CPI": "RPT_ECONOMY_CPI", "PPI": "RPT_ECONOMY_PPI",
         "制造业PMI": "RPT_ECONOMY_PMI", "货币供应量": "RPT_ECONOMY_CURRENCY_SUPPLY",
         "社会消费品零售总额": "RPT_ECONOMY_TOTAL_RETAIL", "固定资产投资": "RPT_ECONOMY_ASSET_INVEST",
         "存款准备金率": "RPT_ECONOMY_DEPOSIT_RESERVE"}


def main_macro():
    print("\n[4/6] 宏观数据")
    for nm, rn in MACRO.items():
        try:
            rows = fetch_all_pages(rn, "")
            df = pd.DataFrame(rows)
            if "REPORT_DATE" in df.columns:
                df = df[df["REPORT_DATE"] >= "2014-01-01"]
            df.to_csv(os.path.join(RAW, "macro", f"{nm}.csv"), index=False, encoding="utf-8-sig")
            rng = f"{df['REPORT_DATE'].min()[:10]}~{df['REPORT_DATE'].max()[:10]}" if len(df) else ""
            log(f"宏观 {nm}", len(df), "成功" if len(df) else "失败", rng)
        except Exception as e:  # noqa: BLE001
            log(f"宏观 {nm}", 0, "失败", str(e)[:60])
        time.sleep(0.4)

    try:
        r = requests.post("https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis",
                          headers={**UA, "Referer": "https://www.chinamoney.com.cn/chinese/bkccpr/"},
                          data={"lang": "CN", "startDate": "2025-01-01", "endDate": "2026-12-31",
                                "pageNum": 1, "pageSize": 40}, timeout=25)
        recs = r.json().get("records") or []
        df = pd.DataFrame([{"日期": x.get("showDateCN"), "LPR1Y": float(x.get("1Y")),
                            "LPR5Y": float(x.get("5Y"))} for x in recs])
        df["日期"] = pd.to_datetime(df["日期"], format="%Y年%m月%d日", errors="coerce")
        df = df.sort_values("日期")
        df.to_csv(os.path.join(RAW, "macro", "LPR贷款市场报价利率.csv"), index=False, encoding="utf-8-sig")
        log("宏观 LPR（近一年明细）", len(df), "成功", f"1Y={df['LPR1Y'].iloc[-1]}% 5Y={df['LPR5Y'].iloc[-1]}%")
    except Exception as e:  # noqa: BLE001
        log("宏观 LPR", 0, "失败", str(e)[:60])


# ------------------------------------------------------------------ 公告
def main_reports():
    print("\n[5/6] 定期报告 PDF（巨潮资讯网）")
    meta = []
    for type_code, type_name, pages in [("category_ndbg_szsh", "年度报告", 2), ("category_yjdbg_szsh", "季度报告", 3)]:
        for page in range(1, pages + 1):
            try:
                r = requests.post(
                    "http://www.cninfo.com.cn/new/hisAnnouncement/query",
                    headers={**UA, "Referer": "http://www.cninfo.com.cn/new/commonUrl?url=disclosure/list/notice",
                             "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                    data={"pageNum": page, "pageSize": 30, "column": "sse", "tabName": "fulltext", "plate": "",
                          "stock": "600105,gssh0600105", "searchkey": "", "secDate": "", "tDate": "",
                          "type": type_code, "trade": "", "seDate": "", "sortName": "", "sortType": "",
                          "isHLtitle": "true"}, timeout=30)
                anns = r.json().get("announcements") or []
            except Exception as e:  # noqa: BLE001
                log(f"巨潮 {type_name} 列表p{page}", 0, "失败", str(e)[:50])
                break
            if not anns:
                break
            for a in anns:
                ts = pd.to_datetime(a["announcementTime"], unit="ms")
                meta.append({"类别": type_name, "代码": a.get("secCode"), "名称": a.get("secName"),
                             "标题": a.get("announcementTitle"), "公告日期": ts.strftime("%Y-%m-%d"),
                             "大小KB": a.get("adjunctSize"),
                             "下载地址": "http://static.cninfo.com.cn/" + a.get("adjunctUrl", ""),
                             "公告ID": a.get("announcementId")})
            time.sleep(0.5)

    mdf = pd.DataFrame(meta).drop_duplicates(subset=["公告ID"])
    if mdf.empty:
        log("巨潮 公告清单", 0, "失败", "无返回")
        return
    mdf.to_csv(os.path.join(RAW, "reports", "公告清单.csv"), index=False, encoding="utf-8-sig")
    log("巨潮 公告清单", len(mdf), "成功", f"{mdf['公告日期'].min()}~{mdf['公告日期'].max()}")

    nd = mdf[(mdf["类别"] == "年度报告") & mdf["标题"].str.contains("年度报告", na=False)
             & ~mdf["标题"].str.contains("摘要|英文|已取消|取消|专项", na=False)].copy()
    nd["年度"] = nd["标题"].str.extract(r"(\d{4})\s*年年度报告")[0]
    nd = nd.dropna(subset=["年度"]).sort_values("年度")
    nd = nd[nd["年度"].astype(int).between(2015, 2025)]

    saved = []
    for _, row in nd.iterrows():
        fn = f"永鼎股份_{row['年度']}年年度报告_披露{row['公告日期']}.pdf"
        path = os.path.join(RAW, "reports", fn)
        if os.path.exists(path) and os.path.getsize(path) > 500_000:
            saved.append((row["年度"], fn, os.path.getsize(path), "已存在"))
            log(f"年报 {row['年度']}", 1, "成功", "已存在，跳过")
            continue
        try:
            with requests.get(row["下载地址"], headers=UA, timeout=120, stream=True) as rr:
                rr.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(65536):
                        f.write(chunk)
            sz = os.path.getsize(path)
            saved.append((row["年度"], fn, sz, "新下载"))
            log(f"年报 {row['年度']}", 1, "成功", f"{sz/1024:.0f}KB")
        except Exception as e:  # noqa: BLE001
            log(f"年报 {row['年度']}", 0, "失败", str(e)[:50])
        time.sleep(0.8)

    q = mdf[(mdf["类别"] == "季度报告") & mdf["标题"].str.contains("第三季度报告", na=False)].head(1)
    for _, row in q.iterrows():
        fn = f"永鼎股份_{row['公告日期']}_2026年第三季度报告.pdf"
        path = os.path.join(RAW, "reports", fn)
        try:
            with requests.get(row["下载地址"], headers=UA, timeout=120, stream=True) as rr:
                rr.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in rr.iter_content(65536):
                        f.write(chunk)
            log("2026三季报", 1, "成功", f"{os.path.getsize(path)/1024:.0f}KB")
        except Exception as e:  # noqa: BLE001
            log("2026三季报", 0, "失败", str(e)[:50])

    pd.DataFrame(saved, columns=["年度", "文件", "字节", "方式"]).to_csv(
        os.path.join(RAW, "reports", "已下载年报清单.csv"), index=False, encoding="utf-8-sig")


def main():
    t0 = time.time()
    print("=" * 78)
    print("永鼎股份(600105.SH) 数据抓取 v2  开始", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 78)
    main_market()
    print("\n[2/6] 公司财报与指标")
    fetch_statements("600105")
    fetch_indicators("600105")
    fetch_mainop("600105")
    fetch_dividend("600105")
    main_peers()
    main_macro()
    main_reports()
    pd.DataFrame(LOG).to_csv(os.path.join(RAW, "_fetch_log.csv"), index=False, encoding="utf-8-sig")
    ok = sum(1 for x in LOG if x["状态"] == "成功")
    print("\n" + "=" * 78)
    print(f"完成：{ok}/{len(LOG)} 项成功，耗时 {time.time()-t0:.1f}s")
    print("=" * 78)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        pd.DataFrame(LOG).to_csv(os.path.join(RAW, "_fetch_log.csv"), index=False, encoding="utf-8-sig")
        sys.exit(1)
