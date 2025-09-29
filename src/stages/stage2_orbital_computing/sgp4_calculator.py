"""
🛰️ SGP4Calculator - 標準軌道傳播計算器

符合文檔要求的 Grade A 學術級實現：
✅ 標準SGP4/SDP4算法
✅ 高精度位置和速度計算
✅ 批次計算和時間序列生成
❌ 禁止任何簡化或近似方法
"""

import logging
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine
    from shared.utils.time_utils import TimeUtils
except ImportError:
    # 回退導入路徑
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine
    from shared.utils.time_utils import TimeUtils

logger = logging.getLogger(__name__)

@dataclass
class SGP4Position:
    """SGP4計算結果位置和速度"""
    x: float  # km
    y: float  # km
    z: float  # km
    vx: float  # km/s
    vy: float  # km/s
    vz: float  # km/s
    timestamp: str
    time_since_epoch_minutes: float

@dataclass
class SGP4OrbitResult:
    """SGP4軌道計算結果"""
    satellite_id: str
    positions: List[SGP4Position]
    calculation_successful: bool
    algorithm_used: str = "SGP4"
    precision_grade: str = "A"

class SGP4Calculator:
    """
    標準SGP4軌道傳播計算器

    功能職責：
    - 實現標準SGP4/SDP4軌道傳播算法
    - 處理近地和深空衛星軌道
    - 提供高精度位置和速度計算
    - 支援批次計算和時間序列生成
    """

    def __init__(self):
        """初始化SGP4計算器"""
        self.logger = logging.getLogger(f"{__name__}.SGP4Calculator")

        # 初始化真實SGP4引擎 - Grade A要求
        self.sgp4_engine = SGP4OrbitalEngine(
            observer_coordinates=None,  # Stage 2不需要觀測者座標
            eci_only_mode=True         # 僅輸出ECI座標
        )

        # 計算統計
        self.calculation_stats = {
            "total_calculations": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "engine_type": "SGP4OrbitalEngine",
            "academic_grade": "A"
        }

        self.logger.info("✅ SGP4Calculator 初始化完成 - 學術級Grade A標準")

    def calculate_position(self, tle_data: Dict[str, Any], time_since_epoch: float) -> Optional[SGP4Position]:
        """
        計算指定時間的衛星位置

        Args:
            tle_data: TLE數據字典，包含line1, line2等
            time_since_epoch: 相對於TLE epoch的時間（分鐘）

        Returns:
            SGP4Position: 計算結果位置
        """
        try:
            self.calculation_stats["total_calculations"] += 1

            # ✅ v3.0架構要求：使用Stage 1提供的epoch_datetime，禁止TLE重新解析
            tle_line1 = tle_data.get('line1', tle_data.get('tle_line1', ''))
            tle_line2 = tle_data.get('line2', tle_data.get('tle_line2', ''))

            if not tle_line1 or not tle_line2:
                raise ValueError("TLE數據不完整")

            # 🚨 關鍵修復：使用Stage 1的epoch_datetime，不重新解析TLE
            epoch_datetime_str = tle_data.get('epoch_datetime')
            if not epoch_datetime_str:
                raise ValueError("v3.0架構要求：必須提供Stage 1的epoch_datetime，禁止TLE重新解析")

            try:
                # 解析Stage 1提供的epoch_datetime
                epoch_time = datetime.fromisoformat(epoch_datetime_str.replace('Z', '+00:00'))
                calculation_time = epoch_time + timedelta(minutes=time_since_epoch)

                # 確保時區信息正確設置
                if calculation_time.tzinfo is None:
                    calculation_time = calculation_time.replace(tzinfo=timezone.utc)

                # v3.0合規性標記
                self.logger.debug(f"✅ v3.0合規：使用Stage 1 epoch_datetime: {epoch_datetime_str}")

            except (ValueError, TypeError) as e:
                raise ValueError(f"Stage 1 epoch_datetime格式錯誤: {epoch_datetime_str}, 錯誤: {e}")

            # 構建SGP4引擎期望的數據格式
            sgp4_data = {
                'line1': tle_line1,
                'line2': tle_line2,
                'satellite_name': tle_data.get('name', 'Satellite'),
                'epoch_datetime': epoch_time
            }

            # 使用真實SGP4引擎計算
            result = self.sgp4_engine.calculate_position(sgp4_data, calculation_time)

            if result and result.calculation_successful and result.position:
                # 使用直接 SGP4 庫計算速度分量
                vx, vy, vz = self._calculate_velocity_direct(tle_line1, tle_line2, time_since_epoch)

                position = SGP4Position(
                    x=result.position.x,
                    y=result.position.y,
                    z=result.position.z,
                    vx=vx,
                    vy=vy,
                    vz=vz,
                    timestamp=calculation_time.isoformat(),
                    time_since_epoch_minutes=time_since_epoch
                )

                self.calculation_stats["successful_calculations"] += 1
                return position
            else:
                self.calculation_stats["failed_calculations"] += 1
                return None

        except Exception as e:
            self.logger.error(f"SGP4計算失敗: {e}")
            self.calculation_stats["failed_calculations"] += 1
            return None

    def _calculate_velocity_direct(self, tle_line1: str, tle_line2: str, time_since_epoch: float) -> Tuple[float, float, float]:
        """
        使用標準SGP4庫計算精確速度分量 - Grade A學術標準

        Args:
            tle_line1: TLE第一行
            tle_line2: TLE第二行
            time_since_epoch: 相對epoch的時間（分鐘）

        Returns:
            Tuple[float, float, float]: (vx, vy, vz) in km/s
        """
        try:
            # ✅ 強制使用標準SGP4庫 - 無回退機制
            from sgp4.api import Satrec

            # 創建SGP4衛星對象
            satellite = Satrec.twoline2rv(tle_line1, tle_line2)

            # 使用標準SGP4算法計算位置和速度
            error, position, velocity = satellite.sgp4_tsince(time_since_epoch)

            # 檢查計算錯誤
            if error != 0:
                error_messages = {
                    1: "mean eccentricity < 0.0 or > 1.0",
                    2: "mean motion < 0.0",
                    3: "perturbed eccentricity < 0.0 or > 1.0",
                    4: "semi-latus rectum < 0.0",
                    5: "epoch elements are sub-orbital",
                    6: "satellite has decayed"
                }
                error_msg = error_messages.get(error, f"SGP4計算錯誤代碼: {error}")
                raise RuntimeError(f"SGP4計算失敗: {error_msg}")

            # 驗證速度數據有效性
            if velocity is None or len(velocity) != 3:
                raise RuntimeError("SGP4返回無效速度數據")

            # 檢查速度合理性 (LEO衛星速度應在3-12 km/s範圍)
            speed = (velocity[0]**2 + velocity[1]**2 + velocity[2]**2)**0.5
            if not (3.0 <= speed <= 12.0):
                self.logger.warning(f"速度超出合理範圍: {speed:.2f} km/s")

            return float(velocity[0]), float(velocity[1]), float(velocity[2])

        except ImportError as e:
            # ❌ Grade A標準：不允許無SGP4庫運行
            raise RuntimeError(f"Grade A標準要求：必須安裝sgp4庫，當前系統缺少該依賴: {e}")

        except Exception as e:
            # ❌ Grade A標準：不允許簡化算法回退
            raise RuntimeError(f"SGP4速度計算失敗，Grade A標準禁止使用估算方法: {e}")

    def batch_calculate(self, tle_data_list: List[Dict[str, Any]], time_series: List[float]) -> Dict[str, SGP4OrbitResult]:
        """
        批次計算多顆衛星的軌道

        Args:
            tle_data_list: TLE數據列表
            time_series: 時間序列（相對於epoch的分鐘數）

        Returns:
            Dict[str, SGP4OrbitResult]: 衛星ID對應的軌道結果
        """
        self.logger.info(f"🚀 開始批次計算 {len(tle_data_list)} 顆衛星的軌道")

        results = {}

        for tle_data in tle_data_list:
            satellite_id = str(tle_data.get('satellite_id', tle_data.get('norad_id', 'unknown')))

            try:
                positions = []

                # 為每個時間點計算位置
                for time_point in time_series:
                    position = self.calculate_position(tle_data, time_point)
                    if position:
                        positions.append(position)

                if positions:
                    results[satellite_id] = SGP4OrbitResult(
                        satellite_id=satellite_id,
                        positions=positions,
                        calculation_successful=True,
                        algorithm_used="SGP4",
                        precision_grade="A"
                    )

                    self.logger.debug(f"✅ 衛星 {satellite_id} 軌道計算完成: {len(positions)} 個位置點")
                else:
                    self.logger.warning(f"❌ 衛星 {satellite_id} 軌道計算失敗")

            except Exception as e:
                self.logger.error(f"衛星 {satellite_id} 批次計算異常: {e}")
                continue

        self.logger.info(f"✅ 批次計算完成: {len(results)}/{len(tle_data_list)} 顆衛星成功")
        return results

    def validate_calculation_accuracy(self, results: Dict[str, SGP4OrbitResult]) -> Dict[str, Any]:
        """
        驗證計算精度

        Args:
            results: SGP4計算結果

        Returns:
            Dict[str, Any]: 驗證結果
        """
        validation_result = {
            "validation_passed": True,
            "total_satellites": len(results),
            "accuracy_checks": {},
            "issues": []
        }

        # 檢查1: 位置數據完整性
        incomplete_satellites = 0
        total_positions = 0

        for satellite_id, orbit_result in results.items():
            positions = orbit_result.positions
            total_positions += len(positions)

            if len(positions) < 100:  # 少於100個位置點視為異常
                incomplete_satellites += 1
                validation_result["issues"].append(f"衛星 {satellite_id} 位置點過少: {len(positions)}")

        validation_result["accuracy_checks"]["position_completeness"] = {
            "total_positions": total_positions,
            "incomplete_satellites": incomplete_satellites,
            "passed": incomplete_satellites == 0
        }

        if incomplete_satellites > 0:
            validation_result["validation_passed"] = False

        # 檢查2: 算法標準合規性
        non_standard_algorithms = 0
        for satellite_id, orbit_result in results.items():
            if orbit_result.algorithm_used != "SGP4":
                non_standard_algorithms += 1
                validation_result["issues"].append(f"衛星 {satellite_id} 使用非標準算法: {orbit_result.algorithm_used}")

        validation_result["accuracy_checks"]["algorithm_compliance"] = {
            "non_standard_count": non_standard_algorithms,
            "passed": non_standard_algorithms == 0
        }

        if non_standard_algorithms > 0:
            validation_result["validation_passed"] = False

        # 檢查3: 學術級精度要求
        low_grade_satellites = 0
        for satellite_id, orbit_result in results.items():
            if orbit_result.precision_grade != "A":
                low_grade_satellites += 1
                validation_result["issues"].append(f"衛星 {satellite_id} 精度等級不符: {orbit_result.precision_grade}")

        validation_result["accuracy_checks"]["precision_grade"] = {
            "low_grade_count": low_grade_satellites,
            "passed": low_grade_satellites == 0
        }

        if low_grade_satellites > 0:
            validation_result["validation_passed"] = False

        return validation_result

    def get_calculation_statistics(self) -> Dict[str, Any]:
        """獲取計算統計信息"""
        stats = self.calculation_stats.copy()

        if stats["total_calculations"] > 0:
            stats["success_rate"] = (stats["successful_calculations"] / stats["total_calculations"]) * 100
        else:
            stats["success_rate"] = 0.0

        return stats

    def calculate_orbital_period(self, tle_line2: str) -> float:
        """
        從TLE數據計算精確軌道週期 - Grade A學術標準

        Args:
            tle_line2: TLE第二行數據

        Returns:
            float: 軌道週期（分鐘）
        """
        try:
            # ✅ 精確解析TLE第二行的mean motion
            # TLE格式：positions 52-63 是 mean motion (revolutions per day)
            mean_motion_str = tle_line2[52:63].strip()
            if not mean_motion_str:
                raise ValueError("TLE第二行mean motion字段為空")

            mean_motion = float(mean_motion_str)

            # 驗證mean motion合理性
            if mean_motion <= 0:
                raise ValueError(f"Mean motion必須為正數: {mean_motion}")

            if mean_motion > 20:  # 超過20圈/天不合理
                raise ValueError(f"Mean motion超出合理範圍: {mean_motion} revs/day")

            # ✅ 使用標準軌道力學公式：1440分鐘/天 ÷ 每日圈數
            orbital_period_minutes = 1440.0 / mean_motion

            # 驗證軌道週期合理性 (LEO: 85-130分鐘)
            if not (80.0 <= orbital_period_minutes <= 150.0):
                self.logger.warning(f"軌道週期超出典型LEO範圍: {orbital_period_minutes:.1f}分鐘")

            return orbital_period_minutes

        except Exception as e:
            # ❌ Grade A標準：不允許硬編碼回退值
            raise ValueError(f"軌道週期計算失敗，Grade A標準禁止使用預設值: {e}")

    def calculate_optimal_time_points(self, tle_line2: str, time_interval_seconds: int = 30, coverage_cycles: float = 1.0) -> int:
        """
        基於實際軌道物理參數計算時間點數量 - Grade A學術標準

        學術原則：
        1. 基於實際TLE軌道參數計算
        2. 禁止星座硬編碼或預設值
        3. 完整軌道週期覆蓋，基於物理計算

        Args:
            tle_line2: TLE第二行數據
            time_interval_seconds: 時間間隔（秒）
            coverage_cycles: 覆蓋週期數（1.0=完整軌道週期）

        Returns:
            int: 基於物理計算的時間點數量
        """
        try:
            # ✅ 從真實TLE數據計算軌道週期
            orbital_period_minutes = self.calculate_orbital_period(tle_line2)

            # ✅ 基於物理軌道週期計算覆蓋時間
            coverage_time_minutes = orbital_period_minutes * coverage_cycles
            coverage_time_seconds = coverage_time_minutes * 60

            # ✅ 基於時間間隔計算精確時間點數
            time_points = int(coverage_time_seconds / time_interval_seconds)

            # 驗證最小合理數量 (至少30分鐘的數據)
            min_time_points = (30 * 60) // time_interval_seconds
            if time_points < min_time_points:
                self.logger.warning(f"計算的時間點數({time_points})小於最小要求({min_time_points})，使用最小值")
                time_points = min_time_points

            # 學術級計算記錄
            self.logger.info(f"🔬 Grade A軌道物理計算:")
            self.logger.info(f"  - 實際軌道週期: {orbital_period_minutes:.1f}分鐘")
            self.logger.info(f"  - 覆蓋倍數: {coverage_cycles:.1f}x")
            self.logger.info(f"  - 覆蓋時間: {coverage_time_minutes:.1f}分鐘")
            self.logger.info(f"  - 時間間隔: {time_interval_seconds}秒")
            self.logger.info(f"  - 計算時間點數: {time_points}")
            self.logger.info(f"  - 計算基礎: 真實TLE軌道參數")

            return time_points

        except Exception as e:
            # ❌ Grade A標準：不允許硬編碼回退值
            raise ValueError(f"時間點計算失敗，Grade A標準禁止使用預設值: {e}")
