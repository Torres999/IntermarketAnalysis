# 数据源选型（稳定性优先）

本工程只使用 **Scrapling Fetcher（HTTP）** 与 **StealthySession（浏览器抓 Investing/TradingView 图表）**，不引入 Tushare token 等第三方账号。

| 资产类 | 序列 | 数据源 | 稳定性 | 说明 |
| --- | --- | --- | --- | --- |
| **汇** | `rmb_*` | [中国货币网](https://www.chinamoney.com.cn/chinese/bkrmbidx/) Excel POST | ★★★★★ | 官方导出接口，纯 HTTP，已验证可 5 年分段拉取 |
| **大宗** | `comm_au/cu/sc/rb` | [新浪财经](https://finance.sina.com.cn/) 期货日 K JSONP | ★★★★☆ | 主连 `AU0/SC0/CU0/RB0`，纯 HTTP，历史长、响应快 |
| **大宗综合** | `nh_commodity` | 本地合成 | ★★★★☆ | 金/铜/油/螺等权归一化指数，依赖上述四条 Sina 序列 |
| **债** | `cn10y_yield` | 中国货币网 `ClsYldCurvHis`（10Y 国债到期收益率）+ Investing 历史页补近期 | ★★★★ | HTTP 按月分页；Investing 页 sbcharts 数据异常已弃用 |
| **债** | `cn10y` | TradingView / 国债期货图表 | ★★★☆ | 价格口径，浏览器抓包 |
| **股** | 现货指数 | Investing.com 图表 5 年 | ★★★☆ | 反爬较重，建议 `INTERMARKET_REAL_CHROME=1` |
| **股** | 股指期货 | Investing.com 图表 5 年 | ★★★☆ | 需用 `scripts/discover_pair_ids.py` 校验 pair_id |

## 未采用的数据源

| 来源 | 原因 |
| --- | --- |
| 南华指数官网 API | 无公开 HTTP 历史端点，需商务/API 授权 |
| Tushare / Wind | 需积分或 license，不符合「仅 Scrapling + Python」约束 |
| 东方财富 push2his | 在本环境对期货主连 `secid` 返回空数据（`rc=100`），稳定性不足 |
| Investing 大宗商品 | 本机对 `cn.investing.com` 连接不稳定；国内期货改走 **Sina** |

## 运维建议

1. **日常**：双击 `start.bat` 或 `.\start.ps1` → 自动增量更新 + 打开浏览器。  
2. **首次或 Investing 序列缺失**：`python main.py start --full-backfill`（耗时较长）。  
3. **pair_id 异常**：`python scripts/discover_pair_ids.py` 后更新 `config.py`。
