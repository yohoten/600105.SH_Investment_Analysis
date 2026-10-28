# -*- coding: utf-8 -*-
"""
analysis_lib.py —— 永鼎股份(600105.SH)投资分析 公共分析库
Notebook 与本目录下 05_build_outputs.py 共用，保证图表与报告口径一致。

数据依赖：data/processed/*.csv、data/raw/*
输出：figures/*.png（300dpi）
"""
from __future__ import annotations

import json
import os
import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PRO = os.path.join(ROOT, "data", "processed")

# 图目录与“裸图”开关：
#   默认 figures/                 —— 带图内标题与图内数据来源，供 Notebook 单独查看时自解释
#   FIG_DIR=figures/report
#   FIG_BARE=1                    —— 去掉图内标题与图内数据来源，供 Word 报告使用
#                                    （报告已在图下方给出图题与数据来源，避免同一信息出现两次）
_fig_dir = os.environ.get("FIG_DIR", "figures")
FIG = _fig_dir if os.path.isabs(_fig_dir) else os.path.join(ROOT, _fig_dir)
BARE = os.environ.get("FIG_BARE") == "1"
os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------- 绘图样式
for f in ["SimHei", "Microsoft YaHei", "SimSun"]:
    try:
        font_manager.findfont(f, fallback_to_default=False)
        CN = f
        break
    except Exception:
        continue
else:
    CN = "SimHei"

plt.rcParams.update({
    "font.sans-serif": [CN, "Microsoft YaHei"],
    "font.family": "sans-serif",
    "axes.unicode_minus": False,
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#4a4a4a",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#dcdcdc",
    "grid.linewidth": 0.6,
    "grid.linestyle": "--",
    "axes.titlesize": 11,
    "axes.labelsize": 9.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5,
    "legend.frameon": False,
})

# 报告配色（深色适合打印）：主色 蓝 / 辅 橙 / 强调 红（涨）/ 绿（跌）
C_MAIN = "#1f4e79"
C_SUB = "#c55a11"
C_ACC = "#2e7d32"
C_WARN = "#c00000"
C_GRAY = "#7f7f7f"
C_LIGHT = "#9dc3e6"
PALETTE = ["#1f4e79", "#c55a11", "#2e7d32", "#7f7f7f", "#7030a0", "#bf9000"]

SRC = "数据来源：公司2016—2025年年度报告、2026年第三季度报告；腾讯财经、东方财富；作者整理计算"


def _save(fig, name: str) -> str:
    path = os.path.join(FIG, name)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def _src(ax, text: str = SRC, y: float = -0.22):
    if BARE:            # 裸图模式：来源由报告正文给出
        return
    ax.annotate(text, xy=(0, y), xycoords="axes fraction", fontsize=7, color="#666666")


if BARE:
    # 裸图模式下去掉图内标题：报告已用“图X-X ……”的图题，重复标题会显得业余
    from matplotlib.axes import Axes as _Axes
    _Axes.set_title = lambda self, *a, **k: None


def _peer_plus_yd(d: dict) -> pd.DataFrame:
    """同业核心指标 + 永鼎股份自身。

    东方财富同业接口（PEERS）只含 6 家可比公司，不含 600105。为使同业对比图
    里本公司不被“漏画”，这里按同一口径把公司自身年度指标补进面板：
    营业收入、毛利率、净利率、加权 ROE、资产负债率、总资产周转率、流动比率。
    """
    pi = d["peer_ind"].copy()
    ra = d["ra"].set_index("年度")
    rows = []
    for y in range(2016, 2026):
        if y not in ra.index:
            continue
        r = ra.loc[y]
        rows.append({
            "名称": "永鼎股份",
            "REPORT_DATE_NAME": f"{y}年报",
            "TOTALOPERATEREVE": r["营业收入(亿元)"] * 1e8,
            "XSMLL": r["毛利率%"],
            "XSJLL": r["归母净利率%"],
            "ROEJQ": r["ROE%"],
            "ZCFZL": r["资产负债率%"],
            "TOAZZL": r["总资产周转率"],
            "LD": r["流动比率"],
        })
    return pd.concat([pi, pd.DataFrame(rows)], ignore_index=True)


# ---------------------------------------------------------------- 数据加载
def load_all() -> dict:
    d = {}
    d["ra"] = pd.read_csv(os.path.join(PRO, "ratios_annual.csv"))
    d["q3"] = pd.read_csv(os.path.join(PRO, "ratios_2026Q3.csv")).iloc[0].to_dict()
    d["panel"] = pd.read_csv(os.path.join(PRO, "panel_all_periods.csv"))
    d["single"] = pd.read_csv(os.path.join(PRO, "quarterly_single.csv"))
    d["val"] = pd.read_csv(os.path.join(PRO, "valuation_daily.csv"), parse_dates=["日期"])
    d["seg"] = pd.read_csv(os.path.join(PRO, "segment_income.csv"), parse_dates=["报告期"])
    d["reg"] = pd.read_csv(os.path.join(PRO, "segment_region.csv"), parse_dates=["报告期"])
    d["peer_ind"] = pd.read_csv(os.path.join(RAW, "peers", "同业核心指标.csv"))
    d["peer_px"] = pd.read_csv(os.path.join(RAW, "peers", "同业日线_前复权.csv"), parse_dates=["日期"])
    d["idx"] = pd.read_csv(os.path.join(RAW, "market", "指数日线.csv"), parse_dates=["日期"])
    d["px"] = pd.read_csv(os.path.join(RAW, "market", "600105_日线_前复权.csv"), parse_dates=["日期"])
    d["mac"] = {}
    for f, k in [("GDP.csv", "gdp"), ("CPI.csv", "cpi"), ("PPI.csv", "ppi"), ("制造业PMI.csv", "pmi"),
                 ("货币供应量.csv", "m2"), ("社会消费品零售总额.csv", "retail"),
                 ("固定资产投资.csv", "fai"), ("存款准备金率.csv", "rrr"),
                 ("LPR贷款市场报价利率.csv", "lpr")]:
        p = os.path.join(RAW, "macro", f)
        if os.path.exists(p):
            df = pd.read_csv(p)
            if "REPORT_DATE" in df.columns:
                df["REPORT_DATE"] = pd.to_datetime(df["REPORT_DATE"])
                df = df.sort_values("REPORT_DATE")
            d["mac"][k] = df
    return d


