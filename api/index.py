"""
Global Asset Flow API — Vercel Serverless
端点：
  GET /api/cities          — 所有城市数据
  GET /api/cities/{city}   — 单个城市
  GET /api/ranking         — 按调整后收益排名
  GET /api/summary         — 文字摘要（给 AI 调用）
  POST /api/refresh        — 重新跑 pipeline（需 secret）
"""

import json
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# 把 pipeline 目录加入路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))

app = FastAPI(
    title="Global Asset Flow API",
    description="全球主要城市房产价格 + 汇率调整后真实收益，中国买家视角",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = ROOT / "data" / "processed" / "city_reports.json"


def load_data() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


# ─────────────────────────────────────────
# GET /api/cities
# ─────────────────────────────────────────
@app.get("/api/cities")
def get_all_cities():
    """返回所有城市的完整数据"""
    data = load_data()
    return {"count": len(data), "cities": data}


# ─────────────────────────────────────────
# GET /api/cities/{city}
# ─────────────────────────────────────────
@app.get("/api/cities/{city}")
def get_city(city: str):
    """返回单个城市数据（大小写不敏感）"""
    data = load_data()
    city_lower = city.lower()
    for item in data:
        if item["city"].lower() == city_lower:
            return item
    raise HTTPException(status_code=404, detail=f"City '{city}' not found")


# ─────────────────────────────────────────
# GET /api/ranking
# ─────────────────────────────────────────
@app.get("/api/ranking")
def get_ranking(
    order: str = Query("asc", description="asc=低到高(买入机会), desc=高到低"),
    only_complete: bool = Query(False, description="只返回有完整数据的城市"),
):
    """按调整后收益排名"""
    data = load_data()

    if only_complete:
        data = [d for d in data if d.get("adjusted_return_pct") is not None]

    data.sort(
        key=lambda x: x.get("adjusted_return_pct") if x.get("adjusted_return_pct") is not None else 999,
        reverse=(order == "desc"),
    )

    return {
        "order": order,
        "base_currency": "CNY",
        "ranking": [
            {
                "rank": i + 1,
                "city": d["city"],
                "country": d["country"],
                "adjusted_return_pct": d.get("adjusted_return_pct"),
                "interpretation": d.get("interpretation", "数据不足"),
                "status": d.get("status"),
            }
            for i, d in enumerate(data)
        ],
    }


# ─────────────────────────────────────────
# GET /api/summary
# ─────────────────────────────────────────
@app.get("/api/summary")
def get_summary():
    """
    给 AI 对话调用的文字摘要
    返回精简的文字描述，方便 Claude 直接读取并回答问题
    """
    data = load_data()
    complete = [d for d in data if d.get("adjusted_return_pct") is not None]
    incomplete = [d for d in data if d.get("adjusted_return_pct") is None]

    lines = ["【全球房产流向 — CNY 视角调整后收益排名】", ""]

    # 有数据的城市
    for d in sorted(complete, key=lambda x: x["adjusted_return_pct"]):
        adj = d["adjusted_return_pct"]
        interp = d.get("interpretation", "")
        local = d.get("local_price_change_pct", "N/A")
        fx = d.get("fx_change_pct", "N/A")
        lines.append(
            f"• {d['city']}（{d['country']}）: 调整后 {adj:+.1f}% {interp}"
            f" | 本地房价 {local:+.1f}% | 汇率 {fx:+.1f}%"
            if isinstance(local, float) and isinstance(fx, float)
            else f"• {d['city']}（{d['country']}）: 调整后 {adj:+.1f}% {interp}"
        )

    # 数据不足的城市
    if incomplete:
        lines.append("")
        lines.append("【数据不足（汇率数据缺失，需配置 FRED API Key）】")
        for d in incomplete:
            local = d.get("local_price_change_pct")
            price = d.get("latest_price")
            unit = d.get("price_unit", "")
            local_str = f"本地房价 {local:+.1f}%" if local is not None else "无房价数据"
            price_str = f"| 当前价格 {price:,} {unit}" if price else ""
            lines.append(f"• {d['city']}（{d['country']}）: {local_str} {price_str}")

    lines += [
        "",
        "注：调整后收益 = 本地房价涨幅 × 汇率变动（CNY 视角）",
        "数据来源：Zillow ZHVI / DLD / URA / CoreLogic / UK Land Registry / 国家统计局",
        f"数据周期：近 12 个月（截至 2024-12 ~ 2026-05）",
    ]

    return {
        "summary": "\n".join(lines),
        "cities_with_data": len(complete),
        "cities_total": len(data),
    }


# ─────────────────────────────────────────
# 本地运行入口
# ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
