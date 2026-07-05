# 全球资产流向产品 — 数据源文档

> 整理时间：2026-07-05
> 优先级顺序：房产 > 汇率 > 股票/债券 > 大宗商品

---

## 一、房产数据源

### 🇺🇸 美国

| 名称 | 覆盖内容 | 更新频率 | 费用 | API/获取方式 |
|------|---------|---------|------|------------|
| **Zillow Research** | 全美城市房价指数、挂牌量、成交周期 | 月度/周度 | 免费 | https://www.zillow.com/research/data/ (CSV 下载，无标准 REST API) |
| **Redfin Data Center** | 全美房价中位数、库存、DOM | 周度 | 免费 | https://redfin.com/news/data-center/ (CSV) |
| **Case-Shiller 指数** | 20 大城市房价指数（1987 年起） | 月度（滞后 2 月） | 免费 | FRED API: `SPCS20RSA` 等 series |
| **ATTOM Property Data** | 交易记录、法拍、估值 | 实时 | 付费 $150/月起 | https://api.attomdata.com |
| **HUD (住房与城市发展部)** | 公租房、租金可负担性 | 年度 | 免费 | https://www.huduser.gov/portal/datasets |

### 🇨🇳 中国

| 名称 | 覆盖内容 | 更新频率 | 费用 | API/获取方式 |
|------|---------|---------|------|------------|
| **国家统计局 70 城房价** | 70 城新建/二手房价格指数 | 月度 | 免费 | http://data.stats.gov.cn (网页，需爬虫) |
| **安居客/链家** | 挂牌均价、成交趋势 | 实时 | 无官方 API（爬虫） | 非官方，自行爬取 |
| **Tushare Pro** | 中国房地产板块数据（上市公司） | 日度 | 免费基础版 | https://tushare.pro `pro.query('namechange')` |

### 🌏 全球 / 跨国

| 名称 | 覆盖内容 | 更新频率 | 费用 | API/获取方式 |
|------|---------|---------|------|------------|
| **Knight Frank Global House Price Index** | 56 国房价同比涨跌排名 | 季度 | 免费（PDF报告） | https://www.knightfrank.com/research/global-house-price-index |
| **OECD Housing Prices** | 成员国名义/实际房价指数（1970年起） | 季度 | 免费 | OECD API: `https://stats.oecd.org/SDMX-JSON/data/HOUSE_PRICES` |
| **BIS Property Prices** | 60+ 国住宅房价指数（长历史） | 季度 | 免费 | https://www.bis.org/statistics/pp.htm (CSV) |
| **Numbeo** | 全球城市租金、房价收入比（众包） | 实时（不可靠） | 免费浏览，API 付费 | https://www.numbeo.com/api/ ($50/月) |
| **Global Property Guide** | 租金回报率、房价对比 | 不定期 | 免费浏览 | 无 API，需爬虫 |

### 🇸🇬🇦🇪🇯🇵 特殊市场（外资购房数据相对透明）

| 名称 | 覆盖内容 | 获取方式 |
|------|---------|---------|
| **新加坡 URA** | 各区成交价、外国买家比例 | https://www.ura.gov.sg/reis/index |
| **迪拜 DLD (土地局)** | 成交量、外资国籍分布 | https://dubailand.gov.ae/en/open-data |
| **日本国土交通省** | 不动产交易价格 | https://www.land.mlit.go.jp/webland/api.html (免费 API) |
| **澳大利亚 CoreLogic** | 八大城市房价指数 | 付费，部分指数免费发布 |

---

## 二、汇率数据源

| 名称 | 覆盖内容 | 更新频率 | 费用 | API 端点 |
|------|---------|---------|------|---------|
| **ExchangeRate-API** | 170+ 货币实时汇率 | 实时 | 免费 1500次/月；$12/月无限 | `https://v6.exchangerate-api.com/v6/{key}/latest/USD` |
| **Open Exchange Rates** | 专业级汇率 | 实时 | $12/月起 | `https://openexchangerates.org/api/latest.json` |
| **Fixer.io** | 欧洲央行数据 | 每日 | 免费 100次/月 | `http://data.fixer.io/api/latest` |
| **FRED (美联储)** | 主要货币对历史（1971年起） | 每日 | 完全免费 | `https://api.stlouisfed.org/fred/series/observations?series_id=DEXUSEU` |
| **BIS 有效汇率 (REER/NEER)** | 实际/名义有效汇率（60国）| 月度 | 免费 | `https://www.bis.org/statistics/eer.htm` |
| **IMF COFER** | 各国外汇储备货币构成 | 季度 | 免费 | `https://data.imf.org/api/SDMX/2.1/data/COFER` |

---

## 三、股票 / 基金流向数据源