# ---------------------------------------------------------------- 表格
def t_annual(d: dict) -> pd.DataFrame:
    """2016-2025 年度主要指标 + 2026前三季度 对照"""
    ra = d["ra"].set_index("年度")
    cols = ["营业收入(亿元)", "归母净利润(亿元)", "扣非归母净利润(亿元)", "毛利率%", "归母净利率%",
            "期间费用率%", "ROE%", "ROA%", "流动比率", "速动比率", "资产负债率%", "应收账款周转率",
            "存货周转率", "总资产周转率", "净现比", "扣非占比%", "EPS(元)", "BPS(元)"]
    t = ra.loc[2016:2025, cols].T
    q = d["q3"]
    t["2026前三季度"] = [q.get(c, np.nan) for c in cols]
    t.index.name = "指标"
    return t.round(2)


def t_segment_h1(d: dict) -> pd.DataFrame:
    """半年报口径分产品收入与毛利率（2021H1起口径一致）"""
    s = d["seg"][d["seg"]["报告期"].dt.month == 6].copy()
    s["期"] = s["报告期"].dt.strftime("%Y") + "H1"

    def unify(x: str) -> str:
        x = str(x)
        if "光" in x:
            return "光通信"
        if "汽车" in x:
            return "汽车线束"
        if "电力工程" in x or "海外工程" in x:
            return "电力工程"
        if "超导" in x or "铜" in x:
            return "超导及铜导体"
        if "大数据" in x or "软件" in x:
            return "大数据应用"
        return "其他"

    s["板块"] = s["业务板块"].map(unify)
    p = s.pivot_table(index="期", columns="板块", values="主营收入(元)", aggfunc="sum") / 1e8
    return p.round(2)


def t_segment_margin_h1(d: dict) -> pd.DataFrame:
    s = d["seg"][d["seg"]["报告期"].dt.month == 6].copy()
    s["期"] = s["报告期"].dt.strftime("%Y") + "H1"

    def unify(x: str) -> str:
        x = str(x)
        if "光" in x:
            return "光通信"
        if "汽车" in x:
            return "汽车线束"
        if "电力工程" in x or "海外工程" in x:
            return "电力工程"
        if "超导" in x or "铜" in x:
            return "超导及铜导体"
        if "大数据" in x or "软件" in x:
            return "大数据应用"
        return "其他"

    s["板块"] = s["业务板块"].map(unify)
    p = s.pivot_table(index="期", columns="板块", values="毛利率", aggfunc="mean") * 100
    return p.round(2)


def t_peer(d: dict) -> pd.DataFrame:
    """同业对比：2025年报 + 2026三季报（东财F10口径）"""
    pi = d["peer_ind"].copy()
    pi = pi[pi["REPORT_DATE_NAME"].isin(["2025年报", "2026三季报"])]
    keep = ["名称", "REPORT_DATE_NAME", "TOTALOPERATEREVE", "PARENTNETPROFIT", "XSMLL", "XSJLL",
            "ROEJQ", "ZCFZL", "EPSJB", "BPS"]
    keep = [c for c in keep if c in pi.columns]
    out = pi[keep].copy()
    out.columns = ["名称", "报告期", "营业收入(元)", "归母净利润(元)", "毛利率%", "净利率%",
                   "加权ROE%", "资产负债率%", "EPS(元)", "BPS(元)"][: len(keep)]
    out["营业收入(亿元)"] = out["营业收入(元)"] / 1e8
    out["归母净利润(亿元)"] = out["归母净利润(元)"] / 1e8
    return out


def t_macro_annual(d: dict) -> pd.DataFrame:
    m = d["mac"]
    g = m["gdp"][m["gdp"]["TIME"].astype(str).str.contains("第1-4季度|全年")].copy()
    g["年"] = g["REPORT_DATE"].dt.year
    g = g.drop_duplicates("年", keep="last").set_index("年")
    cpi = m["cpi"][m["cpi"]["TIME"].astype(str).str.endswith("12月份")].copy()
    cpi["年"] = cpi["REPORT_DATE"].dt.year
    cpi = cpi.drop_duplicates("年", keep="last").set_index("年")
    ppi = m["ppi"][m["ppi"]["TIME"].astype(str).str.endswith("12月份")].copy()
    ppi["年"] = ppi["REPORT_DATE"].dt.year
    ppi = ppi.drop_duplicates("年", keep="last").set_index("年")
    pmi = m["pmi"].copy()
    pmi["年"] = pmi["REPORT_DATE"].dt.year
    pmi_y = pmi.groupby("年")["MAKE_INDEX"].mean()
    m2 = m["m2"][m["m2"]["TIME"].astype(str).str.endswith("12月份")].copy()
    m2["年"] = m2["REPORT_DATE"].dt.year
    m2 = m2.drop_duplicates("年", keep="last").set_index("年")

    out = pd.DataFrame({
        "GDP增速%": g["SUM_SAME"],
        "CPI同比%": cpi["NATIONAL_SAME"],
        "PPI同比%": ppi["BASE_SAME"],
        "制造业PMI均值": pmi_y,
        # BASIC_CURRENCY = 货币和准货币(M2)；FREE_CASH 是 M0，勿混用
        "M2同比%": m2["BASIC_CURRENCY_SAME"],
    })
    return out.loc[2016:2025].round(2)


