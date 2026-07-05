"""
主运行脚本 — 全球房产流向 Pipeline
用法：python run.py [--skip-fetch]
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "pipeline"))
from fx_fetcher import fetch_all_fx
from property_fetcher import fetch_all_property
from calculator import build_city_report, generate_text_report
from config import DATA_RAW, DATA_PROCESSED, REPORTS_DIR

BASE_DIR = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser(description="全球房产流向 Pipeline")
    parser.add_argument("--skip-fetch", action="store_true", help="跳过数据拉取，使用已缓存数据")
    args = parser.parse_args()

    # 确保目录存在
    for d in [DATA_RAW, DATA_PROCESSED, REPORTS_DIR]:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("全球房产流向 Pipeline")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # ── Step 1: 拉取汇率数据 ──
    fx_data = {}
    fx_cache = BASE_DIR / DATA_RAW / "fx_data.json"
    if args.skip_fetch and fx_cache.exists():
        print("\n[Step 1] 使用缓存汇率数据")
        fx_data = json.loads(fx_cache.read_text())
    else:
        print("\n[Step 1] 拉取汇率数据...")
        try:
            fx_data = fetch_all_fx()
            print("  ✓ 汇率数据拉取完成")
        except Exception as e:
            print(f"  ✗ 汇率数据拉取失败: {e}")
            if fx_cache.exists():
                fx_data = json.loads(fx_cache.read_text())
                print("  → 使用缓存数据")

    # ── Step 2: 拉取房产数据 ──
    property_data = {}
    prop_cache = BASE_DIR / DATA_RAW / "property_summary.json"
    if args.skip_fetch and prop_cache.exists():
        print("\n[Step 2] 使用缓存房产数据")
        property_data = json.loads(prop_cache.read_text())
    else:
        print("\n[Step 2] 拉取房产数据...")
        try:
            property_data = fetch_all_property()
            print("  ✓ 房产数据拉取完成")
        except Exception as e:
            print(f"  ✗ 房产数据拉取失败: {e}")
            if prop_cache.exists():
                property_data = json.loads(prop_cache.read_text())
                print("  → 使用缓存数据")

    # ── Step 3: 计算调整后收益 ──
    print("\n[Step 3] 计算汇率调整后收益...")
    reports = build_city_report(fx_data, property_data)
    print(f"  ✓ 已生成 {len(reports)} 个城市报告")

    # ── Step 4: 输出报告 ──
    print("\n[Step 4] 生成报告...")
    text_report = generate_text_report(reports)

    date_str = datetime.now().strftime("%Y%m%d")
    report_path = BASE_DIR / REPORTS_DIR / f"global_property_{date_str}.md"
    report_path.write_text(text_report, encoding="utf-8")
    print(f"  ✓ 报告已保存: {report_path}")

    # 打印摘要
    print("\n" + "=" * 50)
    print("📊 城市排名摘要（调整后收益，CNY 视角）")
    print("=" * 50)
    for r in reports:
        city = r["city"]
        adj = r.get("adjusted_return_pct")
        interp = r.get("interpretation", "数据不足")
        if adj is not None:
            print(f"  {city:15s}  {adj:+6.1f}%  {interp}")
        else:
            print(f"  {city:15s}  {'N/A':>7s}  数据不足")

    print(f"\n完整报告: {report_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
