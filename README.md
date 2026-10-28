# 永鼎股份（600105.SH）投资价值分析

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.66-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Data](https://img.shields.io/badge/data-2016--2026-blue)
![Report](https://img.shields.io/badge/report-34p%20%2F%2021fig-orange)

《证券投资学》课程实践课 · 个股投资分析报告。
以**江苏永鼎股份有限公司（600105.SH）**为对象，从宏观、行业、公司财务、估值四条线展开，
最终给出**"谨慎看待 · Hold"**的评级结论——**好公司、贵价格**。

> 面向课程提交的清单与排版规范见 [`交付说明.md`](交付说明.md)；
> 本文面向仓库读者，说明**数据怎么来的、结论怎么算的、如何一键复现**。

---

## 一、结论速览

| 维度 | 数值 | 说明 |
|---|---|---|
| 现价 / 总市值 | **25.30 元** / **369.88 亿元** | 2026-10-27 收盘，股本 14.62 亿股 |
| PE(TTM) / PB / PS | **57.13** / **9.55** / **5.22** | 历史分位 **60.2% / 92.3% / 91.1%** |
| 2026 前三季营收 | **54.30 亿元（+49.6%）** | AI 算力驱动光通信订单，十年最强的一次增长 |
| 2026 前三季归母 | **7.43 亿元（+125.8%）** | 扣非 7.40 亿元，占归母 **99.66%** |
| DCF 中性每股价值 | **7.5 元** | 三情景 11.6 / 7.5 / 3.8 元，**均低于现价** |
| 评级 | **谨慎看待 · Hold** | 基本面改善是真的，价格已提前兑现 |

**一句话**：2026 年是永鼎第一次"业绩兑现成长"的年份（主业由亏转正、扣非占比 99.66%），
但当前价格已隐含 2027—2030 年自由现金流连续四年复合增长 **55.7%** 的假设——
赔率不足，故不给予买入评级。

---

## 二、三种打开方式

| 想做什么 | 怎么做 |
|---|---|
| **只看结论** | 双击打开 [`index.html`](index.html)（零依赖，离线可用）。含价格 vs 内在价值对照条、8 张 KPI 卡、21 图图表墙、深浅色主题、图片灯箱 |
| **交互探索** | `pip install -r requirements.txt && streamlit run streamlit_app.py` → 8 页看板，DCF 滑块可实时联动 |
| **看正式报告** | 打开根目录 `12607320270457_滕宇豪_..._投资分析报告.pdf`（34 页 / 17,049 字 / 21 图 / 12 表），Word 版同名 `.docx` 可编辑 |

---

## 三、目录结构

```
600105.SH_Investment_Analysis/
├── index.html                    项目门户首页（973 行，零外部依赖，浏览器直接打开）
├── streamlit_app.py              交互看板（8 页，口径与报告同源）
├── 永鼎股份投资分析.ipynb         分析 Notebook（8 章 / 51 单元格 / 0 报错 / 21 图内嵌）
├── requirements.txt              Python 3.12 依赖（锁 numpy 1.26.4 / pyarrow 17.0.0）
├── 交付说明.md                    课程交付清单、排版规范、署名信息
├── README.md                     本文件
├── LICENSE                       MIT
│
├── 12607320270457_滕宇豪_25级大数据与财务管理03班_江苏永鼎股份（600105.SH）投资分析报告.docx / .pdf
├── 经济与管理学院实践课报告-《证券投资学》.docx    学院模板（排版参照，原始文件）
│
├── scripts/                      27 个脚本，覆盖抓取 → 加工 → 出图 → 排版全链路
│   ├── 00_probe_*.py             接口探测（连通性 / 字段 / 复权路径，保留排查记录）
│   ├── 01_fetch_all.py           主抓取；01b / 01c / 01d 为三次补抓
│   ├── 02_process.py             生成 processed/ 下 7 张分析表（02a/02b/02c 为核对脚本）
│   ├── 03_extract_pdf.py         年报 PDF → 文本；04_grep_pdf.py 原文检索
│   ├── 05_make_notebook.py       生成 Notebook；05b_run_notebook.py 执行并内嵌输出
│   ├── 06_build_report.py        Word 报告排版引擎
│   ├── analysis_lib.py           **口径中枢**：指标计算 + 21 张图（报告与看板共用）
│   └── report_content.py         报告正文（章节 / 图题 / 表题）
│
├── data/
│   ├── raw/                      原始抓取：_fetch_log.csv、_json/、financials/、
│   │                             indicators/、macro/、market/、peers/、reports/
│   ├── processed/                7 张分析用表（panel / quarterly_single / ratios_annual /
│   │                             ratios_2026Q3 / segment_income / segment_region / valuation_daily）
│   └── README.md                 数据底稿说明：14 类接口、派生表口径、9 项校验、6 项局限
│
└── figures/                      21 张 300dpi 图（带图内标题，网页/Notebook 用）
    └── report/                   同源 21 张"裸图"（去图内标题，供 Word 用，避免与图题重复）
```

---

## 四、数据管线

```
14 类公开接口  ──01─┐
（腾讯财经行情 / 东方财富 F10 与数据中心 / 巨潮资讯 / 中国货币网）
                    ├─→ data/raw ──02─→ data/processed（7 张表）
  13 份年报 PDF ──03─┘                        │
                                              ├─→ analysis_lib.py ─→ figures/（21 图）
                                              ├─→ 永鼎股份投资分析.ipynb（8 章 51 单元格）
                                              ├─→ report_content.py ─→ Word/PDF 报告
                                              └─→ streamlit_app.py ─→ 交互看板（8 页）
```

**报告、Notebook、看板、首页共用 `scripts/analysis_lib.py` 的同一套口径**，不存在"网页一个数、报告一个数"。
数据区间：财务 **2015—2025 年报 + 2026 三季报**，行情 **2016-01-04 — 2026-10-27**（前复权）。
接口清单、记录数与抓取要点见 [`data/README.md`](data/README.md)。

---

## 五、完整复现

```bash
# 1) 安装依赖（Python 3.12）
pip install -r requirements.txt

# 2) 抓取 → 加工 → 年报抽取
python scripts/01_fetch_all.py      # 主抓取（约 3 分钟）
python scripts/01b_fix.py           # 补抓不复权日线与年报
python scripts/01c_fix2.py          # 补抓 2014—2020 年报
python scripts/01d_index.py         # 补抓三大指数日线
python scripts/02_process.py        # 生成 processed/ 下 7 张表
python scripts/03_extract_pdf.py    # 年报 PDF → 文本

# 3) 出图：带标题版（网页用）与裸图版（Word 用）
python scripts/analysis_lib.py
set FIG_DIR=figures\report && set FIG_BARE=1 && python scripts/analysis_lib.py   # Windows
# FIG_DIR=figures/report FIG_BARE=1 python scripts/analysis_lib.py               # Linux / macOS

# 4) Notebook 与报告
python scripts/05_make_notebook.py && python scripts/05b_run_notebook.py
python scripts/report_content.py    # 生成 Word；PDF 用 Word 另存为或 COM 导出

# 5) 启动看板
streamlit run streamlit_app.py
```

> ⚠️ **版本锁定**：`numpy==1.26.4`、`pyarrow==17.0.0` 不可升级。
> pyarrow ≥20 按 NumPy 2.x ABI 编译，会抛 `ImportError: pyarrow requires NumPy 2.0 or newer`；
> numpy 升 2.x 则 matplotlib 3.9.3 配套失效。

---

## 六、核心结论

1. **成长性**：2016 年营收 25.79 亿 → 2025 年 52.87 亿，9 年 CAGR **8.3%**，2020、2024 两年负增长——
   长期是一条低增速制造业曲线；真正的跳变发生在 **2026 年前三季度（+49.6%）**。
2. **盈利质量**：2025 年归母 2.34 亿中含东昌投资权益法收益 **2.74 亿**（房地产处置），
   按"毛利 − 期间费用"口径的**主业经营利润为 −0.21 亿**（亏损）；
   2026Q3 扣非占比 **99.66%**、投资收益仅 0.12 亿，是十年来第一次由主业真实驱动。
3. **同业位置**：区间涨幅 中际旭创 +8755%、长飞 +719%、亨通 +420%、中天 +274%、**永鼎 +241%**、
   烽火 +12%、通鼎 −14.8%——永鼎在光通信板块中处中游，并非最热标的。
4. **估值**：PE 分位在本案例会失效（2024 年利润塌陷把 PE 推到千倍、拉高样本上沿，
   剔除净利 <1 亿元年份后分位由 60.2% 升至 67.0%），**结论应以 PB(92.3%) / PS(91.1%) 分位为主**；
   两阶段 DCF（WACC 10%、g 2.5%、净有息负债 20.7 亿）三情景每股价值 11.6 / 7.5 / 3.8 元，均低于现价。

---

## 七、关键口径（四处容易算错的地方）

| 口径 | 正确做法 |
|---|---|
| 营收 CAGR | 2016→2025 共 **9 个间隔**，用 `(52.87/25.79)^(1/9)−1 = 8.3%`；按十年根 (1/10) 会低估为 7.4% |
| 主业经营利润 | **毛利 − 期间费用**（含研发）。2016 年及以前年报未单列研发费用，故该口径自 2017 年起可比 |
| 2026Q3 | 为**前三季度累计**值，非全年，柱高不可与年度值直接比较；增长率类指标仍为同比口径 |
| 估值防前视偏差 | TTM 值只在实际**公告日之后**才允许用于估值（`merge_asof` 按公告日阶梯填充），否则 2026 年 8—10 月的 PE 会提前用到 10 月底才披露的三季报 |

完整口径与 9 项校验记录见 [`data/README.md`](data/README.md) 第三节、第四节。

---

## 八、已知局限

1. 东方财富 `push2his` / `push2` 行情域名在本机网络下连接被拒，行情统一改用腾讯财经，
   估值结论已与腾讯实时快照、东方财富 F10 交叉验证。
2. 东方财富同业接口返回 6 家可比公司、**不含 600105**，已在 `_peer_plus_yd()` 中按同一口径补入本公司行。
3. 中际旭创 2017 年营收增速 1690% 系重大资产重组并表，非内生增长，图中已截断并注明。
4. LPR 仅有近一年明细（中国货币网限制），利率环境改用 1 年期 LPR 现值 + 存款准备金率序列描述。
5. 2016 年及以前未单列研发费用，期间费用率自 2017 年起才有值——不是漏算，而是口径不可比。
6. DCF 对基期自由现金流与永续增长率高度敏感，请以"三情景 + WACC×g 热力图"的区间视角使用，而非单一数值。

---

## 九、环境

| 项 | 版本 |
|---|---|
| Python | 3.12 |
| 核心依赖 | pandas 2.2.2 · numpy 1.26.4 · matplotlib 3.9.3 |
| 报告链 | python-docx 1.2.0 · PyMuPDF 1.28.2 · nbformat 5.11.1 · nbclient 0.11.0 |
| 看板 | streamlit 1.66.1 · plotly 7.1.0 · pyarrow 17.0.0 |
| 操作系统 | Windows 11（脚本路径处理已兼顾 POSIX） |

---

## 十、署名

**滕宇豪** · 学号 12607320270457 · 25 级大数据与财务管理 03 班
指导老师：**李淑会** · 2026 年 11 月

---

## 免责声明

本项目为**课程学习用途**，所有结论基于公开数据与作者自行测算，
**不构成任何投资建议**。数据来源：腾讯财经（行情）、东方财富 F10 与数据中心（财务 / 宏观 / 同业）、
巨潮资讯网（定期报告）、中国货币网（LPR）。测算口径已在第七节与 `data/README.md` 中完整披露。

## License

[MIT](LICENSE) © 2026 滕宇豪