def t_valuation(d: dict) -> pd.DataFrame:
    v = d["val"].dropna(subset=["PE_TTM"]).copy()
    last = v.iloc[-1]
    rows = [
        ("收盘价(元)", last["收盘"], "2026-10-27"),
        ("总股本(亿股)", last["股本"] / 1e8, "2026年三季报"),
        ("总市值(亿元)", last["总市值(亿元)"], "收盘价×总股本"),
        ("TTM归母净利润(亿元)", last["TTM归母"] / 1e8, "2025Q4—2026Q3"),
        ("TTM营业收入(亿元)", last["TTM营收"] / 1e8, "2025Q4—2026Q3"),
        ("PE(TTM)", last["PE_TTM"], "总市值/TTM归母净利润"),
        ("PB(MRQ)", last["PB"], "总市值/归母净资产"),
        ("PS(TTM)", last["PS_TTM"], "总市值/TTM营业收入"),
    ]
    return pd.DataFrame(rows, columns=["指标", "数值", "说明"])


# ---------------------------------------------------------------- 图 1 宏观
def f_macro_growth(d: dict) -> str:
    m = t_macro_annual(d)
    years = m.index.astype(int)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.bar(years - 0.18, m["GDP增速%"], width=0.36, color=C_MAIN, label="GDP实际增速(%)")
    ax.bar(years + 0.18, m["PPI同比%"], width=0.36, color=C_SUB, label="PPI同比(%)")
    ax.plot(years, m["CPI同比%"], "o-", color=C_ACC, lw=1.9, ms=4.5, label="CPI同比(%)")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.set_xticks(years)
    ax.set_ylim(-4, 11.5)
    ax.set_title("2016—2025年中国GDP、CPI与PPI同比增速", pad=24)
    ax.set_ylabel("%")
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0), columnspacing=1.4)
    _src(ax, "数据来源：国家统计局、东方财富数据中心（年度值为12月当月同比；PMI为12个月算术平均）")
    return _save(fig, "图1-1_宏观GDP_CPI_PPI.png")


def f_macro_money(d: dict) -> str:
    """M2 与 PMI 量纲差异大（7—12 vs 49—52），采用双纵轴"""
    m = t_macro_annual(d)
    years = m.index.astype(int)
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    ax.plot(years, m["M2同比%"], "s-", color=C_MAIN, lw=1.9, ms=4.5, label="M2余额同比（左轴，%）")
    ax.set_ylabel("M2同比（%）", color=C_MAIN)
    ax.set_ylim(0, 20)
    ax.tick_params(axis="y", colors=C_MAIN)
    ax2 = ax.twinx()
    ax2.plot(years, m["制造业PMI均值"], "o-", color=C_SUB, lw=1.9, ms=4.5, label="制造业PMI年均值（右轴）")
    ax2.axhline(50, color=C_GRAY, lw=0.9, ls=":")
    ax2.text(years[0] - 0.3, 50.15, "荣枯线 50", color=C_GRAY, fontsize=7.5, ha="left")
    ax2.set_ylim(48, 53)
    ax2.set_ylabel("制造业PMI", color=C_SUB)
    ax2.tick_params(axis="y", colors=C_SUB)
    ax2.grid(False)
    ax.set_xticks(years)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    ax.set_title("货币供应与制造业景气：M2增速与制造业PMI（双纵轴）", pad=26)
    _src(ax, "数据来源：中国人民银行、国家统计局、东方财富数据中心；M2为年末同比，PMI为当年12个月均值")
    return _save(fig, "图1-2_宏观M2_PMI.png")


# ---------------------------------------------------------------- 图 2 行业
def f_peer_index(d: dict) -> str:
    """同业与公司股价指数（2016-01-04=100）"""
    px = d["peer_px"]
    px = px[px["日期"] >= "2016-01-01"]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    base_date = px["日期"].min()
    series = {}
    for nm, g in px.groupby("名称"):
        g = g.sort_values("日期")
        s = g.set_index("日期")["收盘"]
        s = s / s.iloc[0] * 100
        if len(s) > 100:
            series[nm] = s
            ax.plot(s.index, s.values, lw=1.2, color=PALETTE[list(series).index(nm) % len(PALETTE)], label=nm)
    own = d["px"].sort_values("日期").set_index("日期")["收盘"]
    own = own[own.index >= base_date]
    own = own / own.iloc[0] * 100
    ax.plot(own.index, own.values, lw=2.4, color=C_WARN, label="永鼎股份", zorder=5)
    ax.set_yscale("log")
    ax.set_yticks([50, 100, 200, 400, 800, 1600])
    ax.get_yaxis().set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}"))
    ax.set_title("永鼎股份与同业公司股价走势（2016-01-04=100，对数坐标）", pad=10)
    ax.legend(ncol=4, loc="upper left", fontsize=7.5)
    _src(ax, "数据来源：腾讯财经前复权日行情，作者整理")
    return _save(fig, "图2-1_同业股价指数.png")


