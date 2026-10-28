# -*- coding: utf-8 -*-
"""
永鼎股份(600105.SH) 数据处理：由原始报表计算分析口径指标
输出 data/processed/*.csv

指标口径（合并报表、人民币元）：
  流动比率 = 流动资产/流动负债            速动比率 = (流动资产-存货)/流动负债
  现金比率 = (货币资金+交易性金融资产)/流动负债
  资产负债率 = 负债合计/资产总计          产权比率 = 负债合计/归母权益
  权益乘数 = 资产总计/归母权益            利息保障倍数 = (利润总额+财务费用)/财务费用
  应收账款周转率 = 营业收入/平均应收账款   存货周转率 = 营业成本/平均存货
  固定资产周转率 = 营业收入/平均固定资产   总资产周转率 = 营业收入/平均总资产
  毛利率 = (营业收入-营业成本)/营业收入    归母净利率 = 归母净利润/营业收入
  ROA = 归母净利润/平均总资产              ROE = 归母净利润/平均归母权益
  净现比 = 经营现金流净额/归母净利润       收入现金比 = 销售商品收到现金/营业收入
  杜邦：ROE = 归母净利率 × 总资产周转率 × 权益乘数
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PRO = os.path.join(ROOT, "data", "processed")
os.makedirs(PRO, exist_ok=True)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)

CODE = "600105"


def load(name):
    df = pd.read_csv(os.path.join(RAW, "financials", name))
    df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"])
    return df


def col(df, name, default=np.nan):
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce")
    print(f"   [警告] 缺少字段 {name}")
    return pd.Series([default] * len(df), index=df.index, dtype="float64")


bs = load(f"{CODE}_资产负债表.csv")
inc = load(f"{CODE}_利润表.csv")
cf = load(f"{CODE}_现金流量表.csv")

trade_col = "TRADE_FINASSET_NOTFVTPL" if "TRADE_FINASSET_NOTFVTPL" in bs.columns else "TRADE_FINASSET"
dep_col = "FA_IR_DEPR" if "FA_IR_DEPR" in cf.columns else "DEPR_FA_COGA_DPBA"
print("交易性金融资产字段:", trade_col, "| 折旧摊销字段:", dep_col)


def build(df, mapping, keep_period=True):
    out = pd.DataFrame({"REPORT_DATE": df["REPORT_DATE"]})
    if keep_period:
        out["报告期"] = df["REPORT_DATE_NAME"]
    for k, v in mapping.items():
        out[k] = col(df, v)
    return out.set_index("REPORT_DATE").sort_index()


P = (build(bs, {
        "货币资金": "MONETARYFUNDS", "交易性金融资产": trade_col, "应收账款": "ACCOUNTS_RECE",
        "存货": "INVENTORY", "流动资产": "TOTAL_CURRENT_ASSETS", "固定资产": "FIXED_ASSET",
        "在建工程": "CIP", "资产总计": "TOTAL_ASSETS", "流动负债": "TOTAL_CURRENT_LIAB",
        "负债合计": "TOTAL_LIABILITIES", "归母权益": "TOTAL_PARENT_EQUITY",
        "所有者权益": "TOTAL_EQUITY", "股本": "SHARE_CAPITAL", "短期借款": "SHORT_LOAN",
        "长期借款": "LONG_LOAN", "应付债券": "BOND_PAYABLE",
    })
     .join(build(inc, keep_period=False, mapping={
        "营业收入": "TOTAL_OPERATE_INCOME", "营业成本": "OPERATE_COST", "销售费用": "SALE_EXPENSE",
        "管理费用": "MANAGE_EXPENSE", "研发费用": "RESEARCH_EXPENSE", "财务费用": "FINANCE_EXPENSE",
        "投资收益": "INVEST_INCOME", "其他收益": "OTHER_INCOME", "资产减值损失": "ASSET_IMPAIRMENT_INCOME",
        "信用减值损失": "CREDIT_IMPAIRMENT_INCOME", "资产处置收益": "ASSET_DISPOSAL_INCOME",
        "公允价值变动": "FAIRVALUE_CHANGE_INCOME", "营业利润": "OPERATE_PROFIT", "利润总额": "TOTAL_PROFIT",
        "净利润": "NETPROFIT", "归母净利润": "PARENT_NETPROFIT", "扣非归母净利润": "DEDUCT_PARENT_NETPROFIT",
        "基本每股收益": "BASIC_EPS", "所得税": "INCOME_TAX",
    }))
     .join(build(cf, keep_period=False, mapping={
        "经营现金流净额": "NETCASH_OPERATE", "投资现金流净额": "NETCASH_INVEST",
        "筹资现金流净额": "NETCASH_FINANCE", "销售商品收到现金": "SALES_SERVICES", "折旧摊销": dep_col,
    })))

P["报告期"] = P["报告期"].astype(str)
P.to_csv(os.path.join(PRO, "panel_all_periods.csv"), encoding="utf-8-sig")

annual = P[P["报告期"].str.endswith("年报")].copy()
annual["年度"] = annual["报告期"].str[:4].astype(int)
annual = annual.sort_values("年度")

flow_cols = ["营业收入", "营业成本", "销售费用", "管理费用", "研发费用", "财务费用", "投资收益",
             "其他收益", "营业利润", "利润总额", "净利润", "归母净利润", "扣非归母净利润",
             "经营现金流净额", "投资现金流净额", "筹资现金流净额", "销售商品收到现金"]


def qmap(s: str) -> float:
    if s.endswith("一季报"):
        return 1
    if s.endswith("中报"):
        return 2
    if s.endswith("三季报"):
        return 3
    if s.endswith("年报"):
        return 4
    return float("nan")


def to_single(df):
    d = df.copy()
    d["Q"] = d["报告期"].map(qmap)
    d["年度"] = d["报告期"].str[:4].astype(int)
    out = []
    for _, g in d.groupby("年度"):
        g = g.sort_values("Q")
        prev = None
        for _, row in g.iterrows():
            r = row.copy()
            if prev is not None and row["Q"] > 1:
                for c in flow_cols:
                    r[c] = row[c] - prev[c]
            prev = row
            out.append(r)
    s = pd.DataFrame(out).sort_values(["年度", "Q"])
    return s[["年度", "Q", "报告期"] + flow_cols]


single = to_single(P)
single.to_csv(os.path.join(PRO, "quarterly_single.csv"), index=False, encoding="utf-8-sig")


def compute_ratios(df):
    d = df.copy()
    for new, src in [("平均应收账款", "应收账款"), ("平均存货", "存货"), ("平均固定资产", "固定资产"),
                     ("平均总资产", "资产总计"), ("平均流动资产", "流动资产"), ("平均归母权益", "归母权益")]:
        d[new] = (d[src] + d[src].shift(1)) / 2

    r = pd.DataFrame(index=d.index)
    r["年度"] = d["年度"]
    r["营业收入(亿元)"] = d["营业收入"] / 1e8
    r["归母净利润(亿元)"] = d["归母净利润"] / 1e8
    r["扣非归母净利润(亿元)"] = d["扣非归母净利润"] / 1e8
    r["经营现金流净额(亿元)"] = d["经营现金流净额"] / 1e8
    r["投资现金流净额(亿元)"] = d["投资现金流净额"] / 1e8
    r["筹资现金流净额(亿元)"] = d["筹资现金流净额"] / 1e8
    r["毛利率%"] = (d["营业收入"] - d["营业成本"]) / d["营业收入"] * 100
    r["归母净利率%"] = d["归母净利润"] / d["营业收入"] * 100
    r["期间费用率%"] = (d["销售费用"] + d["管理费用"] + d["研发费用"] + d["财务费用"]) / d["营业收入"] * 100
    r["销售费用率%"] = d["销售费用"] / d["营业收入"] * 100
    r["管理费用率%"] = d["管理费用"] / d["营业收入"] * 100
    r["研发费用率%"] = d["研发费用"] / d["营业收入"] * 100
    r["财务费用率%"] = d["财务费用"] / d["营业收入"] * 100

    r["流动比率"] = d["流动资产"] / d["流动负债"]
    r["速动比率"] = (d["流动资产"] - d["存货"]) / d["流动负债"]
    r["现金比率"] = (d["货币资金"] + d["交易性金融资产"].fillna(0)) / d["流动负债"]
    r["资产负债率%"] = d["负债合计"] / d["资产总计"] * 100
    r["产权比率"] = d["负债合计"] / d["归母权益"]
    r["权益乘数"] = d["资产总计"] / d["归母权益"]
    r["利息保障倍数"] = (d["利润总额"] + d["财务费用"]) / d["财务费用"]

    r["应收账款周转率"] = d["营业收入"] / d["平均应收账款"]
    r["应收账款周转天数"] = 365 / r["应收账款周转率"]
    r["存货周转率"] = d["营业成本"] / d["平均存货"]
    r["存货周转天数"] = 365 / r["存货周转率"]
    r["固定资产周转率"] = d["营业收入"] / d["平均固定资产"]
    r["总资产周转率"] = d["营业收入"] / d["平均总资产"]
    r["流动资产周转率"] = d["营业收入"] / d["平均流动资产"]

    r["ROA%"] = d["归母净利润"] / d["平均总资产"] * 100
    r["ROE%"] = d["归母净利润"] / d["平均归母权益"] * 100
    r["EPS(元)"] = d["基本每股收益"]
    r["BPS(元)"] = d["归母权益"] / d["股本"]
    r["扣非占比%"] = d["扣非归母净利润"] / d["归母净利润"] * 100
    r["净现比"] = d["经营现金流净额"] / d["归母净利润"]
    r["收入现金比"] = d["销售商品收到现金"] / d["营业收入"]
    r["每股经营现金流(元)"] = d["经营现金流净额"] / d["股本"]

    r["营收增长率%"] = d["营业收入"].pct_change() * 100
    r["归母净利增长率%"] = d["归母净利润"].pct_change() * 100
    r["总资产增长率%"] = d["资产总计"].pct_change() * 100
    r["净资产增长率%"] = d["归母权益"].pct_change() * 100

    r["杜邦校验ROE%"] = r["归母净利率%"] / 100 * r["总资产周转率"] * r["权益乘数"] * 100
    return r


ratios_annual = compute_ratios(annual)
ratios_annual.to_csv(os.path.join(PRO, "ratios_annual.csv"), index=False, encoding="utf-8-sig")

q26 = P[P["报告期"] == "2026三季报"]
prev_y = P[P["报告期"] == "2025年报"].iloc[0]
prev_q3 = P[P["报告期"] == "2025三季报"].iloc[0]
if len(q26):
    rw = q26.iloc[0]
    ann26 = pd.DataFrame([{
        "年度": 2026, "口径": "2026前三季度",
        "营业收入(亿元)": rw["营业收入"] / 1e8, "归母净利润(亿元)": rw["归母净利润"] / 1e8,
        "扣非归母净利润(亿元)": rw["扣非归母净利润"] / 1e8,
        "经营现金流净额(亿元)": rw["经营现金流净额"] / 1e8,
        "投资现金流净额(亿元)": rw["投资现金流净额"] / 1e8,
        "筹资现金流净额(亿元)": rw["筹资现金流净额"] / 1e8,
        "毛利率%": (rw["营业收入"] - rw["营业成本"]) / rw["营业收入"] * 100,
        "归母净利率%": rw["归母净利润"] / rw["营业收入"] * 100,
        "期间费用率%": (rw["销售费用"] + rw["管理费用"] + rw["研发费用"] + rw["财务费用"]) / rw["营业收入"] * 100,
        "财务费用率%": rw["财务费用"] / rw["营业收入"] * 100,
        "研发费用率%": rw["研发费用"] / rw["营业收入"] * 100,
        "流动比率": rw["流动资产"] / rw["流动负债"],
        "速动比率": (rw["流动资产"] - rw["存货"]) / rw["流动负债"],
        "现金比率": (rw["货币资金"] + (rw["交易性金融资产"] if not np.isnan(rw["交易性金融资产"]) else 0)) / rw["流动负债"],
        "资产负债率%": rw["负债合计"] / rw["资产总计"] * 100,
        "产权比率": rw["负债合计"] / rw["归母权益"],
        "权益乘数": rw["资产总计"] / rw["归母权益"],
        "利息保障倍数": (rw["利润总额"] + rw["财务费用"]) / rw["财务费用"],
        "应收账款周转率": rw["营业收入"] / ((rw["应收账款"] + prev_y["应收账款"]) / 2) * 3 / 4,
        "存货周转率": rw["营业成本"] / ((rw["存货"] + prev_y["存货"]) / 2) * 3 / 4,
        "总资产周转率": rw["营业收入"] / ((rw["资产总计"] + prev_y["资产总计"]) / 2) * 3 / 4,
        "ROE%": rw["归母净利润"] / ((rw["归母权益"] + prev_y["归母权益"]) / 2) * 3 / 4 * 100,
        "ROA%": rw["归母净利润"] / ((rw["资产总计"] + prev_y["资产总计"]) / 2) * 3 / 4 * 100,
        "EPS(元)": rw["基本每股收益"], "BPS(元)": rw["归母权益"] / rw["股本"],
        "扣非占比%": rw["扣非归母净利润"] / rw["归母净利润"] * 100,
        "净现比": rw["经营现金流净额"] / rw["归母净利润"],
        "收入现金比": rw["销售商品收到现金"] / rw["营业收入"],
        "营收增长率%": (rw["营业收入"] / prev_q3["营业收入"] - 1) * 100,
        "归母净利增长率%": (rw["归母净利润"] / prev_q3["归母净利润"] - 1) * 100,
    }])
    ann26.to_csv(os.path.join(PRO, "ratios_2026Q3.csv"), index=False, encoding="utf-8-sig")
    print("\n=== 2026 前三季度（周转率/ROE 已按 3/4 折算为年化）===")
    print(ann26.T.to_string())

print("\n=== 年度比率表 ===")
show = ["年度", "营业收入(亿元)", "归母净利润(亿元)", "毛利率%", "归母净利率%", "ROE%",
        "资产负债率%", "流动比率", "总资产周转率", "净现比", "扣非占比%"]
print(ratios_annual[show].round(2).to_string(index=False))

# ---------------- 估值序列 ----------------
print("\n>>> 构建估值序列")
px = pd.read_csv(os.path.join(RAW, "market", "600105_日线_不复权.csv"))
px["日期"] = pd.to_datetime(px["日期"], errors="coerce")
px = px.dropna(subset=["日期"]).drop_duplicates(subset=["日期"], keep="last").sort_values("日期")

# 用 merge_asof 做阶梯填充，避免 reindex 对索引单调性的要求
sh = P[["股本"]].dropna().reset_index()
sh = sh.dropna().sort_values("REPORT_DATE")[["REPORT_DATE", "股本"]]
px = pd.merge_asof(px, sh, left_on="日期", right_on="REPORT_DATE", direction="backward")

# TTM 归母净利 / 营收：按实际公告日（NOTICE_DATE）生效，避免前视偏差
notice = inc[["REPORT_DATE", "NOTICE_DATE"]].dropna().copy()
notice["NOTICE_DATE"] = pd.to_datetime(notice["NOTICE_DATE"], errors="coerce")
notice = notice.dropna().sort_values("REPORT_DATE").drop_duplicates(subset=["REPORT_DATE"], keep="last")
notice_map = dict(zip(notice["REPORT_DATE"], notice["NOTICE_DATE"]))

sq = single.copy()
sq["期末"] = pd.to_datetime(sq["年度"].astype(str) + "-" +
                            sq["Q"].map({1: "03-31", 2: "06-30", 3: "09-30", 4: "12-31"}))
sq = sq.drop_duplicates(subset=["期末"], keep="last").sort_values("期末")
sq["TTM归母"] = sq["归母净利润"].rolling(4).sum()
sq["TTM营收"] = sq["营业收入"].rolling(4).sum()
sq["公告日"] = sq["期末"].map(notice_map)
ttm = sq.dropna(subset=["TTM归母", "公告日"])[["公告日", "TTM归母", "TTM营收"]].copy()
ttm = ttm.sort_values("公告日")
px = pd.merge_asof(px, ttm, left_on="日期", right_on="公告日", direction="backward")

eq = P[["归母权益"]].dropna().reset_index()
eq = eq.sort_values("REPORT_DATE")[["REPORT_DATE", "归母权益"]]
px = pd.merge_asof(px, eq, left_on="日期", right_on="REPORT_DATE", direction="backward")

px["总市值(亿元)"] = px["收盘"] * px["股本"] / 1e8
px["PE_TTM"] = np.where(px["TTM归母"] > 1e7, px["总市值(亿元)"] / (px["TTM归母"] / 1e8), np.nan)
px["PB"] = px["总市值(亿元)"] / (px["归母权益"] / 1e8)
px["PS_TTM"] = np.where(px["TTM营收"] > 0, px["总市值(亿元)"] / (px["TTM营收"] / 1e8), np.nan)

val = px[["日期", "收盘", "股本", "总市值(亿元)", "PE_TTM", "PB", "PS_TTM", "TTM归母", "TTM营收"]]
val.to_csv(os.path.join(PRO, "valuation_daily.csv"), index=False, encoding="utf-8-sig")
last = val.dropna(subset=["PE_TTM"]).iloc[-1]
print(f"   最新：{last['日期'].date()} 收盘{last['收盘']:.2f} 市值{last['总市值(亿元)']:.1f}亿 "
      f"PE_TTM {last['PE_TTM']:.1f} PB {last['PB']:.1f} PS {last['PS_TTM']:.2f}")

# ---------------- 主营构成 ----------------
mo = pd.read_csv(os.path.join(RAW, "financials", "600105_主营构成.csv"))
mo["REPORT_DATE"] = pd.to_datetime(mo["REPORT_DATE"])
seg = mo[mo["MAINOP_TYPE"] == 1].copy()
seg["报告期"] = seg["REPORT_DATE"].dt.strftime("%Y-%m-%d")
seg = seg[["报告期", "ITEM_NAME", "MAIN_BUSINESS_INCOME", "MBI_RATIO", "GROSS_RPOFIT_RATIO", "MAIN_BUSINESS_RPOFIT"]]
seg.columns = ["报告期", "业务板块", "主营收入(元)", "收入占比", "毛利率", "主营毛利(元)"]
seg.to_csv(os.path.join(PRO, "segment_income.csv"), index=False, encoding="utf-8-sig")
print(f"   主营构成：{seg['报告期'].nunique()} 期；板块 {sorted(seg['业务板块'].unique())}")

reg = mo[mo["MAINOP_TYPE"] == 3].copy()
reg["报告期"] = reg["REPORT_DATE"].dt.strftime("%Y-%m-%d")
reg[["报告期", "ITEM_NAME", "MAIN_BUSINESS_INCOME", "MBI_RATIO", "GROSS_RPOFIT_RATIO"]].to_csv(
    os.path.join(PRO, "segment_region.csv"), index=False, encoding="utf-8-sig")

print("\n处理完成 →", PRO)
