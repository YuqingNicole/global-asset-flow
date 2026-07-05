"""
Calculator — 计算汇率调整后的房产真实收益
核心公式：外币购买力调整后涨幅 = 本地房价涨幅 + 本地货币对基准货币升贬值幅度
"""

import json
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import BASE_CURRENCY, CITIES, DATA_PROCESSED, REPORTS_DIR

BASE_DIR = Path(__file__).parent.parent


def calc_adjusted_return(
    local_price_change_pct: float | None,
    fx_change_pct: float | None,
    city: str,
    currency: str,
) -> dict:
    """
    计算基准货币视角下的真实房产收益

    Args:
        local_price_change_pct: 本地货币计价的房价涨幅 (%)
        fx_change_pct: 本地货币相对美元的升贬值 (%) 正=升值，负=贬值
        city: 城市名
        currency: 本地货币

    Returns:
        dict with adjusted_return_pct and breakdown
    """
    if local_price_change_pct is None or fx_change_pct is None:
        return {
            "city": city,
            "currency": currency,
            "local_price_change_pct": local_price_change_pct,
            "fx_change_pct": fx_change_pct,
            "adjusted_return_pct": None,
            "status": "insufficient_data",
        }

    # 简化公式（精确公式应用复利）
    # adjusted = (1 + price_change/100) * (1 + fx_change/100) - 1
    adjusted = (1 + local_price_change_pct / 100) * (1 + fx_change_pct / 100) - 1
    adjusted_pct = round(adjusted * 100, 2)

    return {
        "city": city,
        "currency": currency,
        "local_price_change_pct": round(local_price_change_pct, 2),
        "fx_change_pct": round(fx_change_pct, 2),
        "adjusted_return_pct": adjusted_pct,
        "interpretation": _interpret(adjusted_pct),
        "status": "ok",
    }


def _interpret(pct: float) -> str:
    if pct >= 10:
        return "🔴 强势上涨（外资买入成本显著上升）"
    elif pct >= 5:
        return "🟠 温和上涨"
    elif pct >= 0:
        return "🟡 基本持平或小幅上涨"
    elif pct >= -5:
        return "🟢 小幅下跌（外资视角性价比提升）"
    else:
        return "💚 大幅下跌（外资购入窗口期）"


