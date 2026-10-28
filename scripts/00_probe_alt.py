# -*- coding: utf-8 -*-
"""测试备用行情源（腾讯/新浪/网易）可用性"""
import requests, json

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

def t(name, url, **kw):
    try:
        r = requests.get(url, headers=UA, timeout=25, **kw)
        txt = r.text
        print(f"[{name}] {r.status_code} len={len(txt)} :: {txt[:180]}")
    except Exception as e:
        print(f"[{name}] FAIL {type(e).__name__}: {str(e)[:100]}")

t("腾讯qfq", "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600105,day,2016-01-01,2026-10-27,4000,qfq")
t("腾讯day", "https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param=sh600105,day,2016-01-01,2026-10-27,4000")
t("新浪kline", "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600105&scale=240&ma=no&datalen=2000")
t("网易csv", "https://quotes.money.163.com/service/chddata.html?code=0600105&start=20160101&end=20261027&fields=TCLOSE;HIGH;LOW;TOPEN;LCLOSE;CHG;PCHG;TURNOVER;VOTURNOVER;VATURNOVER")
t("腾讯实时", "https://qt.gtimg.cn/q=sh600105")
t("新浪实时", "https://hq.sinajs.cn/list=sh600105")
t("datacenter", "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_FINANCE_MAINFINADATA&columns=SECUCODE%2CREPORT_DATE%2CEPSJB&filter=(SECUCODE%3D%22600105.SH%22)&pageNumber=1&pageSize=2&source=HSF10&client=PC")
