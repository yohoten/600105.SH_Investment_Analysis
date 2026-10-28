# -*- coding: utf-8 -*-
"""streamlit_app.py —— 永鼎股份（600105.SH）投资价值分析 · 交互看板

《证券投资学》实践课配套应用。设计原则：
  1) **不重算口径**：全部指标复用 scripts/analysis_lib.py（与报告、Notebook 同源），
     避免"网页上的数"和"报告里的数"打架；
  2) **只读本地数据**：读 data/processed/*.csv 与 data/raw/*，不联网；
  3) **涨红跌绿**：遵循 A 股习惯，涨用红色、跌用绿色。

启动：
    streamlit run streamlit_app.py

兼容性：
    本机有两套环境——Python 3.11（streamlit 1.36，PATH 里 `streamlit` 命令默认指向它）
    与 Python 3.12（streamlit 1.66）。二者 API 差异较大（segmented_control、
    metric(border=)、width="stretch" 等均为新版才有）。文件顶部的「版本兼容层」
    统一做能力检测，使同一份代码在两个版本下都能运行：新版保留新特性，旧版自动降级。
"""
from __future__ import annotations

import json
import re
import sys
from inspect import signature
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "scripts"))

import analysis_lib as A  # noqa: E402  （必须放在 sys.path 之后）

# ============================================================== 版本兼容层
# 下面的包装函数屏蔽 streamlit 1.36 / 1.66 的 API 差异，业务代码一律调用包装函数，
# 不再直接使用 st.dataframe / st.plotly_chart / st.image / st.metric 的新版参数。

def _st_ver() -> tuple:
    m = re.match(r"(\d+)\.(\d+)", st.__version__ or "")
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def _has_param(fn, name: str) -> bool:
    try:
        return name in signature(fn).parameters
    except (TypeError, ValueError):
        return False


ST_VER = _st_ver()
HAS_SEG = hasattr(st, "segmented_control")             # 1.40+
HAS_METRIC_BORDER = _has_param(st.metric, "border")    # 1.44+
HAS_CONTAINER_BORDER = _has_param(st.container, "border")
HAS_STR_WIDTH = ST_VER >= (1, 50)                      # width="stretch" / height="content"


def _wide() -> dict:
    """铺满容器宽度：新版 width="stretch"，旧版 use_container_width=True。"""
    return {"width": "stretch"} if HAS_STR_WIDTH else {"use_container_width": True}


def chart(fig, **kw):
    """plotly 图。旧版 plotly_chart 没有 width 参数，只能用 use_container_width。"""
    if HAS_STR_WIDTH:
        st.plotly_chart(fig, width="stretch", theme=None, **kw)
    else:
        st.plotly_chart(fig, use_container_width=True, theme=None, **kw)


def show_image(src, caption=None):
    """图片：旧版用 use_column_width=True（不是 use_container_width）。"""
    if HAS_STR_WIDTH:
        st.image(src, caption=caption, width="stretch")
    else:
        st.image(src, caption=caption, use_column_width=True)


def seg(label, options, default=0, **kw):
    """分段控件：新版 segmented_control，旧版降级为横向 radio。"""
    if HAS_SEG:
        return st.segmented_control(label, options, default=options[default], **kw)
    return st.radio(label, options, index=default, horizontal=True, **kw)


def metric(scope, label, value, delta=None, delta_color="normal",
           help=None, border=True):
    """指标卡：新版直接 border=True；旧版用带边框容器模拟同样的卡片外观。"""
    kw = {}
    if help is not None:
        kw["help"] = help
    if delta is not None:
        kw["delta"] = delta
        kw["delta_color"] = delta_color
    if not border:
        scope.metric(label, value, **kw)
    elif HAS_METRIC_BORDER:
        scope.metric(label, value, border=True, **kw)
    else:
        box = scope.container(border=True) if HAS_CONTAINER_BORDER else scope.container()
        box.metric(label, value, **kw)


def dl_button(scope, label, data, file_name, mime):
    """下载按钮：旧版用 use_container_width=True。"""
    if HAS_STR_WIDTH:
        scope.download_button(label, data, file_name, mime, width="stretch")
    else:
        scope.download_button(label, data, file_name, mime, use_container_width=True)


# ------------------------------------------------------------------ 常量
C_MAIN = "#1f4e79"      # 主色·深蓝
C_SUB = "#c55a11"       # 辅色·橙
C_ACC = "#2e7d32"       # 强调·绿
C_WARN = "#c00000"      # 强调·红
C_LIGHT = "#9dc3e6"
C_GRAY = "#7f7f7f"
UP, DOWN = "#c00000", "#2e7d32"   # A 股：涨红跌绿
INK = "#1f2937"

SCORES = {"成长性": 92, "盈利能力": 78, "盈利质量": 85,
          "偿债安全": 42, "营运效率": 55, "估值吸引力": 25}

FIGS = [
    ("第二章 宏观", [
        ("图1-1_宏观GDP_CPI_PPI.png", "图2-1　2016—2025 年中国 GDP、CPI 与 PPI 同比增速"),
        ("图1-2_宏观M2_PMI.png", "图2-2　货币供应与制造业景气：M2 增速与制造业 PMI"),
    ]),
    ("第三章 行业", [
        ("图2-1_同业股价指数.png", "图3-1　永鼎股份与同业公司股价走势（2016-01-04=100）"),
        ("图2-2_同业营收增速.png", "图3-2　同业公司营业收入同比增速（2017—2025）"),
    ]),
    ("第四章 公司", [
        ("图2-3_分产品收入结构.png", "图4-1　分产品营业收入结构（2021H1—2026H1）"),
        ("图2-4_分产品毛利率.png", "图4-2　分产品毛利率（2021H1—2026H1）"),
    ]),
    ("第五章 财务", [
        ("图3-1_营收与归母净利.png", "图5-1　营业收入与归母净利润（2016—2026Q3）"),
        ("图3-2_盈利能力指标.png", "图5-2　毛利率、净利率与期间费用率（2016—2026Q3）"),
        ("图3-3_杜邦分解.png", "图5-3　ROE 的杜邦三因子分解（2016—2026Q3）"),
        ("图3-4_偿债能力.png", "图5-4　流动比率、速动比率与资产负债率（2016—2026Q3）"),
        ("图3-5_营运能力.png", "图5-5　应收账款、存货与总资产周转率（2016—2026Q3）"),
        ("图3-6_现金流量结构.png", "图5-6　经营、投资、筹资活动现金流净额（2016—2026Q3）"),
        ("图3-7_盈利质量.png", "图5-7　净现比与扣非归母净利润占比（2016—2026Q3）"),
        ("图3-8_2025利润拆解.png", "图5-8　2025 年利润构成瀑布拆解（亿元）"),
        ("图4-1_同业雷达图.png", "图5-9　2025 年同业公司财务特征对比（雷达图）"),
        ("图4-2_同业盈利对比.png", "图5-10　2025 年同业公司盈利能力对比"),
    ]),
    ("第六章 估值", [
        ("图5-1_PE_Band.png", "图6-1　PE(TTM) 历史走势与分位（2017—2026.10，对数坐标）"),
        ("图5-3_估值分位.png", "图6-2　当前估值所对应的历史分位"),
        ("图5-2_PB_ROE.png", "图6-3　PB—ROE 匹配关系（2017—2026Q3）"),
        ("图5-4_DCF敏感性.png", "图6-4　自由现金流折现的企业价值敏感性（亿元）"),
    ]),
    ("第七章 结论", [
        ("图5-5_综合评分.png", "图7-1　永鼎股份投资价值六维评分"),
    ]),
]