| 名称 | 覆盖内容 | 更新频率 | 费用 | API/获取方式 |
|------|---------|---------|------|------------|
| **Yahoo Finance (yfinance)** | 全球股价、ETF 持仓、基本面 | 实时（延迟15分钟） | 免费 | `pip install yfinance` |
| **Alpha Vantage** | 股票资金流、技术指标 | 实时 | 免费 25次/日；$50/月专业版 | `https://www.alphavantage.co/query` |
| **ICI (投资公司协会)** | 美国共同基金/ETF 每周净申购 | 每周三 | 免费（CSV） | https://www.ici.org/research/stats |
| **ETF.com / etfdb.com** | ETF 资金净流入/流出 | 每日 | 免费浏览，API 付费 | https://etfdb.com |
| **沪深港通数据** | 北向/南向每日净买入（陆股通） | 每日收盘后 | 免费 | 东方财富 API / Tushare `moneyflow_hsgt` |
| **SEC EDGAR (13F)** | 机构投资者季度持仓 | 季度（45天内披露） | 免费 | `https://data.sec.gov/submissions/` |
| **CFTC COT 报告** | 期货持仓（机构/散户/商业分类） | 每周五 | 免费 | https://www.cftc.gov/MarketReports/CommitmentsofTraders |

---

## 四、债券数据源

| 名称 | 覆盖内容 | 更新频率 | 费用 | API/获取方式 |
|------|---------|---------|------|------------|
| **FRED** | 美债收益率曲线（全期限）、TIPS | 实时 | 免费 | `https://api.stlouisfed.org/fred/series/observations?series_id=DGS10` |
| **美国财政部 TIC** | 外国持有美债（国别）| 月度（滞后6-8周）| 免费 | https://ticdata.treasury.gov |
| **ECB (欧洲央行)** | 欧元区债券收益率 | 每日 | 免费 | `https://data.ecb.europa.eu/api/data/YC` |
| **中国债券信息网** | 银行间市场收益率曲线 | 每日 | 免费 | http://yield.chinabond.com.cn |
| **BIS Debt Securities** | 全球债券发行统计 | 季度 | 免费 | https://www.bis.org/statistics/secstats.htm |

---

## 五、大宗商品数据源

| 名称 | 覆盖内容 | 更新频率 | 费用 | API/获取方式 |
|------|---------|---------|------|------------|
| **世界黄金协会 (WGC)** | 全球黄金 ETF 持仓、央行购金 | 月度 | 免费 | https://www.gold.org/goldhub/data |
| **EIA (美国能源信息署)** | 石油/天然气库存、产量、流向 | 每周 | 免费 | `https://api.eia.gov/v2/` |
| **LME (伦敦金属交易所)** | 铜/铝/锌等基本金属价格+库存 | 实时 | 部分免费 | https://www.lme.com/en/market-data |
| **CFTC COT** | 黄金/原油/农产品期货持仓 | 每周五 | 免费 | 同上 |
| **USDA (美国农业部)** | 农产品供需报告 (WASDE) | 月度 | 免费 | https://apps.fas.usda.gov/psdonline/app/index.html |

---

## 六、宏观综合数据源（跨资产）

| 名称 | 覆盖内容 | 费用 | API/获取方式 |
|------|---------|------|------------|
| **FRED (圣路易斯联储)** | 50万+ 美国及全球宏观时间序列 | 完全免费 | `https://fred.stlouisfed.org/docs/api/fred/` |
| **World Bank Open Data** | 各国 GDP、通胀、贸易等 | 免费 | `https://api.worldbank.org/v2/` |
| **IMF Data API** | 全球经济指标 (WEO/IFS/COFER) | 免费 | `https://datahelp.imf.org/knowledgebase/articles/667681` |
| **TradingEconomics** | 全球 196 国宏观指标 | 免费浏览；$75/月 API | `https://api.tradingeconomics.com` |
| **MacroMicro (财经M平方)** | 亚太宏观指标、图表 | 免费基础版 | 网页为主，API 付费 |

---

## 数据源优先级建议（房产优先策略）

```
Phase 1 MVP（0成本）：
  房产：OECD + BIS + Zillow CSV + 国家统计局 + 日本国土省 API + 新加坡 URA + 迪拜 DLD
  汇率：FRED + ExchangeRate-API（免费版）
  辅助：FRED 宏观背景数据

Phase 2（少量付费）：
  Numbeo API ($50/月) — 补充全球城市租金回报率
  ExchangeRate-API Pro ($12/月) — 解除请求限制

Phase 3（验证后）：
  ATTOM ($150/月) — 美国房产精细数据
  EPFR Global — 基金流量（按需评估）
```

---

## 房产 × 汇率联动的核心计算逻辑

```
外币购买力调整后房价涨幅 = 本地房价涨幅（本地货币）+ 本地货币对目标货币升贬值幅度

示例：
  日本东京房价 2023→2024 日元涨 +8%
  日元兑人民币同期贬值 -12%
  → 中国买家视角：实际购买力涨幅 = 8% - 12% = -4%（实际便宜了）
```

这个计算每个城市都做一遍，就是产品最核心的差异化指标。

---

*最后更新：2026-07-05*
