# -*- coding: utf-8 -*-
"""按关键词抽取年报关键段落"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT = os.path.join(ROOT, "data", "raw", "reports", "_text")
text = open(os.path.join(TXT, "2025年报.txt"), encoding="utf-8").read()

KEYS = sys.argv[1:] or ["主营业务分行业", "前五名客户", "研发投入", "短期借款", "行业情况",
                        "竞争格局", "光棒", "海外", "在手订单"]

for k in KEYS:
    idx = [m.start() for m in re.finditer(k, text)]
    print("=" * 90)
    print(f"### 关键词【{k}】 命中 {len(idx)} 处")
    for i in idx[:2]:
        seg = text[max(0, i - 200): i + 1400]
        print("-" * 80)
        print(re.sub(r"\s+", " ", seg))
