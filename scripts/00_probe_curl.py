# -*- coding: utf-8 -*-
import subprocess, shutil, sys
print("which curl:", shutil.which("curl"))
u = ("https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600105&klt=101&fqt=1"
     "&beg=20260101&end=20500101&fields1=f1&fields2=f51,f53")
p = subprocess.run(["curl.exe", "-s", "-m", "30", "-H", "User-Agent: Mozilla/5.0", u],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print("rc", p.returncode, "len", len(p.stdout))
print(p.stdout[:200])
print("err", p.stderr[:200])

u2 = ("https://push2.eastmoney.com/api/qt/stock/get?secid=1.600105"
      "&fields=f43,f57,f58,f84,f85,f116,f117,f162,f167,f173")
p2 = subprocess.run(["curl.exe", "-s", "-m", "30", "-H", "User-Agent: Mozilla/5.0", u2],
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
print("quote rc", p2.returncode, "len", len(p2.stdout))
print(p2.stdout[:400])