# ------------------------------------------------------------------ 页面设置
st.set_page_config(page_title="永鼎股份 600105.SH · 投资价值分析",
                   page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

CSS = """
<style>
  .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px;}
  #MainMenu, footer {visibility: hidden;}
  h1, h2, h3, h4 {color: #1f2937; font-weight: 700; letter-spacing: .2px;}
  .hero {
      background: linear-gradient(120deg, #1f4e79 0%, #2f6ea5 60%, #3d87c4 100%);
      border-radius: 14px; padding: 22px 26px; color: #fff; margin-bottom: 18px;
  }
  .hero h1 {color: #fff; font-size: 26px; margin: 0 0 6px 0;}
  .hero p {color: #dbe9f6; margin: 0; font-size: 13.5px; line-height: 1.7;}
  .hero .tag {
      display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.28);
      border-radius: 999px; padding: 2px 11px; font-size: 12px; margin-right: 8px; margin-top: 10px;
  }
  .kpi {
      background: #fff; border: 1px solid #e4e9f0; border-radius: 12px;
      padding: 14px 16px 12px 16px; height: 100%;
      box-shadow: 0 1px 2px rgba(16,24,40,.04);
  }
  .kpi .lab {color: #6b7280; font-size: 12.5px; margin-bottom: 6px; letter-spacing: .3px;}
  .kpi .val {font-size: 25px; font-weight: 700; line-height: 1.15; font-variant-numeric: tabular-nums;}
  .kpi .sub {color: #8b95a5; font-size: 11.5px; margin-top: 6px;}
  .verdict {
      border-left: 5px solid #c00000; background: #fff5f5; border-radius: 8px;
      padding: 14px 18px; color: #4a1a1a; font-size: 14px; line-height: 1.85;
  }
  .note {
      background: #f6f8fb; border: 1px solid #e4e9f0; border-radius: 10px;
      padding: 12px 16px; color: #475467; font-size: 13px; line-height: 1.8;
  }
  .sec {
      font-size: 15px; font-weight: 700; color: #1f4e79; margin: 6px 0 10px 0;
      padding-left: 10px; border-left: 4px solid #1f4e79;
  }
  div[data-testid="stMetricValue"] {font-size: 1.35rem;}
  .stTabs [data-baseweb="tab"] {font-size: 14px;}
  img {border-radius: 6px;}
  /* 顶部工具栏（Deploy / Stop / 运行状态）不属于看板内容，隐藏 */
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stAppDeployButton"], [data-testid="stStatusWidget"] {display: none !important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ 数据层
@st.cache_data(show_spinner="正在读取本地数据底稿 …")
def get_data() -> dict:
    return A.load_all()


@st.cache_data(show_spinner=False)
def get_snapshot() -> dict:
    p = BASE / "data" / "raw" / "market" / "实时快照.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def get_pct(d: dict) -> dict:
    """估值分位：PE 取 2017 年起（2016 年 TTM 不可得），PB/PS 取全样本 —— 与报告口径一致。"""
    v = d["val"]
    vp = v.dropna(subset=["PE_TTM"])
    vp = vp[vp["日期"] >= "2017-01-01"]
    cur = v.iloc[-1]
    out = {}
    for key, s, c in [("PE", vp["PE_TTM"], cur["PE_TTM"]),
                      ("PB", v.dropna(subset=["PB"])["PB"], cur["PB"]),
                      ("PS", v.dropna(subset=["PS_TTM"])["PS_TTM"], cur["PS_TTM"])]:
        out[key] = (float(c), float((s <= c).mean() * 100), int(len(s)))
    return out


def get_main_profit(d: dict) -> pd.DataFrame:
    """主业经营利润 = 毛利 − 期间费用（穿透"扣非占比"的局限，与报告第五章一致）"""
    p = d["panel"]
    rows = []
    periods = [f"{y}年报" for y in range(2016, 2026)] + ["2026三季报"]

    def _n(v) -> float:
        # 注意：不能写 `r.get(c) or 0` —— NaN 在 Python 里是真值，
        # `NaN or 0` 返回 NaN，会让整列变成空值（2016 年研发费用就是空）。
        return 0.0 if v is None or pd.isna(v) else float(v)

    for rp in periods:
        row = p[p["报告期"] == rp]
        if row.empty:
            continue
        r = row.iloc[0]
        rev = r["营业收入"] / 1e8
        cost = r["营业成本"] / 1e8
        exp = sum(_n(r.get(c)) for c in ["销售费用", "管理费用", "研发费用", "财务费用"]) / 1e8
        gp = rev - cost
        rows.append({"期间": rp.replace("年报", "").replace("三季报", "Q3"),
                     "营业收入": rev, "毛利": gp, "期间费用": exp,
                     "主业经营利润": gp - exp, "投资收益": _n(r.get("投资收益")) / 1e8})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def get_peer_return(d: dict) -> pd.DataFrame:
    px = d["peer_px"].copy()
    px["名称"] = px["名称"].astype(str).str.replace(" ", "")
    px = px.dropna(subset=["收盘"]).sort_values("日期")
    start = px["日期"].min()
    out = []
    for name, g in px.groupby("名称"):
        g = g.sort_values("日期")
        out.append({"名称": name,
                    "起始": g["日期"].iloc[0].strftime("%Y-%m-%d"),
                    "收盘": g["收盘"].iloc[-1],
                    "区间涨幅%": (g["收盘"].iloc[-1] / g["收盘"].iloc[0] - 1) * 100})
    # 补入本公司（同业接口不含 600105）
    p = d["px"].sort_values("日期")
    out.append({"名称": "永鼎股份", "起始": p["日期"].iloc[0].strftime("%Y-%m-%d"),
                "收盘": p["收盘"].iloc[-1],
                "区间涨幅%": (p["收盘"].iloc[-1] / p["收盘"].iloc[0] - 1) * 100})
    df = pd.DataFrame(out).sort_values("区间涨幅%", ascending=False)
    df.attrs["start"] = start.strftime("%Y-%m-%d")
    return df


# ------------------------------------------------------------------ 绘图工具
def style(fig, height=340, legend_top=True, showlegend=True):
    """统一图表外观。

    margin 只留很小的基础值，四轴一律 automargin=True —— 让 Plotly 自己
    把刻度标签需要的空间撑出来。若把 margin 写死成 8px，轴标签会被裁掉：
    最初版本就因此丢了全部横轴年份和横向条形图的公司名。
    """
    fig.update_layout(
        height=height, margin=dict(l=6, r=12, t=34, b=6),
        font=dict(family="Microsoft YaHei, SimHei, sans-serif", size=12, color=INK),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        # 默认 "convert" 会把 "8.0%" 这类字符串当数字并丢掉百分号，
        # 热力图的 WACC / 永续增长率类目会被显示成 8、9、10。
        autotypenumbers="strict",
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#d0d5dd"),
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)") if legend_top else
               dict(orientation="h", yanchor="top", y=-0.16, x=0, font=dict(size=11)),
    )
    # 不画刻度短线：右侧副轴的刻度短线紧贴数字，视觉上会被读成负号（−30.6）
    fig.update_xaxes(showgrid=False, linecolor="#e4e9f0",
                     zeroline=False, ticks="", automargin=True,
                     tickfont=dict(size=11))
    fig.update_yaxes(gridcolor="#f0f2f5", zeroline=False, linecolor="#e4e9f0",
                     ticks="", automargin=True, tickfont=dict(size=11))
    return fig


def kpi(col, label, value, sub="", color=INK):
    col.markdown(
        f'<div class="kpi"><div class="lab">{label}</div>'
        f'<div class="val" style="color:{color}">{value}</div>'
        f'<div class="sub">{sub}</div></div>',
        unsafe_allow_html=True)


def sec(title):
    st.markdown(f'<div class="sec">{title}</div>', unsafe_allow_html=True)


def table(df, fmt="{:,.2f}", height=None, index=True):
    """数值列按 fmt 格式化，文本列（如"说明""增速路径"）原样输出。

    两个坑（均已实测确认）：
      1) 直接 df.style.format(fmt) 会把字符串列也套上 "{:,.2f}"，抛
         ValueError: Unknown format code 'f' for object of type 'str'；
      2) Streamlit 的表格把 null 渲染成 "None"，Styler 的 na_rep 与
         column_config 都管不住——只有预先转成字符串才能显示破折号。
         故仅对"确实含空值"的列转字符串（其余列保持数值型，右对齐）。
    """
    out = df.copy()
    for c in out.select_dtypes("number").columns:
        # 仅对"确实含空值"的列转字符串：既能显示破折号，又不牺牲其余数值列的右对齐
        if out[c].isna().any():
            out[c] = out[c].map(lambda v, f=fmt: "—" if pd.isna(v) else f.format(v))
    extra = {}
    if height is not None:
        # 旧版（<1.50）只接受整数像素高度，"content" 之类的字符串会被当成 int 解析而报错，
        # 此时直接省略 height——表格按行数自适应，效果与 "content" 一致。
        if isinstance(height, int) or HAS_STR_WIDTH:
            extra["height"] = height
    st.dataframe(out.style.format({c: fmt for c in out.select_dtypes("number").columns},
                                  na_rep="—"),
                 hide_index=not index, **_wide(), **extra)


# ------------------------------------------------------------------ 侧边栏
d = get_data()
snap = get_snapshot()
pct = get_pct(d)
val = d["val"]
last = val.iloc[-1]
q3 = d["q3"]
ra = d["ra"].set_index("年度")
snap_chg = float(snap.get("涨跌幅%", 0) or 0)
snap_px = float(snap.get("最新价", last["收盘"]) or last["收盘"])

with st.sidebar:
    st.markdown(
        '<div style="font-size:20px;font-weight:800;color:#1f4e79;line-height:1.3">'
        '永鼎股份<br><span style="font-size:13px;font-weight:500;color:#6b7280">600105.SH · 投资价值分析</span></div>',
        unsafe_allow_html=True)
    st.write("")
    nav = st.radio(
        "导航",
        ["① 概览", "② 行情与估值", "③ 财务五维", "④ 同业对比",
         "⑤ 宏观与行业", "⑥ 估值模型", "⑦ 图表墙", "⑧ 数据与说明"],
        key="nav", label_visibility="collapsed")
    st.divider()
    st.markdown(
        f'<div class="note" style="font-size:12.5px">'
        f'<b>数据快照</b><br>'
        f'交易日：{pd.to_datetime(last["日期"]).strftime("%Y-%m-%d")}<br>'
        f'收盘：<b>{snap_px:.2f}</b> 元　'
        f'<span style="color:{UP if snap_chg >= 0 else DOWN}">{snap_chg:+.2f}%</span><br>'
        f'总市值：{last["总市值(亿元)"]:.2f} 亿元<br>'
        f'PE(TTM)：{last["PE_TTM"]:.2f}　PB：{last["PB"]:.2f}<br>'
        f'数据截止：2026 年三季报'
        f'</div>', unsafe_allow_html=True)
    st.caption("数据来源：腾讯财经、东方财富 F10、巨潮资讯；本地底稿 2016—2026。")
    st.caption("口径与《投资分析报告》、Notebook 完全一致。")


# ================================================================== ① 概览
if nav.startswith("①"):
    st.markdown(
        '<div class="hero">'
        '<h1>江苏永鼎股份（600105.SH）投资价值分析</h1>'
        '<p>基于"宏观 — 行业 — 公司 — 估值"框架的基本面研究　|　'
        '分析主体 2021—2026，数据底稿向前延伸至 2016（10 年）</p>'
        '<span class="tag">成长性 92</span><span class="tag">盈利质量 85</span>'
        '<span class="tag">偿债安全 42</span><span class="tag">估值吸引力 25</span>'
        '</div>', unsafe_allow_html=True)

    c = st.columns(4)
    kpi(c[0], "最新收盘价", f"{snap_px:.2f} 元",
        f'<span style="color:{UP if snap_chg >= 0 else DOWN}">{snap_chg:+.2f}%　'
        f'{"涨" if snap_chg >= 0 else "跌"}</span>',
        UP if snap_chg >= 0 else DOWN)
    kpi(c[1], "总市值", f'{last["总市值(亿元)"]:.0f} 亿元', f"总股本 {last['股本'] / 1e8:.2f} 亿股")
    kpi(c[2], "PE (TTM)", f'{last["PE_TTM"]:.1f} 倍',
        f'历史 {pct["PE"][1]:.0f}% 分位（2017 年以来）')
    kpi(c[3], "PB (MRQ)", f'{last["PB"]:.2f} 倍',
        f'历史 {pct["PB"][1]:.0f}% 分位', C_WARN)

    c = st.columns(4)
    kpi(c[0], "PS (TTM)", f'{last["PS_TTM"]:.2f} 倍', f'历史 {pct["PS"][1]:.0f}% 分位')
    kpi(c[1], "2026 前三季营收", f'{q3["营业收入(亿元)"]:.2f} 亿',
        f'同比 {q3["营收增长率%"]:+.1f}%', UP)
    kpi(c[2], "2026 前三季归母", f'{q3["归母净利润(亿元)"]:.2f} 亿',
        f'同比 {q3["归母净利增长率%"]:+.1f}%', UP)
    kpi(c[3], "2026 前三季 ROE", f'{q3["ROE%"]:.2f}%', "加权平均，未年化")

    st.write("")
    st.markdown(
        '<div class="verdict"><b>结论：谨慎看待（Hold / 观望）</b>　——　'
        '基本面改善是真的，但价格已提前兑现：<b>好公司、贵价格</b>。<br>'
        f'2026 年前三季度扣非归母 <b>{q3["扣非归母净利润(亿元)"]:.2f} 亿元</b>、占归母 <b>{q3["扣非占比%"]:.1f}%</b>，'
        '投资收益仅 0.12 亿元，是十年来第一次由主业真实驱动的盈利；'
        '但 PB 处于 2017 年以来 92% 分位、PS 处于 91% 分位，'
        '反解需未来四年自由现金流复合增速 <b>约 55%</b> 才能支撑当前市值（精确值 55.7%，见第 6 页）。'
        '</div>', unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1.45, 1], gap="medium")
    with left:
        sec("近三年股价（前复权，元）")
        v3 = val[val["日期"] >= (val["日期"].max() - pd.Timedelta(days=365 * 3))]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=v3["日期"], y=v3["收盘"], name="收盘价",
                                 line=dict(color=C_MAIN, width=1.6),
                                 fill="tozeroy", fillcolor="rgba(31,78,121,.08)"))
        style(fig, height=330, showlegend=False).update_layout(
            xaxis=dict(tickformat="%Y-%m"))
        chart(fig)

    with right:
        sec("六维评分")
        cats = list(SCORES)
        fig = go.Figure(go.Scatterpolar(
            r=list(SCORES.values()) + [list(SCORES.values())[0]],
            theta=cats + [cats[0]], fill="toself",
            fillcolor="rgba(31,78,121,.16)", line=dict(color=C_MAIN, width=2)))
        style(fig, height=330, showlegend=False).update_layout(
            polar=dict(radialaxis=dict(range=[0, 100], showline=False, showticklabels=False,
                                       gridcolor="#e4e9f0"),
                       angularaxis=dict(gridcolor="#e4e9f0", tickfont=dict(size=11))),
            margin=dict(l=46, r=46, t=30, b=24))
        chart(fig)

    sec("三条主线")
    a, b, cc = st.columns(3, gap="medium")
    with a:
        st.markdown(
            '<div class="note"><b>① 主业真的反转了</b><br>'
            f'毛利率 13.89%（2025）→ <b>{q3["毛利率%"]:.2f}%</b>（2026Q3），'
            '光通信板块毛利率 58.52%，AI 算力订单是主因。<br>'
            '而 2025 年的 2.34 亿归母里，2.74 亿来自联营企业房地产处置，主业实际亏损 0.21 亿。</div>',
            unsafe_allow_html=True)
    with b:
        st.markdown(
            '<div class="note"><b>② 杠杆已经不低</b><br>'
            f'资产负债率 <b>{q3["资产负债率%"]:.2f}%</b>，速动比率 {q3["速动比率"]:.2f}；'
            '有息负债由 2025 年末 31.50 亿升至 <b>41.73 亿</b>，'
            '货币资金 21.01 亿，净有息负债约 20.7 亿。</div>',
            unsafe_allow_html=True)
    with cc:
        st.markdown(
            '<div class="note"><b>③ 价格透支了预期</b><br>'
            'DCF 中性情景股权价值 88—215 亿元，当前市值 369.88 亿元；'
            'PB 92% 分位、PS 91% 分位。<b>PE 分位 60% 是假象</b>——'
            '2024 年利润塌陷把 PE 推到千倍，抬高了整个样本的上沿。</div>',
            unsafe_allow_html=True)


# ================================================================== ② 行情与估值
elif nav.startswith("②"):
    st.title("行情与估值")
    span = seg("区间", ["近 1 年", "近 3 年", "近 5 年", "全部"],
               default=2, key="span") or "近 3 年"
    days = {"近 1 年": 365, "近 3 年": 365 * 3, "近 5 年": 365 * 5}.get(span)
    v = val if days is None else val[val["日期"] >= val["日期"].max() - pd.Timedelta(days=days)]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.16,
                        row_heights=[0.6, 0.4])
    fig.add_trace(go.Scatter(x=v["日期"], y=v["收盘"], name="收盘价",
                             line=dict(color=C_MAIN, width=1.6)), 1, 1)
    fig.add_trace(go.Scatter(x=v["日期"], y=v["PE_TTM"], name="PE(TTM)",
                             line=dict(color=C_SUB, width=1.3)), 2, 1)
    for q_, lab in [(0.25, "25%"), (0.5, "50%"), (0.75, "75%")]:
        lvl = v["PE_TTM"].dropna().quantile(q_)
        fig.add_hline(y=lvl, line=dict(color=C_GRAY, width=1, dash="dot"), row=2, col=1)
    style(fig, height=520, legend_top=True).update_layout(
        margin=dict(l=66, r=18, t=34, b=28))   # 双 y 轴（两个子图各一条）叠加时
                                              # automargin 会算偏，左下补足留白
    fig.update_xaxes(tickformat="%Y-%m")
    pe = v["PE_TTM"].dropna()
    if len(pe) > 1:
        fig.update_yaxes(type="log", row=2, col=1, dtick=1, tickformat=".0f",
                         range=[np.log10(max(pe.min() * 0.85, 1)),
                                np.log10(pe.max() * 1.15)])
    chart(fig)
    st.caption("上图为前复权收盘价（元）；下图为 PE(TTM)，纵轴对数坐标，"
               "三条灰色点线依次为该区间 PE 的 25%、50%、75% 分位。")

    left, right = st.columns([1.3, 1], gap="medium")
    with left:
        sec("当前估值的历史分位")
        names = {"PE": "PE (TTM)", "PB": "PB (MRQ)", "PS": "PS (TTM)"}
        fig = go.Figure()
        for k in ["PE", "PB", "PS"]:
            c, p, _ = pct[k]
            col = C_WARN if p > 70 else (C_MAIN if p > 30 else C_ACC)
            fig.add_trace(go.Bar(y=[names[k]], x=[p], orientation="h", width=0.52,
                                 marker_color=col, showlegend=False,
                                 text=[f"{c:.2f} 倍　历史 {p:.0f}% 分位"],
                                 textposition="inside", insidetextanchor="end",
                                 textfont=dict(size=12, color="#ffffff")))
        style(fig, height=230, showlegend=False).update_layout(
            xaxis=dict(range=[0, 100], title="分位（%）"),
            yaxis=dict(autorange="reversed", title="", automargin=True))
        chart(fig)
        st.caption("PB / PS 分位 = 当前值在 2016 年以来全部交易日中的位置；"
                   "PE 分位自 2017 年起（2016 年 TTM 利润不可得）。")
    with right:
        sec("估值指标拆解")
        table(A.t_valuation(d).set_index("指标"), fmt="{:,.2f}", index=True)

    sec("PB—ROE 匹配：估值跑在了盈利前面（纵轴 PB 倍，横轴 ROE %）")
    years = list(range(2017, 2026))
    xs = [ra.loc[y, "ROE%"] for y in years]
    ys = [val[val["日期"].dt.year == y]["PB"].median() for y in years]
    roe_ann = q3["ROE%"] * 4 / 3
    fig = go.Figure()
    # 2017—2025 的 PB 挤在 1.9—2.6，全标年份会糊成一团，只标三个有代表性的年份
    tag = {2017, 2020, 2025}
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers+text", name="年度（ROE, 中位 PB）",
                             text=[str(y) if y in tag else "" for y in years],
                             textposition="top center",
                             line=dict(color="#9e9e9e", width=1),
                             marker=dict(size=9, color=C_MAIN)))
    fig.add_trace(go.Scatter(x=[roe_ann], y=[last["PB"]], mode="markers+text",
                             name="2026Q3（ROE 年化）", text=["2026Q3"],
                             textposition="middle right",
                             marker=dict(size=16, color=C_WARN, symbol="star")))
    fig.add_hline(y=val["PB"].median(), line=dict(color=C_GRAY, dash="dot", width=1),
                  annotation_text=f"历史中位 PB {val['PB'].median():.2f}",
                  annotation_position="bottom right", annotation_font_size=10)
    style(fig, height=380).update_layout(xaxis=dict(title="ROE（%）"))
    chart(fig)
    st.caption(f"2026Q3 为前三季度累计 ROE {q3['ROE%']:.2f}% 按 4/3 简单年化（≈{roe_ann:.1f}%），"
               "仅供同尺度比较；该点显著高于 2017 年以来的 PB—ROE 经验区间。")


# ================================================================== ③ 财务五维
elif nav.startswith("③"):
    st.title("财务五维分析")
    t = A.t_annual(d)
    yrs = [str(c) for c in t.columns]
    # 末点若写全称"2026前三季度"，横轴最后一个标签会被绘图区右边界切掉半截
    yrs[-1] = "2026Q3"

    c = st.columns(4)
    kpi(c[0], "毛利率", f'{q3["毛利率%"]:.2f}%', "2026Q3，十年最高", UP)
    kpi(c[1], "归母净利率", f'{q3["归母净利率%"]:.2f}%', "2026Q3")
    kpi(c[2], "资产负债率", f'{q3["资产负债率%"]:.2f}%', "2026Q3，十年最高", C_WARN)
    kpi(c[3], "净现比", f'{q3["净现比"]:.2f}', "经营现金流 / 归母净利润")

    tabs = st.tabs(["成长性", "盈利能力", "偿债能力", "营运能力", "现金流", "盈利质量", "杜邦分解", "全表"])

    with tabs[0]:
        rev = [ra.loc[y, "营业收入(亿元)"] for y in range(2016, 2026)] + [q3["营业收入(亿元)"]]
        g = [ra.loc[y, "营收增长率%"] for y in range(2016, 2026)] + [q3["营收增长率%"]]
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=yrs, y=rev, name="营业收入（亿元）",
                             marker_color=C_LIGHT, marker_line_color=C_MAIN,
                             marker_line_width=0.8), secondary_y=False)
        fig.add_trace(go.Scatter(x=yrs, y=g, name="同比增速（%）", mode="lines+markers",
                                 line=dict(color=C_SUB, width=2)), secondary_y=True)
        style(fig, height=380)
        fig.update_yaxes(showgrid=False, secondary_y=True)
        # 类别轴默认按宽度抽稀，这里强制每年都标
        fig.update_xaxes(tickmode="array", tickvals=yrs, ticktext=yrs, tickangle=0)
        chart(fig)
        c1, c2 = st.columns(2)
        # 2016 → 2025 是 9 个年度间隔，指数必须是 1/9；写成 0.1（十年）会低估 0.9pct
        cagr10 = (rev[9] / rev[0]) ** (1 / 9) - 1
        metric(c1, "2016—2025 营收 CAGR", f"{cagr10 * 100:.1f}%",
               help="9 个年度间隔的几何平均增速")
        metric(c2, "2026 前三季营收同比", f'{q3["营收增长率%"]:+.1f}%')
        st.caption(f"营收从 2016 年 {rev[0]:.2f} 亿爬到 2025 年 {rev[9]:.2f} 亿，"
                   f"9 年 CAGR 仅 {cagr10 * 100:.1f}%，且 2020、2024 两年为负增长；"
                   "真正的跳变发生在 2026 年前三季度（+49.6%），由光通信 AI 算力订单驱动。")

    with tabs[1]:
        fig = go.Figure()
        for col, name, color in [("毛利率%", "毛利率", C_MAIN), ("归母净利率%", "归母净利率", C_ACC),
                                 ("期间费用率%", "期间费用率", C_SUB)]:
            y = [ra.loc[k, col] for k in range(2016, 2026)] + [q3.get(col, np.nan)]
            fig.add_trace(go.Scatter(x=yrs, y=y, name=name, mode="lines+markers",
                                     line=dict(color=color, width=2)))
        style(fig, height=380)
        chart(fig)
        st.caption("2026 年前三季度毛利率跳升至 28.72%，净利率 13.68%，"
                   "而期间费用率仅 13.32% —— 盈利改善来自毛利端而非费用压缩。")

    with tabs[2]:
        p = d["panel"]
        ann = p[p["报告期"].str.endswith("年报") & (p["报告期"].str[:4].astype(int) >= 2016)]
        int_debt = ((ann["短期借款"].fillna(0) + ann["长期借款"].fillna(0) + ann["应付债券"].fillna(0)) / 1e8)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=ann["报告期"].str[:4], y=ra.loc[2016:2025, "资产负债率%"],
                             name="资产负债率（%）", marker_color=C_LIGHT,
                             marker_line_color=C_MAIN, marker_line_width=0.8), secondary_y=False)
        fig.add_trace(go.Scatter(x=ann["报告期"].str[:4], y=int_debt.values, name="有息负债（亿元）",
                                 mode="lines+markers", line=dict(color=C_WARN, width=2)),
                      secondary_y=True)
        style(fig, height=360)
        fig.update_yaxes(showgrid=False, secondary_y=True, tickformat=".1f")
        chart(fig)
        c1, c2, c3 = st.columns(3)
        # 有息负债不写死：口径 = 短期借款 + 长期借款 + 应付债券，与上图折线同源
        q3d = p[p["报告期"] == "2026三季报"].iloc[0]
        debt_now = round(q3d[["短期借款", "长期借款", "应付债券"]].fillna(0).sum() / 1e8, 2)
        debt_25 = round(float(int_debt.iloc[-1]), 2)
        # 差额按"两个已四舍五入的数相减"，与报告正文的 +10.23 亿元逐字一致
        metric(c1, "流动比率（2026Q3）", f'{q3["流动比率"]:.2f}',
               help="流动资产 / 流动负债")
        metric(c2, "速动比率（2026Q3）", f'{q3["速动比率"]:.2f}',
               help="剔除存货后的短期偿债能力")
        metric(c3, "有息负债（2026Q3）", f"{debt_now:.2f} 亿元",
               f"较 2025 年末 {debt_now - debt_25:+.2f} 亿元",
               delta_color="inverse",
               help="短期借款 + 长期借款 + 应付债券")

    with tabs[3]:
        fig = go.Figure()
        for col, name, color in [("应收账款周转率", "应收账款周转率", C_MAIN),
                                 ("存货周转率", "存货周转率", C_SUB),
                                 ("总资产周转率", "总资产周转率", C_ACC)]:
            y = [ra.loc[k, col] for k in range(2016, 2026)] + [q3.get(col, np.nan)]
            fig.add_trace(go.Scatter(x=yrs, y=y, name=name, mode="lines+markers",
                                     line=dict(color=color, width=2)))
        style(fig, height=380)
        chart(fig)
        st.caption("总资产周转率十年间从 0.69 降至 0.40 附近：收入增长靠加杠杆与加资产推动，"
                   "而非资产效率提升。")

    with tabs[4]:
        fig = go.Figure()
        s = d["single"]
        s_ann = s.groupby("年度")[["经营现金流净额", "投资现金流净额", "筹资现金流净额"]].sum() / 1e8
        s_ann = s_ann.loc[2016:2025]
        for col, name, color in [("经营现金流净额", "经营活动", C_MAIN),
                                 ("投资现金流净额", "投资活动", C_SUB),
                                 ("筹资现金流净额", "筹资活动", C_ACC)]:
            fig.add_trace(go.Bar(x=s_ann.index.astype(str), y=s_ann[col], name=name, marker_color=color))
        style(fig, height=380).update_layout(barmode="group")
        chart(fig)
        c1, c2 = st.columns(2)
        metric(c1, "2026Q3 经营现金流", f'{q3["经营现金流净额(亿元)"]:.2f} 亿元')
        # 说明文字不能塞进 metric 的 delta 参数——Streamlit 会把它当增减量并加箭头、染色
        metric(c2, "2026Q3 净现比", f'{q3["净现比"]:.2f}',
               help="经营现金流净额 / 归母净利润")
        st.caption("净现比 ＜1 说明利润尚未足额转化为现金。上图为年度值；2026Q3 为 1—9 月累计，"
                   "与全年数值不可直接比较。")

    with tabs[5]:
        mp = get_main_profit(d)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=mp["期间"], y=mp["毛利"], name="毛利", marker_color=C_LIGHT))
        fig.add_trace(go.Bar(x=mp["期间"], y=mp["期间费用"], name="期间费用", marker_color=C_SUB))
        fig.add_trace(go.Scatter(x=mp["期间"], y=mp["主业经营利润"], name="主业经营利润",
                                 mode="lines+markers", line=dict(color=C_WARN, width=2.4)))
        fig.add_trace(go.Scatter(x=mp["期间"], y=mp["投资收益"], name="投资收益",
                                 mode="lines+markers", line=dict(color=C_ACC, width=1.6, dash="dot")))
        style(fig, height=400).update_layout(barmode="group")
        chart(fig)
        st.caption("单位：亿元。2026Q3 为前三季度累计（非全年），柱高不可与年度值直接比较。"
                   "2016 年及以前报表未单列研发费用，期间费用只含销售/管理/财务三项，"
                   "故 2016 年主业经营利润偏高，与 2017 年起不可比。")
        st.markdown(
            '<div class="note"><b>为什么要造"主业经营利润"这个指标？</b><br>'
            '2025 年归母 2.34 亿元、扣非占比仍高达 97.10%，看上去盈利质量良好；'
            '但权益法投资收益本身就被计入经常性损益，扣非指标识别不出来。'
            '用"毛利 − 期间费用"穿透后，2025 年主业实际<b>亏损 0.21 亿元</b>，'
            '2.34 亿元净利润几乎全部来自联营企业东昌投资的房地产处置收益（2.74 亿元）。</div>',
            unsafe_allow_html=True)
        table(mp.set_index("期间"), fmt="{:,.2f}", index=True)

    with tabs[6]:
        x = np.arange(len(range(2016, 2026)))
        fig = go.Figure()
        fig.add_trace(go.Bar(x=x - 0.26, y=ra.loc[2016:2025, "归母净利率%"], width=0.26,
                             name="归母净利率（%）", marker_color=C_MAIN))
        fig.add_trace(go.Bar(x=x, y=ra.loc[2016:2025, "总资产周转率"] * 100, width=0.26,
                             name="总资产周转率×100", marker_color=C_SUB))
        fig.add_trace(go.Bar(x=x + 0.26, y=ra.loc[2016:2025, "权益乘数"] * 20, width=0.26,
                             name="权益乘数×20", marker_color=C_ACC))
        fig.add_trace(go.Scatter(x=x, y=ra.loc[2016:2025, "ROE%"], name="ROE（%）",
                                 mode="lines+markers", line=dict(color=C_WARN, width=2.6)))
        style(fig, height=400).update_layout(
            xaxis=dict(tickmode="array", tickvals=list(x), ticktext=[str(y) for y in range(2016, 2026)]))
        chart(fig)
        troe = ra.loc[2016:2025, ["ROE%", "杜邦校验ROE%"]].copy()
        troe["偏差(pct)"] = (troe["杜邦校验ROE%"] - troe["ROE%"]).abs()
        st.caption(f"杜邦恒等式校验：10 个年度最大偏差 {troe['偏差(pct)'].max():.2f} pct"
                   "（权益乘数取期末值、ROE 取平均净资产的固有差异），恒等式成立。")

    with tabs[7]:
        table(t, fmt="{:,.2f}", height=560, index=True)
        st.download_button("下载全表 CSV", t.to_csv(index=True).encode("utf-8-sig"),
                           "永鼎股份_主要财务指标_2016-2026Q3.csv", "text/csv")


# ================================================================== ④ 同业对比
elif nav.startswith("④"):
    st.title("同业对比")
    pr = get_peer_return(d)
    st.caption(f"区间：{pr.attrs['start']} 至 {val['日期'].max():%Y-%m-%d}（前复权收盘价，首日归一）")

    left, right = st.columns([1.05, 1], gap="medium")
    with left:
        sec(f"区间累计涨幅（{pr.attrs['start']} 起）")
        # 中际旭创 +8755%（2017 年重大资产重组并表）会把其余 6 家压成一条线，
        # 故截断其条长并标 "→ 实际值"，既不误导又能看清其余各家的差异。
        CAP = 1000.0
        vals = pr["区间涨幅%"].tolist()
        xs = [min(v, CAP) for v in vals]
        labels = [f"{v:+.0f}%" if v <= CAP else f"→ {v:+.0f}%" for v in vals]
        colors = [C_WARN if n == "永鼎股份" else C_MAIN for n in pr["名称"]]
        fig = go.Figure(go.Bar(x=xs, y=pr["名称"], orientation="h",
                               marker_color=colors, text=labels,
                               textposition="outside", cliponaxis=False))
        lo_ = min(0.0, min(vals))
        style(fig, height=340, showlegend=False).update_layout(
            xaxis=dict(title="累计涨幅（%）（中际旭创已截断）",
                       range=[lo_ - 8 if lo_ < 0 else 0, CAP * 1.16]),
            yaxis=dict(autorange="reversed"))
        chart(fig)
    with right:
        sec("2025 年报关键指标")
        tp = A.t_peer(d)
        tp = tp[tp["报告期"] == "2025年报"][["名称", "营业收入(亿元)", "毛利率%",
                                             "加权ROE%", "资产负债率%"]]
        # 同业接口（东方财富 PEERS）只返回 6 家、不含 600105，按同口径补入本公司
        tp = pd.concat([tp, pd.DataFrame([{
            "名称": "永鼎股份",
            "营业收入(亿元)": ra.loc[2025, "营业收入(亿元)"],
            "毛利率%": ra.loc[2025, "毛利率%"],
            "加权ROE%": ra.loc[2025, "ROE%"],
            "资产负债率%": ra.loc[2025, "资产负债率%"],
        }])], ignore_index=True)
        table(tp.set_index("名称"), fmt="{:,.2f}", index=True)
        st.caption("净利率、EPS、BPS 见报告表 5-3；永鼎数据按同口径补入（接口不含 600105），"
                   "其 ROE 取 ratios_annual 加权口径。")

    sec("财务特征雷达（2025 年报，各轴统一百分制）")
    picks = ["永鼎股份", "长飞光纤", "亨通光电", "中天科技", "烽火通信"]
    pi = A._peer_plus_yd(d)
    p25 = pi[(pi["REPORT_DATE_NAME"] == "2025年报") & (pi["名称"].isin(picks))].dropna(subset=["ROEJQ"])
    axes = ["毛利率(%)", "净利率(%)", "加权ROE(%)", "偿债安全度(100-资产负债率)", "总资产周转(次×100)"]
    fig = go.Figure()
    palette = [C_WARN, C_MAIN, C_SUB, C_ACC, C_GRAY]
    for i, (_, r) in enumerate(p25.iterrows()):
        vals = [r["XSMLL"], r["XSJLL"], r["ROEJQ"], 100 - r["ZCFZL"], min(r["TOAZZL"] * 100, 100)]
        own = r["名称"] == "永鼎股份"
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=axes + [axes[0]],
            name=r["名称"], fill="toself" if own else None,
            fillcolor="rgba(192,0,0,.12)" if own else None,
            line=dict(color=palette[i % 5], width=3 if own else 1.4)))
    style(fig, height=460).update_layout(
        polar=dict(radialaxis=dict(range=[0, 100], showticklabels=False,
                                   showline=False, gridcolor="#e4e9f0"),
                   angularaxis=dict(gridcolor="#e4e9f0", tickfont=dict(size=11))),
        margin=dict(l=58, r=58, t=34, b=34))
    chart(fig)
    st.caption("各轴统一为 0—100 分制（刻度已隐去，只比较形状）。"
               "为免极值压扁坐标，雷达图仅取 5 家（不含中际旭创 43.84% 的 ROE 与通鼎互联）；"
               "中际旭创见上表。同业接口不含 600105，永鼎数据按同口径补入。")


# ================================================================== ⑤ 宏观与行业
elif nav.startswith("⑤"):
    st.title("宏观与行业")
    m = A.t_macro_annual(d)

    c = st.columns(4)
    kpi(c[0], "2025 GDP 增速", f'{m.loc[2025, "GDP增速%"]:.1f}%', "实际增速")
    kpi(c[1], "2025 CPI 同比", f'{m.loc[2025, "CPI同比%"]:.1f}%', "低位徘徊")
    kpi(c[2], "2025 PPI 同比", f'{m.loc[2025, "PPI同比%"]:.1f}%', "连续为负，压制中游毛利", C_WARN)
    kpi(c[3], "2025 制造业 PMI", f'{m.loc[2025, "制造业PMI均值"]:.1f}', "荣枯线附近")

    left, right = st.columns([1.25, 1], gap="medium")
    with left:
        sec("增长与价格：GDP、CPI、PPI")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=m.index.astype(str), y=m["GDP增速%"], name="GDP 实际增速",
                             marker_color=C_MAIN, width=0.34))
        fig.add_trace(go.Bar(x=m.index.astype(str), y=m["PPI同比%"], name="PPI 同比",
                             marker_color=C_SUB, width=0.34))
        fig.add_trace(go.Scatter(x=m.index.astype(str), y=m["CPI同比%"], name="CPI 同比",
                                 mode="lines+markers", line=dict(color=C_ACC, width=2)))
        fig.add_hline(y=0, line=dict(color="#333", width=0.9))
        style(fig, height=340).update_layout(barmode="group")
        chart(fig)
    with right:
        sec("货币与景气：M2 与 PMI")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=m.index.astype(str), y=m["M2同比%"], name="M2 同比",
                                 mode="lines+markers", line=dict(color=C_MAIN, width=2.2)),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=m.index.astype(str), y=m["制造业PMI均值"], name="制造业 PMI",
                                 mode="lines+markers", line=dict(color=C_SUB, width=2)),
                      secondary_y=True)
        fig.add_hline(y=50, line=dict(color=C_GRAY, dash="dot", width=1), secondary_y=True)
        style(fig, height=340)
        fig.update_yaxes(showgrid=False, secondary_y=True, tickformat=".1f")
        chart(fig)

    sec("宏观年度指标")
    mm = m.reset_index()
    mm.columns = ["年度"] + list(mm.columns[1:])   # 原索引名为"年"，单独成列才不会挤成一行
    mm["年度"] = mm["年度"].astype(str)            # 否则会被当成数值格式化成 "2,016.00"
    table(mm, fmt="{:,.2f}", index=False)

    sec("分板块收入结构（半年报口径）")
    seg = A.t_segment_h1(d)
    seg = seg.loc[[i for i in seg.index if i >= "2021H1"]]
    fig = go.Figure()
    for col in seg.columns:
        fig.add_trace(go.Bar(x=seg.index, y=seg[col], name=col))
    style(fig, height=360).update_layout(barmode="stack")
    chart(fig)
    st.caption("2026H1：光通信 12.35 亿元（占 58.52% 毛利）、汽车线束 8.77 亿元、"
               "电力工程 6.56 亿元、超导及铜导体 4.84 亿元。")


# ================================================================== ⑥ 估值模型
elif nav.startswith("⑥"):
    st.title("估值模型：两阶段 DCF")
    st.caption("基期自由现金流取 2026 年（约 6.0 亿元）；2027—2030 年按给定增速增长，2031 年起永续；"
               "企业价值 − 净有息负债 = 股权价值。")

    c1, c2, c3, c4 = st.columns(4)
    fcf0 = c1.number_input("基期自由现金流（亿元）", 1.0, 30.0, 6.0, 0.5,
                           help="2026 年经营性自由现金流估计")
    # 滑块值直接用百分数再换算成小数：若传 0.10 又写 format="%.1f%%"，
    # Streamlit 会把 0.10 原样套进格式串，显示成 "0.1%" 而不是 "10.0%"。
    wacc_pct = c2.slider("WACC（%）", 6.0, 16.0, 10.0, 0.5, format="%.1f%%")
    g_pct = c3.slider("永续增长率 g（%）", 0.0, 5.0, 2.5, 0.25, format="%.2f%%")
    netdebt = c4.number_input("净有息负债（亿元）", 0.0, 100.0, 20.7, 0.5,
                              help="有息负债 41.73 − 货币资金 21.01")
    wacc, g = wacc_pct / 100, g_pct / 100
    st.caption("默认参数即报告正文所用的那一组：基期自由现金流 6.0 亿元、WACC 10%、"
               "永续增长 2.5%、2027—2030 年增速 30%/18%/10%/6%（对应图 6-4 的中间一列）。")

    growth = []
    cc = st.columns(4)
    for i in range(4):
        growth.append(cc[i].slider(f"{2027 + i} 年增速（%）", -30, 100,
                                   [30, 18, 10, 6][i], 1, format="%d%%") / 100)

    def dcf_ev(f0, gs, w, gg):
        pv, f = 0.0, f0
        for t, gr in enumerate(gs, 1):
            f *= 1 + gr
            pv += f / (1 + w) ** t
        tv = f * (1 + gg) / (w - gg)
        return pv + tv / (1 + w) ** len(gs)

    shares = last["股本"] / 1e8
    ev = dcf_ev(fcf0, growth, wacc, g)
    eq = ev - netdebt
    ps = eq / shares
    gap = ps / snap_px - 1

    c = st.columns(4)
    kpi(c[0], "企业价值 EV", f"{ev:.0f} 亿元", "未来现金流折现 + 永续价值")
    kpi(c[1], "股权价值", f"{eq:.0f} 亿元", f"减净有息负债 {netdebt:.1f} 亿元")
    kpi(c[2], "每股价值", f"{ps:.2f} 元", f"总股本 {shares:.2f} 亿股")
    kpi(c[3], "相对现价", f"{gap:+.0%}", f"现价 {snap_px:.2f} 元",
        UP if gap > 0 else DOWN)

    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        sec("敏感性：WACC × 永续增长率（企业价值，亿元）")
        ws = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]
        gs = [g - 0.01, g - 0.005, g, g + 0.005, g + 0.01]
        z = [[dcf_ev(fcf0, growth, w, gg) for gg in gs] for w in ws]
        txt = [[f"{v:.0f}" for v in row] for row in z]
        fig = go.Figure(go.Heatmap(z=z, x=[f"{v * 100:.2f}%" for v in gs],
                                   y=[f"{v * 100:.1f}%" for v in ws],
                                   # 用单色 Blues 而非 RdYlGn：在 A 股语境里"红涨绿跌"，
                                   # 红绿渐变会把"企业价值高"读成"跌"，改用深浅表达高低。
                                   colorscale="Blues", text=txt, texttemplate="%{text}",
                                   textfont=dict(size=13), colorbar=dict(title="亿元")))
        style(fig, height=340, showlegend=False).update_layout(
            xaxis=dict(title="永续增长率 g"))
        chart(fig)
    with right:
        sec("反解：多高的增速才能撑起当前市值？")
        target_eq = last["总市值(亿元)"]
        lo, hi = -0.5, 2.0
        for _ in range(120):
            mid = (lo + hi) / 2
            if dcf_ev(fcf0, [mid] * 4, wacc, g) - netdebt < target_eq:
                lo = mid
            else:
                hi = mid
        cagr = (lo + hi) / 2
        kpi(st.container(), "隐含四年复合增速",
            f"{cagr:.1%}", f"当前市值 {target_eq:.0f} 亿元 / WACC {wacc:.1%}")
        st.markdown(
            f'<div class="note" style="margin-top:12px">在 WACC {wacc * 100:.1f}%、永续增长 '
            f'{g * 100:.2f}% 的假设下，要让 DCF 股权价值等于当前 {target_eq:.0f} 亿元市值，'
            f'2027—2030 年自由现金流需连续四年复合增长 <b>{cagr:.1%}</b>。'
            '这是判断"贵不贵"最直接的尺子。</div>', unsafe_allow_html=True)

        sec("参考情景")
        rows = []
        for name, gs_, w_, gg_ in [("中性", [0.30, 0.18, 0.10, 0.06], 0.10, 0.025),
                                   ("乐观", [0.50, 0.35, 0.20, 0.10], 0.10, 0.025),
                                   ("悲观", [0.10, 0.05, 0.03, 0.02], 0.11, 0.020)]:
            ev_ = dcf_ev(6.0, gs_, w_, gg_)
            rows.append({"情景": name, "增速路径": "/".join(f"{x:.0%}" for x in gs_),
                         "WACC": f"{w_:.0%}", "EV(亿元)": ev_,
                         "股权(亿元)": ev_ - 20.7, "每股(元)": (ev_ - 20.7) / shares})
        table(pd.DataFrame(rows).set_index("情景"), fmt="{:,.1f}", index=True)
        st.caption("三套情景均以基期自由现金流 6.0 亿元、净有息负债 20.7 亿元为共同假设。")

    st.markdown(
        '<div class="note" style="margin-top:8px"><b>模型局限（写进报告的那三条）</b><br>'
        '① 估值结论高度依赖"光通信高毛利能否持续"，而该判断缺乏 2027 年订单数据支持；'
        '② 基期自由现金流取自 2026 年，若 2027 年资本开支大幅上升，自由现金流将被显著高估；'
        '③ 永续增长率与 WACC 的微小变动即造成 30% 以上的价值摆动，故本节只给区间、不给目标价。</div>',
        unsafe_allow_html=True)


# ================================================================== ⑦ 图表墙
elif nav.startswith("⑦"):
    st.title("图表墙")
    st.caption("报告中的 21 张成图（300 dpi）。点击图片可放大查看。")
    tabs = st.tabs([t for t, _ in FIGS])
    for tab, (_, items) in zip(tabs, FIGS):
        with tab:
            cols = st.columns(2, gap="medium")
            for i, (fn, cap) in enumerate(items):
                p = BASE / "figures" / fn
                with cols[i % 2]:
                    if p.exists():
                        show_image(str(p), caption=cap)
                    else:
                        st.warning(f"缺少图片：{fn}")


# ================================================================== ⑧ 数据与说明
else:
    st.title("数据与说明")

    st.markdown(
        '<div class="note"><b>分析对象</b>　江苏永鼎股份有限公司（600105.SH）<br>'
        '<b>数据区间</b>　财务数据 2015—2025 年报 + 2026 年第三季度报告；'
        '行情数据 2016-01-04 — 2026-10-27<br>'
        '<b>抓取时间</b>　2026-10-27 23:21—23:24（本地一次性抓取，见 data/raw/_fetch_log.csv，49 条记录 48 成功）<br>'
        '<b>处理原则</b>　原始数据保持接口原样，全部派生逻辑写在 scripts/02_process.py，可一键复现</div>',
        unsafe_allow_html=True)

    st.write("")
    sec("数据源（14 类接口，下表按用途归并为 9 组）")
    src = pd.DataFrame([
        ["日 K 线（前复权 / 不复权）", "腾讯财经", "web.ifzq.gtimg.cn（fqkline/get、kline/kline）", "2 615 × 2"],
        ["实时快照", "腾讯财经", "qt.gtimg.cn", "1"],
        ["资产负债表 / 利润表 / 现金流量表", "东方财富 F10", "datacenter.eastmoney.com", "44 期 × 3"],
        ["核心财务指标", "东方财富 F10", "RPT_F10_FINANCE_MAINFINADATA", "112 期"],
        ["主营构成（分产品 / 分地区）", "东方财富 F10", "RPT_F10_FN_MAINOP", "510 条（58 期）"],
        ["同业 6 家日线 + 核心指标", "腾讯财经 / 东方财富", "代码 601869 / 600487 / 600522 / 600498 / 300308 / 002491", "14 820 / 477"],
        ["宏观 8 项序列 + LPR", "东方财富数据中心 / 中国货币网", "RPT_ECONOMY_*；LprHis", "1 076 / 12"],
        ["定期报告 PDF", "巨潮资讯网", "cninfo.com.cn（searchkey=年度报告）", "13 份"],
        ["指数日线", "腾讯财经", "sh000001 / sh000300 / sz399006", "2 625 × 3"],
    ], columns=["数据项", "来源", "接口", "记录数"])
    # 落到 "content"：接口名一长就会折行，固定像素高度会把最后一行"定期报告 PDF"切掉
    table(src.set_index("数据项"), fmt="{}", index=True, height="content")

    sec("三项关键口径（也是最容易出错的地方）")
    a, b, c = st.columns(3, gap="medium")
    with a:
        st.markdown('<div class="note"><b>累计值拆单季</b><br>一季报 = 累计本身；中报 = 中报 − 一季报；'
                    '三季报 = 三季报 − 中报；年报 = 年报 − 三季报。报告期识别必须用 '
                    '<code>endswith</code>，<b>不能用</b> <code>str[-3:]</code>——'
                    '"一季报"是 4 个字符，截末 3 位会得到"季报"而匹配失败。</div>',
                    unsafe_allow_html=True)
    with b:
        st.markdown('<div class="note"><b>TTM 与防前视偏差</b><br>TTM = 最近 4 个单季之和；'
                    '关键是只在<b>实际公告日</b>之后才允许使用，'
                    '用 <code>merge_asof(direction="backward")</code> 以公告日为阶梯键填充。'
                    '若按报告期末硬对齐，2026 年 8—10 月的 PE 会提前用到 10 月底才披露的三季报。</div>',
                    unsafe_allow_html=True)
    with c:
        st.markdown('<div class="note"><b>盈利质量穿透</b><br>权益法投资收益计入经常性损益，'
                    '"扣非占比"识别不出（2025 年仍达 97.10%）。'
                    '故改用"毛利 − 期间费用 = 主业经营利润"，2025 年为 <b>−0.21 亿元</b>，'
                    '这才是判断盈利质量的正确切口。</div>', unsafe_allow_html=True)

    sec("校验记录")
    chk = pd.DataFrame([
        ["2025 年营业收入", "52.87 亿元", "2025 年报 52.87 亿元", "一致"],
        ["2025 年归母净利润", "2.34 亿元", "2025 年报 2.34 亿元", "一致"],
        ["2026 前三季营收 / 扣非", "54.30 / 7.40 亿元", "2026 三季报", "一致"],
        ["当前 PE(TTM)", "57.13 倍", "腾讯快照 57.13 倍", "一致"],
        ["当前 PB", "9.55 倍", "腾讯快照 9.67 倍", "差 1.3%（净资产口径差一期）"],
        ["单季营收加总", "各年 4 季合计", "年报营业收入", "误差 < 0.01 亿元"],
        ["杜邦恒等式", "净利率×周转×权益乘数", "直接计算 ROE", "10 年均通过（<2pct）"],
    ], columns=["校验项", "本表值", "外部对照", "结论"])
    table(chk.set_index("校验项"), fmt="{}", index=True, height=280)

    sec("已知局限")
    st.markdown(
        "1. **2026 年只有三季报**：周转率类指标未年化，与年度口径不完全可比；ROE 年化仅为同尺度比较。\n"
        "2. **2016 年及以前未单列研发费用**：期间费用率自 2017 年起才有值，2015—2016 年为“—”，"
        "不是漏算，而是口径不可比。\n"
        "3. **同业对比用 2025 年报**：东方财富同业接口最新只到 2026 中报，且不含 600105，"
        "永鼎数据由作者按同口径补入。\n"
        "4. **中际旭创 2017 年增速 1690%** 系重大资产重组并表，非内生增长，图中已截断处理。\n"
        "5. **LPR 仅有近一年明细**：中国货币网历史接口限制，利率环境改用 1 年期 LPR 现值 + 存款准备金率序列描述。\n"
        "6. **行情源更换**：东方财富 push2his 在本机网络被拒，行情改用腾讯财经，已与快照、F10 交叉验证。")

    st.write("")
    sec("下载")
    c1, c2, c3 = st.columns(3)
    docx = next(BASE.glob("12607320270457_*.docx"), None)
    pdf = next(BASE.glob("12607320270457_*.pdf"), None)
    if docx:
        dl_button(c1, "投资分析报告（Word）", docx.read_bytes(), docx.name,
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if pdf:
        dl_button(c2, "投资分析报告（PDF）", pdf.read_bytes(), pdf.name,
                  "application/pdf")
    nbp = BASE / "永鼎股份投资分析.ipynb"
    if nbp.exists():
        dl_button(c3, "分析 Notebook", nbp.read_bytes(), nbp.name,
                  "application/x-ipynb+json")

    st.caption("本看板为《证券投资学》课程作业，所有结论仅供教学讨论，不构成任何投资建议。")
