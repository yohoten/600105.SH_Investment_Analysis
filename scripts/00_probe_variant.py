# -*- coding: utf-8 -*-
import subprocess

def run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, len(p.stdout), (p.stdout[:120] if p.stdout else p.stderr[:120])

u = ("https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600105&klt=101&fqt=1"
     "&beg=20260101&end=20500101&fields1=f1&fields2=f51,f53")
for extra in [[], ["-4"], ["--http1.1"], ["-4", "--http1.1"], ["--tlsv1.2"]]:
    print(extra, run(["curl.exe", "-s", "-m", "20", "-H", "User-Agent: Mozilla/5.0"] + extra + [u]))

# 腾讯分页测试
for q in ["sh600105,day,2016-01-01,2018-12-31,640,qfq",
          "sh600105,day,2016-01-01,2020-12-31,800,qfq",
          "sh600105,day,,,640,qfq",
          "sh600105,day,2024-01-01,2026-10-27,640,qfq"]:
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=" + q
    rc, ln, head = run(["curl.exe", "-s", "-m", "25", url])
    print(q, "->", rc, ln, head)
