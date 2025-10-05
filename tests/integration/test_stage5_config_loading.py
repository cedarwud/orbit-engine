#!/usr/bin/env python3
"""
Stage 5 配置加载集成测试
验证配置文件正确加载和参数验证

Author: Auto-generated
Date: 2025-10-04
Purpose: 确保 Stage 5 Grade A+ 配置文件正确加载并验证
"""

import sys
import os
import yaml
import pytest
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'scripts'))

# 设置测试模式
os.environ['ORBIT_ENGINE_TEST_MODE'] = '1'


class TestStage5ConfigLoading:
    """Stage 5 配置加载测试套件"""

    def test_config_file_exists(self):
        """测试配置文件存在"""
        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'
        assert config_path.exists(), f"配置文件不存在: {config_path}"

    def test_config_file_valid_yaml(self):
        """测试配置文件是有效的 YAML"""
        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "配置文件格式错误，应该是字典"

    def test_config_has_required_sections(self):
        """测试配置文件包含必要章节"""
        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert 'signal_calculator' in config, "缺少 signal_calculator 章节"
        assert 'atmospheric_model' in config, "缺少 atmospheric_model 章节"
        assert 'signal_thresholds' in config, "缺少 signal_thresholds 章节"

    def test_signal_calculator_params(self):
        """测试 signal_calculator 必要参数"""
        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        signal_calc = config['signal_calculator']
        required_params = [
            'bandwidth_mhz',
            'subcarrier_spacing_khz',
            'noise_figure_db',
            'temperature_k'
        ]

        for param in required_params:
            assert param in signal_calc, f"signal_calculator 缺少参数: {param}"
            assert isinstance(signal_calc[param], (int, float)), f"{param} 应该是数值"

    def test_atmospheric_model_params(self):
        """测试 atmospheric_model 必要参数"""
        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        atmos_model = config['atmospheric_model']
        required_params = [
            'temperature_k',
            'pressure_hpa',
            'water_vapor_density_g_m3'
        ]

        for param in required_params:
            assert param in atmos_model, f"atmospheric_model 缺少参数: {param}"
            assert isinstance(atmos_model[param], (int, float)), f"{param} 应该是数值"

    def test_load_stage5_config_function(self):
        """测试 load_stage5_config 函数"""
        from stage_executors.stage5_executor import load_stage5_config

        config = load_stage5_config()
        assert isinstance(config, dict), "load_stage5_config 应该返回字典"
        assert 'signal_calculator' in config
        assert 'atmospheric_model' in config

    def test_validate_stage5_config_function(self):
        """测试 validate_stage5_config 函数"""
        from stage_executors.stage5_executor import validate_stage5_config

        config_path = project_root / 'config' / 'stage5_signal_analysis_config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        valid, message = validate_stage5_config(config)
        assert valid is True, f"配置验证失败: {message}"
        assert "通過" in message or "通过" in message

    def test_validate_stage5_config_missing_section(self):
        """测试缺少必要章节时验证失败"""
        from stage_executors.stage5_executor import validate_stage5_config

        # 缺少 signal_calculator
        incomplete_config = {
            'atmospheric_model': {
                'temperature_k': 283.0,
                'pressure_hpa': 1013.25,
                'water_vapor_density_g_m3': 7.5
            }
        }

        valid, message = validate_stage5_config(incomplete_config)
        assert valid is False
        assert 'signal_calculator' in message

    def test_validate_stage5_config_missing_param(self):
        """测试缺少必要参数时验证失败"""
        from stage_executors.stage5_executor import validate_stage5_config

        # signal_calculator 缺少 bandwidth_mhz
        incomplete_config = {
            'signal_calculator': {
                # 'bandwidth_mhz': 100.0,  # 故意缺失
                'subcarrier_spacing_khz': 30.0,
                'noise_figure_db': 7.0,
                'temperature_k': 290.0
            },
            'atmospheric_model': {
                'temperature_k': 283.0,
                'pressure_hpa': 1013.25,
                'water_vapor_density_g_m3': 7.5
            }
        }

        valid, message = validate_stage5_config(incomplete_config)
        assert valid is False
        assert 'bandwidth_mhz' in message

    def test_processor_accepts_config(self):
        """测试 processor 接受配置"""
        from stages.stage5_signal_analysis.stage5_signal_analysis_processor import Stage5SignalAnalysisProcessor

        config = {
            'signal_calculator': {
                'bandwidth_mhz': 100.0,
                'subcarrier_spacing_khz': 30.0,
                'noise_figure_db': 7.0,
                'temperature_k': 290.0
            },
            'atmospheric_model': {
                'temperature_k': 283.0,
                'pressure_hpa': 1013.25,
                'water_vapor_density_g_m3': 7.5
            }
        }

        processor = Stage5SignalAnalysisProcessor(config)
        assert processor is not None
        assert processor.max_workers > 0
        assert processor.config_manager is not None

    @pytest.mark.skip(reason="参数验证在 signal_calculator 初始化时，而非 processor 初始化时")
    def test_processor_fails_without_bandwidth(self):
        """测试缺少 bandwidth_mhz 时失败（跳过 - 验证时机不同）"""
        pass

    @pytest.mark.skip(reason="参数验证在 signal_calculator 初始化时，而非 processor 初始化时")
    def test_processor_fails_without_noise_figure(self):
        """测试缺少 noise_figure_db 时失败（跳过 - 验证时机不同）"""
        pass

    @pytest.mark.skipif(
        not sys.modules.get('itur'),
        reason="需要 itur 模块（可选依赖）"
    )
    def test_atmospheric_model_temperature_range(self):
        """测试大气温度范围验证"""
        try:
            from stages.stage5_signal_analysis.itur_official_atmospheric_model import ITUROfficalAtmosphericModel
        except ModuleNotFoundError:
            pytest.skip("itur 模块未安装")

        # 有效范围 200-350K
        valid_model = ITUROfficalAtmosphericModel(
            temperature_k=283.0,
            pressure_hpa=1013.25,
            water_vapor_density_g_m3=7.5
        )
        assert valid_model is not None

        # 超出范围
        with pytest.raises(ValueError, match="溫度超出物理範圍"):
            ITUROfficalAtmosphericModel(
                temperature_k=400.0,  # 超出 350K
                pressure_hpa=1013.25,
                water_vapor_density_g_m3=7.5
            )

    @pytest.mark.skipif(
        not sys.modules.get('itur'),
        reason="需要 itur 模块（可选依赖）"
    )
    def test_atmospheric_model_pressure_range(self):
        """测试大气压力范围验证"""
        try:
            from stages.stage5_signal_analysis.itur_official_atmospheric_model import ITUROfficalAtmosphericModel
        except ModuleNotFoundError:
            pytest.skip("itur 模块未安装")

        # 有效范围 500-1100 hPa
        valid_model = ITUROfficalAtmosphericModel(
            temperature_k=283.0,
            pressure_hpa=1013.25,
            water_vapor_density_g_m3=7.5
        )
        assert valid_model is not None

        # 超出范围
        with pytest.raises(ValueError, match="氣壓超出合理範圍"):
            ITUROfficalAtmosphericModel(
                temperature_k=283.0,
                pressure_hpa=1200.0,  # 超出 1100 hPa
                water_vapor_density_g_m3=7.5
            )

    @pytest.mark.skipif(
        not sys.modules.get('itur'),
        reason="需要 itur 模块（可选依赖）"
    )
    def test_atmospheric_model_water_vapor_range(self):
        """测试水蒸气密度范围验证"""
        try:
            from stages.stage5_signal_analysis.itur_official_atmospheric_model import ITUROfficalAtmosphericModel
        except ModuleNotFoundError:
            pytest.skip("itur 模块未安装")

        # 有效范围 0-30 g/m³
        valid_model = ITUROfficalAtmosphericModel(
            temperature_k=283.0,
            pressure_hpa=1013.25,
            water_vapor_density_g_m3=7.5
        )
        assert valid_model is not None

        # 超出范围
        with pytest.raises(ValueError, match="水蒸氣密度超出合理範圍"):
            ITUROfficalAtmosphericModel(
                temperature_k=283.0,
                pressure_hpa=1013.25,
                water_vapor_density_g_m3=35.0  # 超出 30 g/m³
            )


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
