# Global Asset Flow — 产品迭代 PRD

**文档版本：** v1.1  
**最后更新：** 2026-07-05  
**负责人：** Nicole  
**状态：** 待评审  

---

## 一、产品背景

**global-asset-flow** 是一个面向中国买家的全球主要城市房产价值追踪系统。

核心逻辑：用「本地房价涨幅 × 汇率变动」计算 **CNY 视角的真实调整后收益**，帮助用户判断哪个城市的资产在人民币计价下正在升值/贬值。

**当前状态（v1.0 已上线）：**
- 覆盖 8 个城市：Tokyo / Singapore / Sydney / London / Shanghai / Hong Kong / New York / Dubai
- API 部署：https://global-asset-flow.vercel.app
- 端点：`/api/cities`、`/api/cities/{city}`、`/api/ranking`、`/api/summary`

---

## 二、现有问题 & 优化方向

### 🔴 P0 — 数据完整性

**问题 1：东京无房价数据**
- 现状：`property_fetcher.py` 里东京走 `mock_tokyo_data()`，返回空壳，`city_reports.json` 里 Tokyo 无 `local_price_change_pct`
- 根因：Zillow ZHVI 不覆盖日本，需要接日本官方数据源
- 方案：接 [MLIT 不動産価格指数](https://www.mlit.go.jp/totikensangyo/totikensangyo_tk5_000085.html)（月度更新，CSV 可下载）或通过 StatLib Japan API
- 验收：Tokyo 能正常显示本地房价涨幅 + 调整后收益

**问题 2：香港/新加坡数据延迟大**
- 现状：香港走 HKSAR open data（稳定），新加坡走 URA（3-6 个月延迟）
- 方案：补充 PropertyGuru、SquareFoot 爬虫作为近实时估算（明确标注数据源和延迟）

---

### 🟠 P1 — 数据刷新机制

**问题 3：数据不会自动更新**
- 现状：`run.py` 需要手动触发，Vercel 上的 `city_reports.json` 是构建时的快照
- 方案 A（短期）：Vercel Cron Job，每月 1 日自动触发 `/api/refresh` 重跑 pipeline
- 方案 B（中期）：数据写入 Supabase，API 查库而非读 JSON 文件，支持更细粒度刷新
- 验收：无需手动推代码即可获得最新数据

**问题 4：汇率数据时效性不透明**
- 现状：FRED 汇率数据有 1-3 天延迟，API 返回中没有标注 `data_as_of` 字段
- 方案：在每个城市 response 里加 `fx_as_of`（汇率数据日期）、`price_as_of`（房价数据日期）
- 验收：`/api/cities/Tokyo` 返回的 JSON 里包含完整 data timestamp

---

### 🟡 P2 — API 可用性提升

**问题 5：FRED Key 硬编码在源代码里**
- 现状：`config.py` 里直接写明文 Key，已推到 GitHub public repo
- 风险：Key 可能被 GitHub 扫描器检测并自动 revoke
- 方案：改用 Vercel Environment Variables，`config.py` 改读 `os.environ.get("FRED_API_KEY")`
- 验收：config.py 里无明文 Key，Vercel dashboard 配置环境变量

**问题 6：缺少数据说明端点**
- 现状：用户调用 API 不知道数据是什么周期、什么口径
- 方案：新增 `GET /api/meta`，返回各城市数据源说明、更新频率、最后刷新时间
- 验收：`/api/meta` 返回结构化说明，可被 AI 对话直接读取

**问题 7：ranking 无法按绝对值排序**
- 现状：ranking 按调整后收益排，正负混在一起，不直观
- 方案：新增 `?metric=absolute_return` 参数，支持按绝对值排序
- 验收：`/api/ranking?order=desc&only_complete=true` 返回迪拜 > 悉尼 > 纽约...

---

### 🟢 P3 — 扩展性

**问题 8：城市覆盖不足**
- 缺失：曼谷、吉隆坡、多伦多、温哥华（都是中国买家热门目的地）
- 方案：
  - 泰国：REIC（泰国房地产信息中心）API
  - 马来西亚：NAPIC（全国产权信息中心）
  - 加拿大：CREA（加拿大房地产协会）月度数据
- 验收：覆盖城市扩展到 12 个

**问题 9：缺少 AI 分析层**
- 现状：`/api/summary` 返回原始数字，需要用户自己或 AI 二次分析
- 方案：新增 `GET /api/insights`，用 LLM 生成 3-5 条可操作结论
  - 示例："上海和香港 CNY 调整后均跌超 5%，反映内地楼市压力 + 港元联系汇率稳定；若 CNY 继续走弱，香港更具入场逻辑"
- 验收：`/api/insights` 返回结构化 JSON，含 conclusion + reasoning + confidence

---

## 三、优先级排序

| 优先级 | 任务 | 工作量 | 影响 |
|--------|------|--------|------|
| P0 | 修东京数据（接 MLIT）| M | 数据完整性 |
| P0 | FRED Key 移出源码 → 环境变量 | S | 安全 |
| P1 | 自动刷新（Vercel Cron）| M | 数据时效 |
| P1 | 加 data timestamp 字段 | S | 透明度 |
| P2 | 新增 `/api/meta` 端点 | S | 可用性 |
| P2 | ranking 绝对值排序 | S | 易用性 |
| P3 | 扩展城市（曼谷/多伦多等）| L | 覆盖面 |
| P3 | `/api/insights` AI 分析层 | L | 差异化 |

---

## 四、技术约束

- 部署平台：Vercel（Hobby 免费额度，Serverless Functions 执行上限 10s）
- 数据存储：当前用 JSON 文件（无数据库），P1 前保持不变
- 语言：Python 3.11 + FastAPI
- GitHub：https://github.com/YuqingNicole/global-asset-flow（public repo，注意不要提交 secrets）

---

## 五、验收标准

**v1.1 完成标志：**
- [ ] FRED Key 移到环境变量，config.py 无明文 key
- [ ] Tokyo 房价数据接通
- [ ] 所有城市 response 包含 `data_as_of` 字段
- [ ] Vercel Cron 每月自动刷新一次数据
- [ ] `/api/meta` 端点上线