def f_peer_revenue_growth(d: dict) -> str:
    pi = _peer_plus_yd(d)
    pi = pi[pi["REPORT_DATE_NAME"].str.endswith("年报")].copy()
    pi["年"] = pi["REPORT_DATE_NAME"].str[:4].astype(int)
    pi = pi[pi["年"].between(2016, 2025)]
    HI = 150.0   # 纵轴上限：中际旭创 2017 年因重组并表增速达 1690%，截断显示以免压扁其余公司
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    others = [n for n in pi["名称"].unique() if n != "永鼎股份"]
    order = ["长飞光纤", "亨通光电", "中天科技", "烽火通信", "中际旭创", "通鼎互联"]
    others = sorted(others, key=lambda n: order.index(n) if n in order else 99)
    for i, nm in enumerate(others):
        g = pi[pi["名称"] == nm].sort_values("年")
        yoy = (g["TOTALOPERATEREVE"].pct_change() * 100).clip(-60, HI)
        ax.plot(g["年"], yoy, label=nm, lw=1.2, color=PALETTE[i % len(PALETTE)], alpha=0.9)
        over = g.loc[(g["TOTALOPERATEREVE"].pct_change() * 100) > HI, "年"]
        for yr in over:
            ax.annotate("↑", (yr, HI), ha="center", va="bottom", fontsize=9,
                        color=PALETTE[i % len(PALETTE)])
    g = pi[pi["名称"] == "永鼎股份"].sort_values("年")
    yoy = (g["TOTALOPERATEREVE"].pct_change() * 100).clip(-60, HI)
    ax.plot(g["年"], yoy, label="永鼎股份", lw=2.6, color=C_WARN, zorder=5, marker="o", ms=3.5)
    ax.axhline(0, color="#333333", lw=0.9)
    ax.set_ylim(-45, HI + 18)
    ax.set_title("同业公司营业收入同比增速（2017—2025）", pad=22)
    ax.set_ylabel("%")
    ax.legend(ncol=7, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 1.0),
              columnspacing=0.9, handlelength=1.5)
    _src(ax, "数据来源：东方财富F10核心指标（同业6家）、公司年度报告（永鼎股份）；作者整理。\n"
             "注：中际旭创 2017 年因重组并表营收增速达 1690%，已按纵轴上限截断（↑ 标示）。", y=-0.24)
    return _save(fig, "图2-2_同业营收增速.png")


