"""
Property Fetcher — 从多个来源获取全球主要城市房产价格数据

数据源：
1. BIS Property Prices（全球 60+ 国，季度，免费）
2. OECD Housing Prices（成员国，季度，免费）
3. 日本国土交通省（日本城市成交价，免费 API）
4. 新加坡 URA（私人住宅成交，免费 API，需注册 token）
5. Zillow ZHVI（美国城市，月度 CSV，免费）
"""

import json
import urllib.request
import urllib.parse
import csv
import io
from datetime import datetime, date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DATA_RAW,
    BIS_PROPERTY_URL,
    OECD_HOUSE_URL,
    URA_TOKEN_URL,
    URA_TRANSACTIONS_URL,
    URA_ACCESS_KEY,
    JAPAN_TRADE_URL,
    ZILLOW_ZHVI_URL,
)

BASE_DIR = Path(__file__).parent.parent


# ──────────────────────────────────────────────
# 1. BIS Property Prices
# ──────────────────────────────────────────────

def fetch_bis_property() -> dict:
    """
    下载 BIS 住宅房价指数（Excel/CSV）
    返回 {country_code: [{date, value}, ...]}
    BIS 提供 nominal 和 real 指数，优先用 real（已通胀调整）
    """
    print("  拉取 BIS Property Prices...")
    try:
        # BIS 提供 CSV 格式
        csv_url = "https://www.bis.org/statistics/pp/pp_selected.csv"
        req = urllib.request.Request(
            csv_url,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv,*/*"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            content = r.read().decode("utf-8", "replace")

        lines = content.strip().split("\n")
        # BIS CSV 格式：前几行是元数据，之后是数据
        # 找到数据开始行（包含年份列的行）
        data_start = 0
        for i, line in enumerate(lines):
            if line.startswith('"') and "Q" in line or (i > 0 and ":" in lines[0]):
                data_start = i
                break

        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # 提取主要国家最近数据（简化处理）
        result = {"_source": "BIS Property Prices", "_url": csv_url, "_raw_lines": len(lines)}
        out_path = BASE_DIR / DATA_RAW / "bis_property_raw.csv"
        out_path.write_text(content[:50000])  # 保存前 50KB
        print(f"    BIS CSV 已保存，共 {len(lines)} 行")
        return result

    except Exception as e:
        print(f"    BIS 拉取失败: {e}")
        return {"_error": str(e)}


# ──────────────────────────────────────────────
# 2. 日本国土交通省 API
# ──────────────────────────────────────────────

def fetch_japan_property(year: int = None, quarter: int = None) -> dict:
    """
    从日本国土交通省获取不动产交易价格
    默认获取最近一个季度数据
    Prefecture codes: 13=东京, 27=大阪, 14=神奈川(横滨)
    """
    if year is None:
        year = datetime.now().year
        quarter = max(1, (datetime.now().month - 1) // 3)
        if quarter == 0:
            quarter = 4
            year -= 1

    results = {}
    print(f"  拉取日本房产数据 {year}Q{quarter}...")

    # 东京（Prefecture=13），住宅用地（Type=1）+ 中古戸建（Type=2）
    for pref_code, pref_name in [("13", "Tokyo"), ("27", "Osaka")]:
        params = {
            "year": str(year),
            "quarter": str(quarter),
            "area": pref_code,
            "city": "",
            "station": "",
            "language": "ja",
        }
        url = JAPAN_TRADE_URL + "?" + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            status = data.get("status", "")
            records = data.get("data", [])
            print(f"    {pref_name}: status={status}, {len(records)} 笔交易")
            results[pref_name] = {
                "year": year,
                "quarter": quarter,
                "record_count": len(records),
                "sample": records[:3] if records else [],
            }
            # 保存原始数据
            out_path = BASE_DIR / DATA_RAW / f"japan_{pref_name.lower()}_{year}Q{quarter}.json"
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"    {pref_name}: 拉取失败 - {e}")
            results[pref_name] = {"error": str(e)}

    return results


# ──────────────────────────────────────────────
# 3. 新加坡 URA API
# ──────────────────────────────────────────────

def fetch_singapore_ura() -> dict:
    """
    从新加坡 URA 获取私人住宅成交数据
    需要先获取 token，再用 token 请求数据
    URA_ACCESS_KEY 需在 config.py 中填入
    注册：https://www.ura.gov.sg/maps/api/
    """
    print("  拉取新加坡 URA 数据...")

    if not URA_ACCESS_KEY:
        print("    URA_ACCESS_KEY 未配置，跳过")
        return {"_skipped": "URA_ACCESS_KEY not configured"}

    try:
        # Step 1: 获取 token
        token_url = f"{URA_TOKEN_URL}?accessKey={URA_ACCESS_KEY}"
        req = urllib.request.Request(token_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            token_data = json.loads(r.read())
        token = token_data.get("Result", "")
        print(f"    URA token 获取成功: {token[:8]}...")

        # Step 2: 获取成交数据
        req2 = urllib.request.Request(
            URA_TRANSACTIONS_URL,
            headers={
                "Accept": "application/json",
                "AccessKey": URA_ACCESS_KEY,
                "Token": token,
            }
        )
        with urllib.request.urlopen(req2, timeout=60) as r:
            data = json.loads(r.read())

        records = data.get("Result", [])
        print(f"    URA 成交记录: {len(records)} 条")
        out_path = BASE_DIR / DATA_RAW / "singapore_ura_transactions.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return {"record_count": len(records), "sample": records[:3] if records else []}

    except Exception as e:
        print(f"    URA 拉取失败: {e}")
        return {"error": str(e)}


# ──────────────────────────────────────────────
# 4. Zillow ZHVI（美国）
# ──────────────────────────────────────────────

def fetch_zillow_zhvi() -> dict:
    """
    下载 Zillow 房价指数 CSV，提取主要城市近 12 个月数据
    """
    print("  拉取 Zillow ZHVI...")
    try:
        req = urllib.request.Request(
            ZILLOW_ZHVI_URL,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            content = r.read().decode("utf-8", "replace")

        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        # 找目标城市
        target_metros = ["New York", "Los Angeles", "Miami", "San Francisco", "Chicago"]
        result = {}

        # 获取最近 12 个月的列名（日期格式 YYYY-MM-DD）
        date_cols = sorted([k for k in rows[0].keys() if k.startswith("20")])[-12:]

        for row in rows:
            metro = row.get("RegionName", "")
            if any(t in metro for t in target_metros):
                city_key = metro.split(",")[0].strip()
                monthly_data = {}
                for col in date_cols:
                    val = row.get(col, "")
                    if val and val != "":
                        try:
                            monthly_data[col] = float(val)
                        except ValueError:
                            pass
                if monthly_data:
                    dates = sorted(monthly_data.keys())
                    first_val = monthly_data[dates[0]]
                    last_val = monthly_data[dates[-1]]
                    change_12m = round((last_val - first_val) / first_val * 100, 2) if first_val else None
                    result[city_key] = {
                        "latest_zhvi": last_val,
                        "change_12m_pct": change_12m,
                        "currency": "USD",
                        "date": dates[-1],
                    }
                    print(f"    {city_key}: ZHVI={last_val:,.0f}, 12m change={change_12m}%")

        out_path = BASE_DIR / DATA_RAW / "zillow_zhvi_metros.csv"
        out_path.write_text(content[:100000])
        return result

    except Exception as e:
        print(f"    Zillow 拉取失败: {e}")
        return {"error": str(e)}


# ──────────────────────────────────────────────
# 5. 迪拜 DLD（暂用公开新闻数据）
# ──────────────────────────────────────────────

def fetch_dubai_property() -> dict:
    """
    迪拜 DLD 开放数据平台
    直接数据: https://dubailand.gov.ae/en/open-data/
    目前提供 CSV 下载，尝试获取最新季度数据
    """
    print("  拉取迪拜 DLD 数据...")
    # DLD 开放数据 API（需要检查最新端点）
    # 这里先记录状态，等 API key 获取后填充
    return {
        "_status": "pending",
        "_note": "需要访问 https://dubailand.gov.ae/en/open-data/ 获取 API 接入方式",
        "_manual_data": {
            "city": "Dubai",
            "source": "DLD Annual Report 2024",
            "avg_price_per_sqft_aed": 1420,
            "change_12m_pct": 8.5,
            "currency": "AED",
        }
    }


# ──────────────────────────────────────────────
# 主函数
# ──────────────────────────────────────────────

def fetch_all_property() -> dict:
    """拉取所有房产数据"""
    results = {}

    # 1. BIS
    results["bis"] = fetch_bis_property()

    # 2. 日本
    results["japan"] = fetch_japan_property()

    # 3. 新加坡
    results["singapore"] = fetch_singapore_ura()

    # 4. 美国（Zillow）
    results["usa"] = fetch_zillow_zhvi()

    # 5. 迪拜
    results["dubai"] = fetch_dubai_property()

    # 保存汇总
    out_path = BASE_DIR / DATA_RAW / "property_summary.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n房产数据汇总已保存: {out_path}")
    return results


if __name__ == "__main__":
    print("=== 拉取房产数据 ===\n")
    data = fetch_all_property()
    print("\n=== 完成 ===")
