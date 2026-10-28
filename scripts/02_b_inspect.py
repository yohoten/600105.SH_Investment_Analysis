# -*- coding: utf-8 -*-
"""检查2026年季度数据与主营构成"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)

inc = pd.read_csv(os.path.join(RAW, "financials", "600105_利润表.csv"))
cols = ["REPORT_DATE_NAME", "TOTAL_OPERATE_INCOME", "OPERATE_COST", "OPERATE_PROFIT", "TOTAL_PROFIT",
        "NETPROFIT", "PARENT_NETPROFIT", "DEDUCT_PARENT_NETPROFIT", "BASIC_EPS", "FINANCE_EXPENSE",
        "INVEST_INCOME", "FAIRVALUE_CHANGE_INCOME", "ASSET_DISPOSAL_INCOME", "OTHER_INCOME"]
cols = [c for c in cols if c in inc.columns]
print("=== 利润表 2025-2026 各期 ===")
print(inc[inc["REPORT_DATE_NAME"] >= "2025一季报"][cols].sort_values("REPORT_DATE_NAME").to_string(index=False))

bs = pd.read_csv(os.path.join(RAW, "financials", "600105_资产负债表.csv"))
c2 = ["REPORT_DATE_NAME", "TOTAL_ASSETS", "TOTAL_LIABILITIES", "TOTAL_PARENT_EQUITY", "SHARE_CAPITAL",
      "TOTAL_CURRENT_ASSETS", "TOTAL_CURRENT_LIAB", "INVENTORY", "ACCOUNTS_RECE"]
print("\n=== 资产负债表 2026 各期 ===")
print(bs[bs["REPORT_DATE_NAME"] >= "2026一季报"][[c for c in c2 if c in bs.columns]].sort_values("REPORT_DATE_NAME").to_string(index=False))

cf = pd.read_csv(os.path.join(RAW, "financials", "600105_现金流量表.csv"))
c3 = [c for c in ["REPORT_DATE_NAME", "NETCASH_OPERATE", "NETCASH_INVEST", "NETCASH_FINANCE"] if c in cf.columns]
print("\n=== 现金流量表（年报及2026Q3）===")
sel = cf[(cf["REPORT_DATE_NAME"].str.endswith("年报")) | (cf["REPORT_DATE_NAME"] == "2026三季报")]
print(sel[c3].sort_values("REPORT_DATE_NAME").to_string(index=False))

mo = pd.read_csv(os.path.join(RAW, "financials", "600105_主营构成.csv"))
print("\n=== 主营构成字段 ===")
print(list(mo.columns))
print("类型取值:", mo["MAINOP_TYPE"].unique())
last = mo[mo["REPORT_DATE"] == mo["REPORT_DATE"].max()]
print("\n最新期", mo["REPORT_DATE"].max())
print(last[["MAINOP_TYPE", "ITEM_NAME", "MAIN_BUSINESS_INCOME", "MBI_RATIO", "GROSS_RPOFIT_RATIO"]].to_string(index=False))