def f_segment_mix(d: dict) -> str:
    t = t_segment_h1(d)
    t = t[t.index >= "2021H1"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bottom = np.zeros(len(t))
    order = ["光通信", "汽车线束", "电力工程", "超导及铜导体", "大数据应用", "其他"]
    colors = ["#1f4e79", "#c55a11", "#2e7d32", "#7030a0", "#bf9000", "#a6a6a6"]
    for c, col in zip(order, colors):
        if c in t.columns:
            v = t[c].fillna(0).values
            ax.bar(t.index, v, bottom=bottom, color=col, label=c, width=0.62)
            bottom += v
    ax.set_title("分产品营业收入结构（半年报口径，2021H1—2026H1）", pad=10)
    ax.set_ylabel("营业收入（亿元）")
    ax.legend(ncol=3, fontsize=7.5, loc="upper left")
    _src(ax, "数据来源：公司各期半年度报告“主营业务分产品情况”，作者整理")
    return _save(fig, "图2-3_分产品收入结构.png")


def f_segment_margin(d: dict) -> str:
    t = t_segment_margin_h1(d)
    t = t[t.index >= "2021H1"]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    for i, c in enumerate(["光通信", "汽车线束", "电力工程", "超导及铜导体"]):
        if c in t.columns:
            ax.plot(t.index, t[c], "o-", lw=2.2 if c == "光通信" else 1.5, ms=4,
                    color=PALETTE[i], label=c)
    ax.set_title("分产品毛利率（半年报口径，2021H1—2026H1）", pad=10)
    ax.set_ylabel("%")
    ax.legend(ncol=4, fontsize=7.5)
    _src(ax, "数据来源：公司各期半年度报告“主营业务分产品情况”，作者整理")
    return _save(fig, "图2-4_分产品毛利率.png")


# ---------------------------------------------------------------- 图 3 公司财务
def f_revenue_profit(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2016:2025]
    q = d["q3"]
    years = list(ra.index.astype(str)) + ["2026前三季度"]
    rev = list(ra["营业收入(亿元)"]) + [q["营业收入(亿元)"]]
    np_ = list(ra["归母净利润(亿元)"]) + [q["归母净利润(亿元)"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    x = np.arange(len(years))
    ax.bar(x - 0.2, rev, width=0.4, color=C_LIGHT, label="营业收入（亿元）", edgecolor=C_MAIN, lw=0.6)
    ax.set_ylabel("营业收入（亿元）")
    ax2 = ax.twinx()
    ax2.bar(x + 0.2, np_, width=0.4, color=C_SUB, label="归母净利润（亿元）", edgecolor="#8c3d0b", lw=0.6)
    ax2.axhline(0, color=C_WARN, lw=0.8, ls="--")
    ax2.set_ylabel("归母净利润（亿元）")
    ax.set_xticks(x)
    ax.set_xticklabels(years, rotation=30, ha="right")
    ax.grid(False)
    ax2.grid(False)
    for i, v in enumerate(np_):
        ax2.annotate(f"{v:.1f}", (x[i] + 0.2, v), ha="center",
                     va="bottom" if v >= 0 else "top", fontsize=7, color="#8c3d0b")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left")
    ax.set_title("营业收入与归母净利润（2016—2026Q3）", pad=10)
    _src(ax, "数据来源：公司年度报告、2026年第三季度报告")
    return _save(fig, "图3-1_营收与归母净利.png")


def f_margin(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2016:2025]
    q = d["q3"]
    years = list(ra.index.astype(str)) + ["2026Q3"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for c, col, mk in [("毛利率%", C_MAIN, "o"), ("归母净利率%", C_ACC, "s"), ("期间费用率%", C_SUB, "^")]:
        v = list(ra[c]) + [q.get(c, np.nan)]
        ax.plot(years, v, mk + "-", lw=2, ms=4.5, color=col, label=c.replace("%", "(%)"))
    ax.set_title("毛利率、归母净利率与期间费用率（2016—2026Q3）", pad=10)
    ax.set_ylabel("%")
    ax.legend(ncol=3)
    ax.tick_params(axis="x", rotation=30)
    # 2016 年及以前东财报表未单列研发费用，期间费用率不可比，故该线自 2017 年起
    _src(ax, "数据来源：公司年报、2026 年三季报，东方财富 F10。"
             "期间费用率自 2017 年起（此前研发费用未单列，口径不可比）")
    return _save(fig, "图3-2_盈利能力指标.png")


def f_dupont(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2016:2025]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    x = np.arange(len(ra))
    w = 0.26
    ax.bar(x - w, ra["归母净利率%"], width=w, color=C_MAIN, label="归母净利率(%)")
    ax.bar(x, ra["总资产周转率"] * 100, width=w, color=C_SUB, label="总资产周转率×100")
    ax.bar(x + w, ra["权益乘数"] * 20, width=w, color=C_ACC, label="权益乘数×20")
    ax.plot(x, ra["ROE%"], "o-", color=C_WARN, lw=2.4, ms=5, label="ROE(%)")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.set_ylim(-34, 74)          # 下界留白：2020 年 ROE -20.56% 不能被图例压住
    ax.set_xticks(x)
    ax.set_xticklabels(ra.index.astype(str), rotation=30)
    ax.set_title("杜邦分解：ROE = 归母净利率 × 总资产周转率 × 权益乘数", pad=10)
    ax.legend(ncol=4, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 0.005))
    _src(ax, "数据来源：公司年度报告；权益乘数与周转率已作比例缩放以便同轴展示")
    return _save(fig, "图3-3_杜邦分解.png")


def f_solvency(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2016:2025]
    q = d["q3"]
    years = list(ra.index.astype(str)) + ["2026Q3"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(years, list(ra["流动比率"]) + [q["流动比率"]], "o-", color=C_MAIN, lw=2, ms=4.5, label="流动比率")
    ax.plot(years, list(ra["速动比率"]) + [q["速动比率"]], "s-", color=C_ACC, lw=2, ms=4.5, label="速动比率")
    ax.axhline(1.0, color=C_GRAY, ls=":", lw=1)
    ax.axhline(2.0, color=C_GRAY, ls=":", lw=1)
    ax.set_ylabel("倍")
    ax2 = ax.twinx()
    ax2.plot(years, list(ra["资产负债率%"]) + [q["资产负债率%"]], "^-", color=C_WARN, lw=2, ms=4.5,
             label="资产负债率(%)")
    ax2.set_ylabel("资产负债率（%）")
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, ncol=3, loc="upper left")
    ax.tick_params(axis="x", rotation=30)
    ax.set_title("偿债能力：流动比率、速动比率与资产负债率", pad=10)
    _src(ax)
    return _save(fig, "图3-4_偿债能力.png")


def f_efficiency(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2016:2025]
    q = d["q3"]
    years = list(ra.index.astype(str)) + ["2026Q3*"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for c, col, mk in [("应收账款周转率", C_MAIN, "o"), ("存货周转率", C_SUB, "s"),
                       ("总资产周转率", C_ACC, "^")]:
        ax.plot(years, list(ra[c]) + [q.get(c, np.nan)], mk + "-", lw=2, ms=4.5, color=col, label=c)
    ax.set_ylabel("次/年")
    ax.legend(ncol=3)
    ax.tick_params(axis="x", rotation=30)
    ax.set_title("营运能力：主要资产周转率（2016—2026Q3）", pad=10)
    _src(ax, "数据来源：公司年度报告；*2026Q3已按3/4折算为年化口径")
    return _save(fig, "图3-5_营运能力.png")


def f_cashflow(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2016:2025]
    q = d["q3"]
    years = list(ra.index.astype(str)) + ["2026Q3"]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    x = np.arange(len(years))
    w = 0.26
    ax.bar(x - w, list(ra["经营现金流净额(亿元)"]) + [q["经营现金流净额(亿元)"]], width=w,
           color=C_MAIN, label="经营活动")
    ax.bar(x, list(ra["投资现金流净额(亿元)"]) + [q["投资现金流净额(亿元)"]], width=w,
           color=C_SUB, label="投资活动")
    ax.bar(x + w, list(ra["筹资现金流净额(亿元)"]) + [q["筹资现金流净额(亿元)"]], width=w,
           color=C_ACC, label="筹资活动")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(years, rotation=30)
    ax.set_ylabel("亿元")
    ax.legend(ncol=3)
    ax.set_title("三类活动现金流量净额（2016—2026Q3）", pad=10)
    _src(ax)
    return _save(fig, "图3-6_现金流量结构.png")


def f_earnings_quality(d: dict) -> str:
    ra = d["ra"].set_index("年度").loc[2018:2025]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    x = np.arange(len(ra))
    ax.bar(x - 0.2, ra["扣非占比%"], width=0.38, color=C_LIGHT, edgecolor=C_MAIN,
           label="扣非归母净利润/归母净利润(%)")
    ax.plot(x + 0.2, ra["净现比"], "o-", color=C_WARN, lw=2.2, ms=5, label="净现比（经营现金流/归母净利润）")
    ax.axhline(1.0, color=C_GRAY, ls=":", lw=1)
    ax.axhline(0, color="#333333", lw=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(ra.index.astype(str))
    ax.set_title("盈利质量：扣非占比与净现比（2018—2025）", pad=10)
    ax.legend(ncol=2, fontsize=8)
    _src(ax, "数据来源：公司年度报告；净现比为负说明经营现金流与账面利润方向背离")
    return _save(fig, "图3-7_盈利质量.png")


def f_2025_bridge(d: dict) -> str:
    """2025年利润来源拆解：主业经营利润 vs 投资收益"""
    p = d["panel"]
    r = p[p["报告期"] == "2025年报"].iloc[0]
    gross = (r["营业收入"] - r["营业成本"]) / 1e8
    exp = (r["销售费用"] + r["管理费用"] + r["研发费用"] + r["财务费用"]) / 1e8
    inv = r["投资收益"] / 1e8
    oth = r["其他收益"] / 1e8
    impair = ((r["资产减值损失"] if not pd.isna(r["资产减值损失"]) else 0) +
              (r["信用减值损失"] if not pd.isna(r["信用减值损失"]) else 0)) / 1e8
    core = gross - exp
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    labels = ["毛利", "期间费用", "主业经营利润", "投资收益\n(联营企业)", "其他收益\n及减值", "营业利润"]
    vals = [gross, -exp, core, inv, oth + impair, r["营业利润"] / 1e8]
    colors = [C_LIGHT, C_SUB, C_ACC if core >= 0 else C_WARN, C_MAIN, C_GRAY, C_MAIN]
    bars = ax.bar(labels, vals, color=colors, width=0.6, edgecolor="#333333", lw=0.5)
    for b, v in zip(bars, vals):
        ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v), ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=8.5, fontweight="bold")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.set_ylabel("亿元")
    ax.set_title("2025年营业利润来源拆解：投资收益贡献超过主业经营利润", pad=10)
    _src(ax, "数据来源：公司2025年年度报告；投资收益2.85亿元主要为联营企业东昌投资权益法确认收益")
    return _save(fig, "图3-8_2025利润拆解.png")


# ---------------------------------------------------------------- 图 4 同业
def f_peer_radar(d: dict) -> str:
    """2025年报同业财务特征雷达图。5 个轴统一到「百分制」量纲，便于同图比较：
       毛利率%、净利率%、加权ROE%、偿债安全度(100-资产负债率)、总资产周转率(次×100)"""
    pi = _peer_plus_yd(d)
    p25 = pi[pi["REPORT_DATE_NAME"] == "2025年报"].dropna(subset=["ROEJQ"]).copy()
    picks = ["永鼎股份", "长飞光纤", "亨通光电", "中天科技", "烽火通信"]
    p25 = p25[p25["名称"].isin(picks)]
    if len(p25) < 3:
        return ""
    order = {n: i for i, n in enumerate(picks)}
    p25 = p25.sort_values("名称", key=lambda s: s.map(order))
    labels = ["毛利率(%)", "净利率(%)", "加权ROE(%)",
              "偿债安全度\n(100-资产负债率)", "总资产周转\n(次×100)"]
    ang = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(5.8, 5.2), subplot_kw=dict(polar=True))
    plain = [n for n in picks if n != "永鼎股份"]
    for _, row in p25.iterrows():
        vals = [row["XSMLL"], row["XSJLL"], row["ROEJQ"],
                100 - row["ZCFZL"], row["TOAZZL"] * 100]
        vals = [float(np.clip(v, 0, 100)) for v in vals]
        vals += vals[:1]
        own = row["名称"] == "永鼎股份"
        col = C_WARN if own else PALETTE[plain.index(row["名称"]) % len(PALETTE)]
        ax.plot(ang, vals, lw=2.4 if own else 1.2, color=col, label=row["名称"],
                zorder=6 if own else 3, marker="o" if own else None, ms=3)
        ax.fill(ang, vals, alpha=0.10 if own else 0.0, color=col)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color=C_GRAY)
    ax.set_title("2025年同业公司财务特征对比（雷达图）", pad=26)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.075), ncol=5, fontsize=8,
              handlelength=1.6, columnspacing=1.1)
    _src(ax, "数据来源：东方财富F10核心指标（同业6家）、公司年度报告（永鼎股份）；作者整理。\n"
             "注：各轴均为百分制，总资产周转率按「次×100」折算；偿债安全度越高表示杠杆越低。", y=-0.245)
    return _save(fig, "图4-1_同业雷达图.png")


