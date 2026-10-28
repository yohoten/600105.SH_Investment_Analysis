# -*- coding: utf-8 -*-
"""下载2026三季报PDF，并抽取年报文本用于关键附注核对"""
import os
import re
import pandas as pd
import requests
import pymupdf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, "data", "raw", "reports")
TXT = os.path.join(REP, "_text")
os.makedirs(TXT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"}

# 1) 三季报
lst = pd.read_csv(os.path.join(REP, "公告清单.csv"))
q3 = lst[lst["标题"].astype(str).str.contains("第三季度报告", na=False)]
if len(q3):
    row = q3.iloc[0]
    fn = os.path.join(REP, "永鼎股份_2026年第三季度报告.pdf")
    if not os.path.exists(fn) or os.path.getsize(fn) < 100_000:
        r = requests.get(row["下载地址"], headers=UA, timeout=120)
        open(fn, "wb").write(r.content)
    print("三季报:", os.path.basename(fn), f"{os.path.getsize(fn)/1024:.0f}KB")

# 2) 抽取文本
def dump(pdf_path: str, out_name: str) -> str:
    doc = pymupdf.open(pdf_path)
    parts = []
    for i, page in enumerate(doc):
        parts.append(f"\n<<<PAGE {i+1}>>>\n" + page.get_text("text"))
    text = "".join(parts)
    open(os.path.join(TXT, out_name), "w", encoding="utf-8").write(text)
    print(f"  {out_name}: {len(doc)} 页, {len(text)} 字符")
    return text


for f in sorted(os.listdir(REP)):
    if f.lower().endswith(".pdf") and "2025年年度报告" in f:
        t25 = dump(os.path.join(REP, f), "2025年报.txt")
    if f.lower().endswith(".pdf") and "2026年第三季度报告" in f:
        tq3 = dump(os.path.join(REP, f), "2026三季报.txt")

# 3) 定位“投资收益”附注
for tag, text in [("2025年报", t25), ("三季报", tq3)]:
    idx = [m.start() for m in re.finditer(r"投资收益", text)]
    print(f"\n### {tag} 命中 {len(idx)} 处")
    for i in idx[:6]:
        print("-" * 70)
        print(text[max(0, i - 120): i + 700].replace("\n", " ")[:800])
