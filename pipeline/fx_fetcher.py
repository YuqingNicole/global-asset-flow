"""
FX Fetcher — 从 FRED 获取主要货币汇率历史数据
支持回退到 ExchangeRate-API 获取当前汇率
"""

import json
import urllib.request
import urllib.parse
import csv
import io
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import FRED_BASE, FRED_API_KEY, FX_BASE, FX_API_KEY, DATA_RAW, CITIES, BASE_CURRENCY

BASE_DIR = Path(__file__).parent.parent


def fetch_fred_series(series_id: str, observation_start: str = None, api_key: str = None) -> list[dict]:
    """从 FRED 获取时间序列数据"""
    key = api_key or FRED_API_KEY
    params = {
        "series_id": series_id,
        "api_key": key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": "60",  # 最近 60 个月
    }
    if observation_start:
        params["observation_start"] = observation_start

    url = FRED_BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    return data.get("observations", [])


def fetch_current_fx_fallback(base: str = "USD") -> dict:
    """
    备用：从 ExchangeRate-API 获取当前汇率（当 FRED key 未配置时使用）
    返回 {currency_code: rate_vs_usd, ...}
    """
    if not FX_API_KEY:
        # 无 key 时用免费端点（有限制）
        url = f"https://open.er-api.com/v6/latest/{base}"
    else:
        url = f"{FX_BASE}/{FX_API_KEY}/latest/{base}"

    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    return data.get("rates", {})


def calc_fx_change_pct(observations: list[dict], periods: int = 12) -> float | None:
    """
    计算过去 N 个月的汇率变动百分比
    FRED 汇率格式通常是 外币/USD，例如 DEXJPUS = JPY per USD
    返回正数 = 外币升值（对美元），负数 = 外币贬值
    """
    valid = [o for o in observations if o.get("value") not in (".", None, "")]
    if len(valid) < 2:
        return None

    # 最新值（observations 按 desc 排列）
    latest = float(valid[0]["value"])
    # N 个月前的值（如果有）
    past = float(valid[min(periods, len(valid) - 1)]["value"])

    if past == 0:
        return None

    # DEXJPUS 是 JPY/USD，值越大 = 日元越弱
    # 外币对美元升值 = 汇率下降（需要更少外币换 1 美元）
    fx_change_pct = (past - latest) / past * 100  # 正数 = 外币升值 vs USD
    return round(fx_change_pct, 2)


def get_usd_to_cny() -> float:
    """获取当前 USD/CNY 汇率（用于最终折算到人民币）"""
    try:
        obs = fetch_fred_series("DEXCHUS")  # CNY per USD
        valid = [o for o in obs if o.get("value") not in (".", None, "")]
        if valid:
            return float(valid[0]["value"])
    except Exception:
        pass
    # 备用：用 ExchangeRate-API
    try:
        rates = fetch_current_fx_fallback("USD")
        return rates.get("CNY", 7.25)
    except Exception:
        return 7.25  # 硬编码备用值


def fetch_all_fx() -> dict:
    """
    拉取所有目标城市的汇率数据
    返回 {city: {currency, change_12m_pct, latest_rate_vs_usd}}
    """
    results = {}
    usd_cny = get_usd_to_cny()
    print(f"USD/CNY: {usd_cny}")

    for city_cfg in CITIES:
        city = city_cfg["city"]
        currency = city_cfg["currency"]
        fred_fx = city_cfg.get("fred_fx")

        if currency == "USD":
            results[city] = {
                "currency": "USD",
                "change_12m_pct": 0.0,
                "latest_rate_vs_usd": 1.0,
                "usd_cny": usd_cny,
            }
            print(f"  {city} (USD): base currency, no change")
            continue

        if currency == "AED":
            # AED 固定汇率 3.67 AED/USD
            results[city] = {
                "currency": "AED",
                "change_12m_pct": 0.0,
                "latest_rate_vs_usd": 3.67,
                "usd_cny": usd_cny,
            }
            print(f"  {city} (AED): pegged to USD, no change")
            continue

        if fred_fx and FRED_API_KEY:
            try:
                obs = fetch_fred_series(fred_fx)
                valid = [o for o in obs if o.get("value") not in (".", None, "")]
                latest_rate = float(valid[0]["value"]) if valid else None
                change = calc_fx_change_pct(obs, periods=12)
                results[city] = {
                    "currency": currency,
                    "change_12m_pct": change,
                    "latest_rate_vs_usd": latest_rate,
                    "usd_cny": usd_cny,
                }
                print(f"  {city} ({currency}): rate={latest_rate}, 12m change={change}%")
            except Exception as e:
                print(f"  {city} ({currency}): FRED error - {e}")
                results[city] = {"currency": currency, "change_12m_pct": None, "latest_rate_vs_usd": None, "usd_cny": usd_cny}
        else:
            # 无 FRED key，用 ExchangeRate-API 只取当前汇率（无历史变动）
            try:
                rates = fetch_current_fx_fallback("USD")
                rate = rates.get(currency)
                results[city] = {
                    "currency": currency,
                    "change_12m_pct": None,  # 无历史数据，无法计算
                    "latest_rate_vs_usd": rate,
                    "usd_cny": usd_cny,
                }
                print(f"  {city} ({currency}): rate={rate} (no FRED key, no 12m change)")
            except Exception as e:
                print(f"  {city} ({currency}): fallback error - {e}")
                results[city] = {"currency": currency, "change_12m_pct": None, "latest_rate_vs_usd": None, "usd_cny": usd_cny}

    # 保存原始数据
    out_path = BASE_DIR / DATA_RAW / "fx_data.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n汇率数据已保存: {out_path}")
    return results


if __name__ == "__main__":
    print("=== 拉取汇率数据 ===")
    data = fetch_all_fx()
    print("\n结果:")
    for city, info in data.items():
        print(f"  {city}: {info}")