def build_city_report(fx_data: dict, property_data: dict) -> list[dict]:
    """
    整合汇率 + 房产数据，生成各城市报告
    """
    reports = []

    # 城市到房产数据的映射（需要手动对齐各数据源）
    # 格式: {city_name: {local_price_change_pct, latest_price, source, ...}}
    property_map = {}

    # 从 Zillow 提取美国城市
    usa_data = property_data.get("usa", {})
    for city_key, info in usa_data.items():
        if isinstance(info, dict) and "change_12m_pct" in info:
            property_map[city_key] = {
                "local_price_change_pct": info["change_12m_pct"],
                "latest_price": info.get("latest_zhvi"),
                "price_unit": "USD (median home value)",
                "source": "Zillow ZHVI",
                "date": info.get("date"),
            }

    # 从日本数据提取（成交量为主，暂用占位数据）
    japan_data = property_data.get("japan", {})
    if "Tokyo" in japan_data and "error" not in japan_data["Tokyo"]:
        # 日本国土省 API 返回成交记录，需额外聚合计算均价变化
        # 暂用 2024 年公开数据作为占位
        property_map["Tokyo"] = {
            "local_price_change_pct": 7.2,  # 2024 年东京公寓均价涨幅（来源：不动产经济研究所）
            "latest_price": 9280,
            "price_unit": "万日元/套（东京新建公寓均价）",
            "source": "不動産経済研究所 2024",
            "date": "2024-12",
            "_note": "Japan API 已连通，具体均价聚合逻辑待完善",
        }

    # 新加坡（URA 数据已拉取，聚合逻辑待完善）
    property_map["Singapore"] = {
        "local_price_change_pct": 3.9,  # URA 2024 全年私人住宅价格指数涨幅
        "latest_price": 2280,
        "price_unit": "SGD/sqft（中央区非有地私人住宅）",
        "source": "URA Property Price Index Q4 2024",
        "date": "2024-Q4",
    }

    # 迪拜
    property_map["Dubai"] = {
        "local_price_change_pct": 8.5,
        "latest_price": 1420,
        "price_unit": "AED/sqft",
        "source": "DLD Annual Report 2024",
        "date": "2024-12",
    }

    # 香港（暂用公开数据）
    property_map["Hong Kong"] = {
        "local_price_change_pct": -6.5,  # 2024 年港楼下跌
        "latest_price": 11500,
        "price_unit": "HKD/sqft",
        "source": "差饷物業估價署 2024",
        "date": "2024-12",
    }

    # 上海（国家统计局 70 城数据）
    property_map["Shanghai"] = {
        "local_price_change_pct": -3.5,  # 2024 年新建商品住宅价格指数
        "latest_price": 55000,
        "price_unit": "CNY/sqm（新建商品住宅）",
        "source": "国家统计局 70 城房价指数 2024",
        "date": "2024-12",
    }

    # 悉尼（CoreLogic 公开摘要）
    property_map["Sydney"] = {
        "local_price_change_pct": 4.9,
        "latest_price": 1400000,
        "price_unit": "AUD（中位数）",
        "source": "CoreLogic Home Value Index 2024",
        "date": "2024-12",
    }

    # 伦敦
    property_map["London"] = {
        "local_price_change_pct": 2.1,
        "latest_price": 530000,
        "price_unit": "GBP（中位数）",
        "source": "UK Land Registry HPI 2024",
        "date": "2024-12",
    }

    # 纽约（从 Zillow 已覆盖）
    if "New York" not in property_map:
        property_map["New York"] = {
            "local_price_change_pct": 4.3,
            "latest_price": 750000,
            "price_unit": "USD（中位数）",
            "source": "Zillow ZHVI 2024",
            "date": "2024-12",
        }

    # 生成各城市报告
    for city_cfg in CITIES:
        city = city_cfg["city"]
        fx_info = fx_data.get(city, {})

        # 匹配房产数据
        prop_info = None
        for key in [city, city.split(",")[0]]:
            if key in property_map:
                prop_info = property_map[key]
                break

        if prop_info is None:
            prop_info = {"local_price_change_pct": None, "source": "no data"}

        report = calc_adjusted_return(
            local_price_change_pct=prop_info.get("local_price_change_pct"),
            fx_change_pct=fx_info.get("change_12m_pct"),
            city=city,
            currency=city_cfg["currency"],
        )

        # 附加额外信息
        report.update({
            "country": city_cfg["country"],
            "latest_price": prop_info.get("latest_price"),
            "price_unit": prop_info.get("price_unit"),
            "price_source": prop_info.get("source"),
            "price_date": prop_info.get("date"),
            "fx_rate_vs_usd": fx_info.get("latest_rate_vs_usd"),
            "base_currency": BASE_CURRENCY,
        })

        reports.append(report)

    # 按调整后收益排序
    reports.sort(
        key=lambda x: x.get("adjusted_return_pct") if x.get("adjusted_return_pct") is not None else -999
    )

    # 保存处理结果
    out_path = BASE_DIR / DATA_PROCESSED / "city_reports.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(reports, indent=2, ensure_ascii=False))
    print(f"城市报告已保存: {out_path}")

    return reports


def generate_text_report(reports: list[dict]) -> str:
    """生成可读的文本报告"""
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# 全球房产流向报告 ({now})",
        f"基准货币视角：{BASE_CURRENCY}（中国买家视角）",
        "数据周期：近 12 个月",
        "",
        "---",
        "",
        "## 城市排名（按调整后收益升序，越低越适合买入）",
        "",
    ]

    for i, r in enumerate(reports, 1):
        city = r["city"]
        country = r["country"]
        adj = r.get("adjusted_return_pct")
        local_chg = r.get("local_price_change_pct")
        fx_chg = r.get("fx_change_pct")
        interp = r.get("interpretation", "")
        price = r.get("latest_price")
        price_unit = r.get("price_unit", "")
        source = r.get("price_source", "")

        if adj is not None:
            lines.append(f"### {i}. {city}（{country}）")
            lines.append(f"- 调整后收益：**{adj:+.1f}%** {interp}")
            lines.append(f"  - 本地房价涨幅：{local_chg:+.1f}%")
            lines.append(f"  - 汇率变动（vs USD）：{fx_chg:+.1f}%")
            if price:
                lines.append(f"  - 当前价格：{price:,} {price_unit}")
            lines.append(f"  - 数据来源：{source}")
            lines.append("")
        else:
            lines.append(f"### {i}. {city}（{country}）— 数据不足")
            lines.append("")

    lines += [
        "---",
        "",
        "## 注意事项",
        "- 汇率调整收益为简化计算，未考虑税费、贷款成本、流动性等因素",
        "- 部分城市使用 2024 年公开报告数据（非实时），实际数据需接入各数据源 API",
        "- 日本/新加坡 API 已连通，聚合逻辑持续完善中",
        "- Dubai AED 固定挂钩 USD，汇率变动为 0",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
    ]

    return "\n".join(lines)
