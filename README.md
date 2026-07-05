# Global Asset Flow API

全球房产流向数据 API，**CNY（人民币）视角**，追踪主要城市的调整后真实收益。

## 端点

| 端点 | 说明 |
|------|------|
| `GET /api/cities` | 所有城市完整数据 |
| `GET /api/cities/{city}` | 单个城市（如 `/api/cities/Dubai`）|
| `GET /api/ranking` | 按调整后收益排名 |
| `GET /api/ranking?order=desc` | 反向排名 |
| `GET /api/ranking?only_complete=true` | 只含完整数据城市 |
| `GET /api/summary` | AI 可读的文字摘要 |

## 覆盖城市

Tokyo · Singapore · Sydney · London · Shanghai · Hong Kong · New York · Dubai

## 部署

```bash
npm i -g vercel
vercel --prod
```

## 本地运行

```bash
pip install -r requirements.txt
python api/index.py
# → http://localhost:8000/api/summary
```

## 数据说明

- **调整后收益** = 本地房价涨幅 × 汇率变动（精确复利公式）
- **基准货币**：CNY（中国买家视角）
- **汇率来源**：Open Exchange Rates API
- **房价来源**：Zillow ZHVI、DLD、URA、CoreLogic、UK Land Registry、国家统计局