def f_peer_valuation(d: dict) -> str:
    pi = _peer_plus_yd(d)
    picks = ["永鼎股份", "长飞光纤", "亨通光电", "中天科技", "烽火通信"]
    p = pi[(pi["REPORT_DATE_NAME"] == "2025年报") & (pi["名称"].isin(picks))].dropna(subset=["ROEJQ"])
    if p.empty:
        return ""
    p = p.sort_values("名称", key=lambda s: s.map({n: i for i, n in enumerate(picks)}))
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = np.arange(len(p))
    ax.bar(x - 0.2, p["XSMLL"], width=0.38, color=C_LIGHT, edgecolor=C_MAIN, label="毛利率(%)")
    ax.bar(x + 0.2, p["ROEJQ"], width=0.38, color=C_SUB, label="加权ROE(%)")
    for xi, v in zip(x - 0.2, p["XSMLL"]):
        ax.annotate(f"{v:.1f}", (xi, v), ha="center", va="bottom", fontsize=7, color=C_MAIN)
    for xi, v in zip(x + 0.2, p["ROEJQ"]):
        ax.annotate(f"{v:.1f}", (xi, v), ha="center", va="bottom" if v >= 0 else "top", fontsize=7, color=C_SUB)
    ax.set_xticks(x)
    ax.set_xticklabels(p["名称"])
    ax.set_ylabel("%")
    ax.axhline(0, color="#333333", lw=0.9)
    ax.legend(ncol=2, loc="upper right")
    ax.set_title("2025年同业公司盈利能力对比", pad=10)
    _src(ax, "数据来源：东方财富F10核心指标（同业6家）、公司年度报告（永鼎股份）；作者整理")
    return _save(fig, "图4-2_同业盈利对比.png")


