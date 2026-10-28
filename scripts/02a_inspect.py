# -*- coding: utf-8 -*-
"""检查已抓取数据的字段与关键数值"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 60)

for nm in ["资产负债表", "利润表", "现金流量表"]:
    p = os.path.join(RAW, "financials", f"600105_{nm}.csv")
    df = pd.read_csv(p)
    print(f"\n=== {nm}  {df.shape}  列数 {len(df.columns)}")
    print("报告期：", sorted(df["REPORT_DATE_NAME"].unique())[:5], "...", sorted(df["REPORT_DATE_NAME"].unique())[-3:])
    print("字段前40:", list(df.columns)[:40])

# 利润表关键科目
inc = pd.read_csv(os.path.join(RAW, "financials", "600105_利润表.csv"))
cols = [c for c in ["REPORT_DATE_NAME", "TOTAL_OPERATE_INCOME", "OPERATE_COST", "OPERATE_PROFIT",
                    "TOTAL_PROFIT", "NETPROFIT", "PARENT_NETPROFIT", "DEDUCT_PARENT_NETPROFIT",
                    "BASIC_EPS", "FINANCE_EXPENSE", "RESEARCH_EXPENSE", "SALE_EXPENSE", "MANAGE_EXPENSE"] if c in inc.columns]
print("\n--- 利润表关键科目（年报）---")
print(inc[inc["REPORT_DATE_NAME"].str.endswith("年报")][cols].sort_values("REPORT_DATE_NAME").to_string(index=False))

bs = pd.read_csv(os.path.join(RAW, "financials", "600105_资产负债表.csv"))
cols = [c for c in ["REPORT_DATE_NAME", "MONETARYFUNDS", "ACCOUNTS_RECE", "INVENTORY", "TOTAL_CURRENT_ASSETS",
                    "TOTAL_ASSETS", "TOTAL_CURRENT_LIAB", "TOTAL_LIABILITIES", "TOTAL_PARENT_EQUITY",
                    "SHARE_CAPITAL", "FIXED_ASSET", "CIP"] if c in bs.columns]
print("\n--- 资产负债表关键科目（年报）---")
print(bs[bs["REPORT_DATE_NAME"].str.endswith("年报")][cols].sort_values("REPORT_DATE_NAME").to_string(index=False))
