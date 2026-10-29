# IntermarketAnalysis

使用 [Scrapling](https://github.com/D4Vinci/Scrapling) 增量抓取跨市场指标，写入本地 SQLite，并通过内置看板按日期区间对比折线图。

<p align="center">
  <a href="https://github.com/Torres999/IntermarketAnalysis">
    <img src="docs/images/dashboard.png" alt="A 股跨市场看板：双图对比、快捷预设与归一化折线" width="920" />
  </a>
</p>
<p align="center"><sub>上下两块面板默认同屏对比；快捷预设会同步指标，也可分别多选做差异分析。</sub></p>

<p align="center">
  <strong>一键使用</strong>：双击 <code>start.bat</code>（或 <code>.\start.ps1</code>）自动更新数据并打开
  <a href="http://127.0.0.1:8765/">http://127.0.0.1:8765/</a>
</p>

## 为何选择 Scrapling 而不是 Crawl4AI

| 维度 | Scrapling | Crawl4AI |
| --- | --- | --- |
| 目标场景 | 结构化抓取、XPath/CSS、并发 Spider、反爬浏览器 | 页面转 Markdown/JSON，服务 LLM/RAG |
| 金融时间序列 | `record_requests` 捕获 XHR/API，适合 TradingView / Investing | 需从 Markdown 再解析，稳定性较差 |
| 反爬 | `StealthyFetcher` / Cloudflare 绕过 | 有 Playwright，但更偏内容抽取 |
| 依赖体积 | 以 curl_cffi + Patchright 为主 | 浏览器栈 + 可选 LLM 相关能力 |

本项目需要**稳定数值序列 + 增量更新 + 本地 SQLite**，Scrapling 更贴合；Crawl4AI 更适合“整页给大模型读”。

Scrapling 源码已 vendored 在 `vendor/scrapling/`，通过 `requirements.txt` 以 editable 方式安装。

## 数据源

| 类别 | series_id | 说明 |
| --- | --- | --- |
| 债券 | `cn10y` / `cn10y_yield` | 10Y 国债价格 / 收益率（分析摘要以 yield 为主；图表四腿预设用价格） |
| 汇率 | `rmb_cfets` / `rmb_bis` / `rmb_sdr` | 中国货币网人民币汇率指数 |
| 现货指数 | `sse_composite`, `sse50`, `csi300`, … | 东方财富日 K（替代 Investing sbcharts 误曲线） |
| 股指期货 | `future_ih` / `future_if` / `future_ic` / `future_im` | 新浪主连 IH0/IF0/IC0/IM0，约 5 年日 K |
| 大宗 | `comm_au`, `comm_cu`, `comm_sc`, `comm_rb`, `nh_commodity` | 新浪主连 + 本地等权综合指数 |

选型与稳定性说明见 [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)。

图表页需点击底部 **「5 年」** 后再从网络接口解析（见 `intermarket_analysis/scrapers/`）。

## 环境要求

- Python 3.10+
- 除 Python 与 Scrapling（含 Patchright 浏览器）外，无 FastAPI/Django 等额外框架依赖
- 图表使用 vendored 的 Chart.js（`web/static/chart.umd.min.js`）

## 安装

```powershell
cd G:\youtube\IntermarketAnalysis
.\setup.ps1
```

> Scrapling 使用 **Patchright**。`setup.ps1` 会把浏览器下载到项目内 `.browsers/`。  
> 若 `patchright install chromium` 因网络超时失败，可改用本机已安装的 Chrome：
>
> ```powershell
> $env:INTERMARKET_REAL_CHROME = "1"
> python main.py scrape
> ```

## 使用

**推荐：只打开网页**

```powershell
.\start.ps1
# 或双击 start.bat
```

首次若 Investing 序列为空，会自动触发一次图表全量回填（较慢）。也可手动：

```powershell
python main.py start --full-backfill
```

高级命令：

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "G:\youtube\IntermarketAnalysis\.browsers"

# 增量抓取（首次约 5 年，之后从上次最后日期向前重叠 7 天）
python main.py scrape

# 清空并重抓所有图表类序列（指数、期货、国债 yield 等）
python main.py backfill-charts

# A 股多资产分析摘要（股债汇 + 宽基 SMT + 期现价差）
python main.py analyze

# 启动本地看板
python main.py serve

# 抓取并启动看板（同 start）
python main.py run
```

浏览器打开：<http://127.0.0.1:8765/>

数据文件：`data/market.db`（SQLite，首次抓取后生成，未纳入 Git）

## 增量逻辑

- 每个序列在 `crawl_state` 表记录 `last_obs_date`
- 下次运行从 `last_obs_date - 7 天` 起到今天重新抓取并 upsert，避免漏数据
- 首次无历史时默认回溯 5 年

## 目录结构

```
docs/images/          # README 看板截图
vendor/scrapling/     # Scrapling 源码（editable install）
intermarket_analysis/ # 存储、抓取、分析、HTTP API
web/                  # 静态页面与 Chart.js
data/market.db        # 运行后生成（.gitignore）
main.py               # CLI 入口
```

## 仓库

<https://github.com/Torres999/IntermarketAnalysis>