# ---------------------------------------------------------------- 图 5 估值
def f_pe_band(d: dict) -> str:
    """PE(TTM) 历史走势与分位。因 2024—2026 年利润基数极低使 PE 一度冲高至千倍，
    线性坐标会把 20—60 倍的常态区间压扁，故纵轴取对数。"""
    v = d["val"].dropna(subset=["PE_TTM"]).copy()
    v = v[v["日期"] >= "2017-01-01"]
    v = v[v["PE_TTM"] > 0]
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    ax.plot(v["日期"], v["PE_TTM"], lw=1.1, color=C_MAIN)
    q = v["PE_TTM"].quantile([0.1, 0.5, 0.9])
    ax.set_yscale("log")
    ax.set_ylim(8, 1600)
    ax.set_yticks([10, 20, 30, 50, 100, 200, 500, 1000])
    ax.get_yaxis().set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}"))
    ax.get_yaxis().set_minor_formatter(FuncFormatter(lambda x, _: ""))
    lines = [(0.1, C_ACC, "10%分位"), (0.5, C_GRAY, "中位数"), (0.9, C_WARN, "90%分位")]
    for pct, col, lb in lines:
        ax.axhline(q[pct], color=col, ls="--", lw=1, zorder=2)
    # 分位标签统一放在左上空白区，避免与曲线/虚线交叉
    y0 = 0.965
    for k, (pct, col, lb) in enumerate(lines):
        ax.text(0.018, y0 - k * 0.072, f"{lb}  {q[pct]:.0f}×", transform=ax.transAxes,
                fontsize=8, color=col, va="top", ha="left", zorder=9,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=col, lw=0.6, alpha=0.92))
    ax.set_ylabel("PE(TTM，倍，对数坐标)")
    ax.set_title("永鼎股份 PE(TTM) 历史走势与分位（2017—2026.10）", pad=10)
    _src(ax, "数据来源：腾讯财经不复权收盘价、公司历次定期报告；TTM净利润按其实际公告日生效。\n"
             "注：纵轴取对数；2024年以来PE冲高系净利润基数极低所致，不宜直接作为估值锚。")
    return _save(fig, "图5-1_PE_Band.png")


def f_pb_roe(d: dict) -> str:
    """PB—ROE 匹配：点＝各年度 PB 中位数与当年 ROE，连线为 2017→2025 的估值—盈利迁移路径"""
    ra = d["ra"].set_index("年度")
    v = d["val"].dropna(subset=["PB"])
    years = list(range(2017, 2026))
    xs = [ra.loc[y, "ROE%"] for y in years]
    ys = [v[v["日期"].dt.year == y]["PB"].median() for y in years]
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.plot(xs, ys, color="#9e9e9e", lw=1.0, ls="-", zorder=1, alpha=0.8)
    ax.scatter(xs, ys, s=58, color=C_MAIN, zorder=4, label="年度中位PB（2017—2025）")
    # 手工错开标注方位，避免 ROE≈1.5~7.6、PB≈1.8~2.2 的密集区文字互相压盖
    off = {2017: (7, 4), 2018: (8, 2), 2019: (-4, -13), 2020: (9, 4),
           2021: (-4, -14), 2022: (8, -12), 2023: (7, 5), 2024: (8, -4), 2025: (7, 4)}
    for y, x, yy in zip(years, xs, ys):
        ax.annotate(str(y), (x, yy), textcoords="offset points", xytext=off[y], fontsize=7.5,
                    color="#404040", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
    last = v.iloc[-1]
    roe_ann = d["q3"]["ROE%"] * 4 / 3
    ax.scatter([roe_ann], [last["PB"]], s=150, marker="*", color=C_WARN, zorder=6,
               label=f"2026Q3（ROE年化≈{roe_ann:.1f}%，PB={last['PB']:.1f}）")
    ax.annotate(f"2026Q3\n估值显著高于\n盈利所对应的历史区间", (roe_ann, last["PB"]),
                textcoords="offset points", xytext=(-14, -34), ha="right", fontsize=7.5,
                color=C_WARN, zorder=7,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec=C_WARN, lw=0.6, alpha=0.9))
    ax.axhline(v["PB"].median(), color=C_GRAY, ls=":", lw=1)
    ax.set_xlim(-25, 27)
    ax.set_xlabel("ROE（%）")
    ax.set_ylabel("PB（倍）")
    ax.set_title("PB—ROE 匹配关系（2017—2026Q3）", pad=10)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(0.0, 1.0))
    _src(ax, "数据来源：腾讯财经不复权收盘价与报告期每股净资产、公司定期报告；ROE为加权平均净资产收益率。\n"
             "注：2026Q3为前三季度累计ROE（15.80%）按4/3简单年化，仅供同尺度比较。")
    return _save(fig, "图5-2_PB_ROE.png")


