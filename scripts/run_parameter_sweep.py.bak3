#!/usr/bin/env python3
"""
參數掃描自動化腳本
Parameter Sweep Automation for Stage 6 Research Optimization

學術目的:
1. 系統性探索參數空間（Systematic Parameter Space Exploration）
2. 敏感度分析（Sensitivity Analysis）
3. 最優參數選擇（Optimal Parameter Selection）
4. 學術論證支撐（Academic Justification Support）

使用方式:
    python scripts/run_parameter_sweep.py --constellation starlink --params d2
    python scripts/run_parameter_sweep.py --constellation oneweb --params d2,a3
    python scripts/run_parameter_sweep.py --full  # 完整掃描（警告: 512 次執行）

輸出:
    results/parameter_sweep_{timestamp}/
    ├── sweep_results.json          # 所有掃描結果
    ├── sensitivity_analysis.json   # 敏感度分析
    ├── optimal_parameters.json     # 推薦最優參數
    └── visualization/
        ├── d2_threshold_heatmap.png
        ├── event_count_vs_threshold.png
        └── pareto_frontier.png
"""

import argparse
import itertools
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple
import yaml

# 添加項目根目錄到路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParameterSweeper:
    """參數掃描執行器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stage6_config_path = PROJECT_ROOT / "config/stage6_research_optimization_config.yaml"
        self.stage6_config_backup = None
        self.sweep_results = []

    def load_sweep_config(self) -> Dict[str, Any]:
        """載入參數掃描配置"""
        with open(self.stage6_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('parameter_sweep', {})

    def backup_config(self):
        """備份原始配置"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.output_dir / f"stage6_config_backup_{timestamp}.yaml"
        shutil.copy(self.stage6_config_path, backup_path)
        self.stage6_config_backup = backup_path
        logger.info(f"✅ 配置已備份: {backup_path}")

    def restore_config(self):
        """恢復原始配置"""
        if self.stage6_config_backup and self.stage6_config_backup.exists():
            shutil.copy(self.stage6_config_backup, self.stage6_config_path)
            logger.info(f"✅ 配置已恢復: {self.stage6_config_path}")

    def update_stage6_config(self, params: Dict[str, float]):
        """更新 Stage 6 配置文件"""
        with open(self.stage6_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 更新門檻值
        thresholds = config.get('handover_thresholds', {})

        # 更新星座特定參數
        for constellation in ['starlink', 'oneweb']:
            if constellation not in thresholds:
                thresholds[constellation] = {}

            for key, value in params.items():
                if key.startswith(f'{constellation}_'):
                    param_name = key.replace(f'{constellation}_', '')
                    thresholds[constellation][param_name] = value

        # 更新通用參數
        for key, value in params.items():
            if not any(key.startswith(f'{c}_') for c in ['starlink', 'oneweb']):
                thresholds[key] = value

        config['handover_thresholds'] = thresholds

        # 保存更新後的配置
        with open(self.stage6_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    def run_stage6(self) -> Dict[str, Any]:
        """執行 Stage 6（只重跑 Stage 6）"""
        logger.info("🔄 執行 Stage 6...")

        # 使用虛擬環境的 python
        venv_python = PROJECT_ROOT / "venv/bin/python"
        if not venv_python.exists():
            venv_python = sys.executable  # 回退到系統 python

        cmd = [
            str(venv_python),
            str(PROJECT_ROOT / "scripts/run_six_stages_with_validation.py"),
            "--stage", "6"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode != 0:
            logger.error(f"❌ Stage 6 執行失敗:\n{result.stderr}")
            return {'success': False, 'error': result.stderr}

        # 讀取 Stage 6 驗證快照
        validation_snapshot = PROJECT_ROOT / "data/validation_snapshots/stage6_validation.json"

        if not validation_snapshot.exists():
            logger.error(f"❌ Stage 6 驗證快照不存在: {validation_snapshot}")
            return {'success': False, 'error': 'Validation snapshot not found'}

        with open(validation_snapshot, 'r', encoding='utf-8') as f:
            stage6_data = json.load(f)

        # 提取 GPP 事件摘要
        gpp_events = stage6_data.get('gpp_events', {})
        event_summary = gpp_events.get('event_summary', {})

        return {
            'success': True,
            'output_file': str(validation_snapshot),
            'event_summary': event_summary,
            'total_events': event_summary.get('a3_count', 0) +
                          event_summary.get('a4_count', 0) +
                          event_summary.get('a5_count', 0) +
                          event_summary.get('d2_count', 0)
        }

    def extract_metrics(self, stage6_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標"""
        event_summary = stage6_result.get('event_summary', {})

        return {
            'a3_count': event_summary.get('a3_count', 0),
            'a4_count': event_summary.get('a4_count', 0),
            'a5_count': event_summary.get('a5_count', 0),
            'd2_count': event_summary.get('d2_count', 0),
            'total_events': event_summary.get('total_events', 0),
            'time_points_processed': event_summary.get('time_points_processed', 0),
            'participating_satellites': event_summary.get('participating_satellites', 0),
        }

    def run_sweep(
        self,
        constellation: str,
        param_names: List[str],
        sweep_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """執行參數掃描"""
        sweep_ranges = sweep_config.get('sweep_ranges', {}).get(constellation, {})

        # 構建參數組合
        param_values = {}
        for param in param_names:
            if param in sweep_ranges:
                param_values[param] = sweep_ranges[param]
            else:
                logger.warning(f"⚠️ 參數 {param} 不在掃描範圍中，跳過")

        if not param_values:
            logger.error("❌ 沒有有效的參數可供掃描")
            return []

        # 生成所有參數組合
        param_combinations = list(itertools.product(*param_values.values()))
        total_combinations = len(param_combinations)

        logger.info(f"📊 參數掃描配置:")
        logger.info(f"   星座: {constellation}")
        logger.info(f"   參數: {list(param_values.keys())}")
        logger.info(f"   總組合數: {total_combinations}")

        results = []

        for i, combination in enumerate(param_combinations, 1):
            # 構建參數字典
            params = {
                f"{constellation}_{name}": value
                for name, value in zip(param_values.keys(), combination)
            }

            logger.info(f"\n{'='*60}")
            logger.info(f"📍 掃描進度: {i}/{total_combinations}")
            logger.info(f"   參數組合: {params}")

            # 更新配置
            self.update_stage6_config(params)

            # 執行 Stage 6
            stage6_result = self.run_stage6()

            if stage6_result['success']:
                metrics = self.extract_metrics(stage6_result)

                result_entry = {
                    'iteration': i,
                    'parameters': params,
                    'metrics': metrics,
                    'output_file': stage6_result['output_file']
                }
                results.append(result_entry)

                logger.info(f"✅ 執行成功:")
                logger.info(f"   總事件: {metrics['total_events']}")
                logger.info(f"   D2: {metrics['d2_count']}, A3: {metrics['a3_count']}, "
                           f"A4: {metrics['a4_count']}, A5: {metrics['a5_count']}")
            else:
                logger.error(f"❌ 執行失敗: {stage6_result.get('error', 'Unknown error')}")

        return results

    def analyze_sensitivity(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """敏感度分析"""
        logger.info("\n📈 執行敏感度分析...")

        # 提取參數名稱
        if not results:
            return {}

        param_names = list(results[0]['parameters'].keys())

        sensitivity = {}

        for param in param_names:
            # 計算參數變化對事件數的影響
            param_values = [r['parameters'][param] for r in results]
            event_counts = [r['metrics']['total_events'] for r in results]

            # 計算相關係數（簡化版）
            if len(set(param_values)) > 1:
                # 正規化
                param_range = max(param_values) - min(param_values)
                event_range = max(event_counts) - min(event_counts) if max(event_counts) > 0 else 1

                # 簡化敏感度: Δevent / Δparam
                sensitivity[param] = {
                    'param_range': param_range,
                    'event_range': event_range,
                    'sensitivity': event_range / param_range if param_range > 0 else 0,
                    'min_events': min(event_counts),
                    'max_events': max(event_counts),
                    'param_values': sorted(set(param_values)),
                }

        return sensitivity

    def find_optimal_parameters(
        self,
        results: List[Dict[str, Any]],
        criteria: str = 'max_events'
    ) -> Dict[str, Any]:
        """尋找最優參數"""
        logger.info(f"\n🎯 尋找最優參數（標準: {criteria}）...")

        if criteria == 'max_events':
            optimal = max(results, key=lambda r: r['metrics']['total_events'])
        elif criteria == 'max_d2':
            optimal = max(results, key=lambda r: r['metrics']['d2_count'])
        elif criteria == 'balanced':
            # 平衡策略: D2 + A3 事件數
            optimal = max(results, key=lambda r:
                         r['metrics']['d2_count'] + r['metrics']['a3_count'])
        else:
            optimal = results[0]

        return {
            'optimal_parameters': optimal['parameters'],
            'optimal_metrics': optimal['metrics'],
            'criteria': criteria,
            'performance_gain': {
                'vs_min': optimal['metrics']['total_events'] -
                         min(r['metrics']['total_events'] for r in results),
                'vs_avg': optimal['metrics']['total_events'] -
                         sum(r['metrics']['total_events'] for r in results) / len(results)
            }
        }

    def save_results(self, results: List[Dict[str, Any]],
                    sensitivity: Dict[str, Any],
                    optimal: Dict[str, Any]):
        """保存結果"""
        # 保存掃描結果
        with open(self.output_dir / "sweep_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # 保存敏感度分析
        with open(self.output_dir / "sensitivity_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(sensitivity, f, indent=2, ensure_ascii=False)

        # 保存最優參數
        with open(self.output_dir / "optimal_parameters.json", 'w', encoding='utf-8') as f:
            json.dump(optimal, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✅ 結果已保存到: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="參數掃描自動化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--constellation',
        choices=['starlink', 'oneweb', 'both'],
        default='starlink',
        help='目標星座'
    )

    parser.add_argument(
        '--params',
        default='d2',
        help='參數類型: d2, a3, a4, 或組合 (如 d2,a3)'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='完整掃描（包含所有參數組合，警告: 512 次執行）'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='輸出目錄（預設: results/parameter_sweep_{timestamp}）'
    )

    args = parser.parse_args()

    # 創建輸出目錄
    if args.output:
        output_dir = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = PROJECT_ROOT / f"results/parameter_sweep_{timestamp}"

    # 初始化掃描器
    sweeper = ParameterSweeper(output_dir)
    sweeper.backup_config()

    try:
        # 載入掃描配置
        sweep_config = sweeper.load_sweep_config()

        # 解析參數類型
        param_map = {
            'd2': ['d2_threshold1_km', 'd2_threshold2_km'],
            'a3': ['a3_offset_db'],
            'a4': ['a4_threshold_dbm'],
        }

        param_types = args.params.split(',')
        param_names = []
        for ptype in param_types:
            if ptype in param_map:
                param_names.extend(param_map[ptype])

        # 執行掃描
        if args.constellation in ['starlink', 'oneweb']:
            results = sweeper.run_sweep(args.constellation, param_names, sweep_config)
        else:  # both
            results_starlink = sweeper.run_sweep('starlink', param_names, sweep_config)
            results_oneweb = sweeper.run_sweep('oneweb', param_names, sweep_config)
            results = results_starlink + results_oneweb

        # 分析結果
        sensitivity = sweeper.analyze_sensitivity(results)
        optimal = sweeper.find_optimal_parameters(results, criteria='max_events')

        # 保存結果
        sweeper.save_results(results, sensitivity, optimal)

        # 輸出摘要
        logger.info("\n" + "="*60)
        logger.info("📊 參數掃描完成摘要")
        logger.info("="*60)
        logger.info(f"總掃描次數: {len(results)}")
        logger.info(f"最優參數: {optimal['optimal_parameters']}")
        logger.info(f"最優性能: {optimal['optimal_metrics']['total_events']} 事件")
        logger.info(f"性能提升: +{optimal['performance_gain']['vs_avg']:.1f} 事件 (相對平均)")
        logger.info(f"\n詳細結果: {output_dir}")

    finally:
        # 恢復原始配置
        sweeper.restore_config()


if __name__ == "__main__":
    main()
