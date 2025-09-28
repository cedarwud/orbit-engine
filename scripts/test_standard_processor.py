#!/usr/bin/env python3
"""
測試原本的標準處理器（CPU版本）
檢查它是否能產生合理的篩選結果
"""

import os
import sys
import json
import time
import yaml
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    """測試標準處理器"""
    print("🔬 測試標準處理器（CPU版本）")

    # 載入配置
    config_path = "config/stage2_orbital_computing.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        stage2_config = config.get('stage2_orbital_computing', {})
        print(f"📊 配置載入成功:")
        print(f"   Starlink仰角: {stage2_config.get('constellation_elevation_thresholds', {}).get('starlink', 'N/A')}°")
        print(f"   OneWeb仰角: {stage2_config.get('constellation_elevation_thresholds', {}).get('oneweb', 'N/A')}°")
    except Exception as e:
        print(f"⚠️ 配置載入失敗: {e}")
        stage2_config = {}

    # 載入階段一輸出
    stage1_output_path = "data/outputs/stage1/tle_data_loading_output_20250927_090128.json"
    print(f"📂 載入階段一輸出: {stage1_output_path}")

    with open(stage1_output_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    print(f"✅ 階段一數據載入完成: {len(input_data.get('satellites', []))} 顆衛星")

    # 檢查前幾顆衛星的星座信息
    satellites = input_data.get('satellites', [])
    print(f"\n🔍 前5顆衛星的星座信息:")
    for i, sat in enumerate(satellites[:5]):
        constellation = sat.get('constellation', 'unknown')
        name = sat.get('name', 'unknown')
        print(f"   {i+1}. {name} -> {constellation}")

    # 統計星座分佈
    constellation_counts = {}
    for sat in satellites:
        constellation = sat.get('constellation', 'unknown')
        constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1

    print(f"\n📊 星座分佈:")
    for constellation, count in constellation_counts.items():
        print(f"   {constellation}: {count} 顆")

    # 初始化並測試標準處理器
    try:
        print(f"\n⚡ 初始化標準處理器...")
        from stages.stage2_orbital_computing.stage2_orbital_computing_processor import Stage2OrbitalComputingProcessor
        processor = Stage2OrbitalComputingProcessor(config=stage2_config)
        print(f"✅ 標準處理器初始化完成")

        # 執行處理
        print(f"🚀 開始執行標準處理器...")
        start_time = time.time()
        result = processor.execute(input_data)
        execution_time = time.time() - start_time

        # 提取結果統計
        if hasattr(result, 'data') and isinstance(result.data, dict):
            satellites = result.data.get('satellites', [])
            metadata = result.data.get('metadata', {})
        else:
            satellites = result.get('satellites', []) if isinstance(result, dict) else []
            metadata = result.get('metadata', {}) if isinstance(result, dict) else {}

        # 統計結果
        total_satellites = len(satellites)
        visible_count = metadata.get('visible_satellites_count', 0)
        feasible_count = metadata.get('feasible_satellites_count', 0)

        visibility_rate = (visible_count / 8995 * 100) if 8995 > 0 else 0
        feasibility_rate = (feasible_count / 8995 * 100) if 8995 > 0 else 0

        print(f"\n📊 標準處理器結果:")
        print(f"   執行時間: {execution_time:.2f} 秒")
        print(f"   輸入衛星: 8995 顆")
        print(f"   輸出衛星: {total_satellites} 顆")
        print(f"   可見衛星: {visible_count} 顆 ({visibility_rate:.1f}%)")
        print(f"   可行衛星: {feasible_count} 顆 ({feasibility_rate:.1f}%)")

        print(f"\n✅ 標準處理器測試完成")

        # 這個結果是否合理？
        print(f"\n🤔 結果分析:")
        if feasibility_rate < 30:
            print(f"   ✅ 可行率 {feasibility_rate:.1f}% 看起來合理（預期 15-25%）")
        else:
            print(f"   ❌ 可行率 {feasibility_rate:.1f}% 看起來太高")

        if visibility_rate < 40:
            print(f"   ✅ 可見率 {visibility_rate:.1f}% 看起來合理（預期 20-35%）")
        else:
            print(f"   ❌ 可見率 {visibility_rate:.1f}% 看起來太高")

    except Exception as e:
        print(f"❌ 標準處理器測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()