def f_val_percentile(d: dict) -> str:
    v = d["val"].dropna(subset=["PE_TTM"]).copy()
    v = v[v["日期"] >= "2017-01-01"]
    cur = v.iloc[-1]
    items = {
        "PE(TTM)": (cur["PE_TTM"], v["PE_TTM"]),
        "PB": (cur["PB"], d["val"].dropna(subset=["PB"])["PB"]),
        "PS(TTM)": (cur["PS_TTM"], d["val"].dropna(subset=["PS_TTM"])["PS_TTM"]),
    }
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    y = np.arange(len(items))
    for i, (k, (c, s)) in enumerate(items.items()):
        pct = (s <= c).mean() * 100
        ax.barh(i, pct, color=C_WARN if pct > 70 else (C_MAIN if pct > 30 else C_ACC), height=0.5)
        ax.annotate(f"{c:.1f}倍（历史{pct:.0f}%分位）", (pct, i), va="center", ha="left",
                    fontsize=9, xytext=(4, 0), textcoords="offset points")
    ax.set_yticks(y)
    ax.set_yticklabels(list(items.keys()))
    ax.set_xlim(0, 118)
    ax.set_xlabel("当前估值对应的历史分位（%）")
    ax.set_title("当前估值的历史分位水平（2017年以来）", pad=10)
    _src(ax, "数据来源：作者基于不复权收盘价、报告期股本与TTM净利润计算")
    return _save(fig, "图5-3_估值分位.png")


def f_dcf_sens(d: dict, wacc=(0.09, 0.10, 0.11), g=(0.02, 0.025, 0.03)) -> str:
    base_fcf = 6.0
    growth = [0.30, 0.18, 0.10, 0.06]
    res = np.zeros((len(wacc), len(g)))
    for i, w in enumerate(wacc):
        for j, gg in enumerate(g):
            pv, f = 0.0, base_fcf
            for t, gr in enumerate(growth, start=1):
                f *= (1 + gr)
                pv += f / (1 + w) ** t
            tv = f * (1 + gg) / (w - gg)
            pv += tv / (1 + w) ** len(growth)
            res[i, j] = pv
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    im = ax.imshow(res, cmap="RdYlGn_r", aspect="auto")
    ax.set_xticks(range(len(g)))
    ax.set_xticklabels([f"{x*100:.1f}%" for x in g])
    ax.set_yticks(range(len(wacc)))
    ax.set_yticklabels([f"{x*100:.0f}%" for x in wacc])
    for i in range(len(wacc)):
        for j in range(len(g)):
            ax.annotate(f"{res[i, j]:.0f}", (j, i), ha="center", va="center", fontsize=9, color="black")
    ax.set_xlabel("永续增长率 g")
    ax.set_ylabel("WACC")
    ax.set_title("自由现金流折现：企业价值敏感性（亿元）", pad=10)
    ax.grid(False)
    _src(ax, "假设：基期自由现金流6.0亿元，2027—2030年增速30%/18%/10%/6%")
    return _save(fig, "图5-4_DCF敏感性.png")


def f_scorecard(d: dict) -> str:
    dims = ["成长性", "盈利能力", "盈利质量", "偿债安全", "营运效率", "估值吸引力"]
    scores = [92, 78, 85, 42, 55, 25]
    ang = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    ang += ang[:1]
    s = scores + scores[:1]
    fig, ax = plt.subplots(figsize=(5.2, 4.6), subplot_kw=dict(polar=True))
    ax.plot(ang, s, lw=2.2, color=C_MAIN)
    ax.fill(ang, s, alpha=0.18, color=C_MAIN)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels(dims, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color=C_GRAY)
    ax.set_title("永鼎股份投资价值六维评分（满分100）", pad=22)
    return _save(fig, "图5-5_综合评分.png")


ALL_FIGS = [f_macro_growth, f_macro_money, f_peer_index, f_peer_revenue_growth, f_segment_mix,
            f_segment_margin, f_revenue_profit, f_margin, f_dupont, f_solvency, f_efficiency,
            f_cashflow, f_earnings_quality, f_2025_bridge, f_peer_radar, f_peer_valuation,
            f_pe_band, f_pb_roe, f_val_percentile, f_dcf_sens, f_scorecard]


def build_all(silent: bool = False) -> list:
    d = load_all()
    out = []
    for fn in ALL_FIGS:
        try:
            p = fn(d)
            if p:
                out.append(p)
                if not silent:
                    print("  ✓", os.path.basename(p))
        except Exception as e:
            print(f"  ✗ {fn.__name__}: {type(e).__name__} {e}")
    return out


if __name__ == "__main__":
    print("生成图表 ...")
    paths = build_all()
    print(f"完成 {len(paths)} 张 →", FIG)
