# -*- coding: utf-8 -*-
"""检查有息负债、长期股权投资等资产负债表明细"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "financials")
bs = pd.read_csv(os.path.join(RAW, "600105_资产负债表.csv"))
bs["REPORT_DATE"] = pd.to_datetime(bs["REPORT_DATE"])

cand = ["REPORT_DATE", "REPORT_DATE_NAME", "SHORT_LOAN", "LONG_LOAN", "BOND_PAYABLE", "NONCURRENT_LIAB_1YEAR",
        "LONG_EQUITY_INVEST", "TRADE_FINASSET_NOTFVTPL", "NOTE_ACCOUNTS_RECE", "CONTRACT_LIAB",
        "MINORITY_EQUITY", "TOTAL_EQUITY", "LEASE_LIAB", "DEFER_INCOME"]
cand = [c for c in cand if c in bs.columns]
sel = bs[bs["REPORT_DATE_NAME"].str.endswith("年报") | (bs["REPORT_DATE_NAME"] == "2026三季报")]
print(sel[cand].sort_values("REPORT_DATE").to_string(index=False))
print("\n字段是否存在：", {c: (c in bs.columns) for c in
      ["SHORT_LOAN", "LONG_LOAN", "BOND_PAYABLE", "NONCURRENT_LIAB_1YEAR", "LONG_EQUITY_INVEST"]})
