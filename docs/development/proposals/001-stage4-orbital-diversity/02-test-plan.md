# 測試計劃
## Stage 4 軌道面多樣性約束驗證

**版本**: v1.0
**日期**: 2025-10-22
**對應提案**: [00-proposal.md](00-proposal.md)

---

## 1. 測試策略

### 1.1 測試層級

```
Level 1: 單元測試
  ├─ TLE 解析功能
  ├─ RAAN 分組邏輯
  ├─ 軌道面代表選擇
  └─ Gini 係數計算

Level 2: 整合測試
  ├─ 兩階段優化完整流程
  ├─ 配置降級處理
  └─ 錯誤處理與恢復

Level 3: 系統測試
  ├─ Stage 4 完整運行
  ├─ Stage 5, 6 下游驗證
  └─ RL 訓練數據質量

Level 4: 驗收測試
  └─ 與目標指標對比
```

---

## 2. 單元測試用例

### 2.1 TLE 解析測試

**文件**: `tests/unit/test_tle_parsing.py`

```python
import pytest
from src.stages.stage4_link_feasibility.pool_optimizer import PoolOptimizer

class TestTLEParsing:
    def setup_method(self):
        self.optimizer = PoolOptimizer(config={})

    def test_raan_extraction_normal(self):
        """測試正常 TLE 的 RAAN 提取"""
        line1 = "1 44713U 19074A   25295.12345678  .00001234  00000-0  12345-3 0  9999"
        line2 = "2 44713  53.0540  20.1234 0001234 123.4567 236.5432 15.05123456789012"

        raan = self.optimizer._get_raan_from_tle(line1, line2)

        assert abs(raan - 20.1234) < 0.0001
        assert 0 <= raan < 360

    def test_raan_extraction_edge_cases(self):
        """測試邊界情況"""
        # RAAN 接近 0°
        line2_zero = "2 44713  53.0540   0.0001 ..."
        raan_zero = self.optimizer._get_raan_from_tle("", line2_zero)
        assert abs(raan_zero - 0.0001) < 0.0001

        # RAAN 接近 360°
        line2_max = "2 44713  53.0540 359.9999 ..."
        raan_max = self.optimizer._get_raan_from_tle("", line2_max)
        assert abs(raan_max - 359.9999) < 0.0001

    def test_raan_extraction_invalid_format(self):
        """測試無效格式處理"""
        line2_invalid = "INVALID LINE"

        with pytest.raises(ValueError):
            self.optimizer._get_raan_from_tle("", line2_invalid)

    def test_raan_bin_mapping(self):
        """測試 RAAN → Bin 映射"""
        self.optimizer.config = {
            'orbital_diversity': {'target_orbital_planes': 24}
        }

        # 15° per bin (360/24)
        assert self.optimizer._get_raan_bin(0.0) == 0
        assert self.optimizer._get_raan_bin(14.9) == 0
        assert self.optimizer._get_raan_bin(15.0) == 1
        assert self.optimizer._get_raan_bin(359.9) == 23
```

### 2.2 軌道面代表選擇測試

**文件**: `tests/unit/test_raan_representatives.py`

```python
class TestRAANRepresentatives:
    def test_basic_selection(self):
        """測試基本軌道面代表選擇"""
        # 創建 mock 候選（24 個 bins，每個 3 顆）
        candidates = self._create_mock_satellites(
            num_bins=24,
            sats_per_bin=3
        )
        tle_map = self._create_mock_tle_map(candidates)

        representatives = self.optimizer._select_raan_representatives(
            candidates=candidates,
            tle_map=tle_map,
            target_planes=24
        )

        # 驗證數量
        assert len(representatives) == 24

        # 驗證每個 bin 只選 1 顆
        raan_bins_selected = set()
        for sat in representatives:
            raan = self.optimizer._get_raan_from_tle(
                tle_map[sat['satellite_id']]['line1'],
                tle_map[sat['satellite_id']]['line2']
            )
            bin_id = self.optimizer._get_raan_bin(raan)
            assert bin_id not in raan_bins_selected
            raan_bins_selected.add(bin_id)

    def test_selection_prefers_high_contribution(self):
        """測試選擇高貢獻度衛星"""
        # Bin 0: 3 顆衛星，時間點數 [10, 50, 30]
        # 應選擇 50 時間點的衛星

        candidates = [
            {'satellite_id': 'A', 'time_series': self._gen_timepoints(10)},
            {'satellite_id': 'B', 'time_series': self._gen_timepoints(50)},
            {'satellite_id': 'C', 'time_series': self._gen_timepoints(30)},
        ]

        # 所有衛星 RAAN 都在同一 bin (0°-15°)
        tle_map = {
            'A': {'line1': '...', 'line2': '2 ... 5.0 ...'},
            'B': {'line1': '...', 'line2': '2 ... 7.0 ...'},
            'C': {'line1': '...', 'line2': '2 ... 10.0 ...'},
        }

        representatives = self.optimizer._select_raan_representatives(
            candidates=candidates,
            tle_map=tle_map,
            target_planes=24
        )

        # 應選擇 B (50 時間點)
        assert len(representatives) == 1
        assert representatives[0]['satellite_id'] == 'B'

    def test_sparse_bins_handling(self):
        """測試稀疏 bins 處理（某些 bins 為空）"""
        # 只有 10 個 bins 有衛星（非連續）
        candidates = self._create_sparse_satellites(
            bins_with_sats=[0, 3, 5, 8, 10, 15, 18, 21, 23]
        )
        tle_map = self._create_mock_tle_map(candidates)

        representatives = self.optimizer._select_raan_representatives(
            candidates=candidates,
            tle_map=tle_map,
            target_planes=24
        )

        # 應選擇 9 顆（只有 9 個 bins 有衛星）
        assert len(representatives) == 9
```

### 2.3 兩階段優化測試

**文件**: `tests/unit/test_two_stage_optimization.py`

```python
class TestTwoStageOptimization:
    def test_max_per_plane_constraint(self):
        """測試每面最多衛星數約束"""
        candidates = self._create_mock_satellites(
            num_bins=24,
            sats_per_bin=10  # 每個 bin 10 顆
        )
        tle_map = self._create_mock_tle_map(candidates)

        self.optimizer.config = {
            'orbital_diversity': {
                'enabled': True,
                'target_orbital_planes': 24,
                'max_satellites_per_plane': 3
            }
        }

        selected = self.optimizer.optimize_pool(
            candidates=candidates,
            tle_map=tle_map,
            target_min=10,
            target_max=15
        )

        # 驗證約束
        distribution = self.optimizer._count_raan_distribution(selected, tle_map)
        for bin_id, count in distribution.items():
            assert count <= 3, f"Bin {bin_id} 有 {count} 顆衛星 (> 3)"

    def test_coverage_rate_maintenance(self):
        """測試時間覆蓋率保持"""
        candidates = self._create_realistic_candidates(2922)  # Starlink 規模
        tle_map = self._create_mock_tle_map(candidates)

        selected = self.optimizer.optimize_pool(
            candidates=candidates,
            tle_map=tle_map,
            target_min=10,
            target_max=15
        )

        # 計算覆蓋率
        coverage_map = self.optimizer._build_coverage_map(selected)
        coverage_rate = self.optimizer._calculate_coverage_rate(
            coverage_map, 10, 15
        )

        # 應 ≥ 93%
        assert coverage_rate >= 93.0

    def test_gini_coefficient_improvement(self):
        """測試 Gini 係數改善"""
        candidates = self._create_realistic_candidates(2922)
        tle_map = self._create_mock_tle_map(candidates)

        # 運行優化
        selected = self.optimizer.optimize_pool(
            candidates=candidates,
            tle_map=tle_map,
            target_min=10,
            target_max=15
        )

        # 計算 Gini
        distribution = self.optimizer._count_raan_distribution(selected, tle_map)
        gini = self.optimizer._calculate_gini_coefficient(
            list(distribution.values())
        )

        # 應 < 0.3
        assert gini < 0.3, f"Gini {gini:.3f} 仍然過高"
```

### 2.4 Gini 係數計算測試

```python
class TestGiniCoefficient:
    def test_perfect_equality(self):
        """完全均勻分佈 → Gini = 0"""
        counts = [5, 5, 5, 5, 5]  # 完全相等
        gini = self.optimizer._calculate_gini_coefficient(counts)
        assert abs(gini - 0.0) < 0.01

    def test_perfect_inequality(self):
        """完全不均勻 → Gini → 1"""
        counts = [100, 0, 0, 0, 0]  # 一個有全部
        gini = self.optimizer._calculate_gini_coefficient(counts)
        assert gini > 0.9

    def test_moderate_inequality(self):
        """中度不均勻"""
        counts = [10, 8, 5, 3, 1]  # 遞減
        gini = self.optimizer._calculate_gini_coefficient(counts)
        assert 0.2 < gini < 0.5
```

---

## 3. 整合測試

### 3.1 配置降級測試

```python
class TestConfigurationFallback:
    def test_disabled_diversity_constraint(self):
        """測試禁用多樣性約束"""
        config = {
            'orbital_diversity': {'enabled': False}
        }
        optimizer = PoolOptimizer(config)

        # 應降級為原算法（無 tle_map 參數）
        selected = optimizer.optimize_pool(
            candidates=candidates,
            tle_map={},  # 空 map
            target_min=10,
            target_max=15
        )

        # 應成功運行（不報錯）
        assert len(selected) > 0

    def test_missing_tle_data(self):
        """測試 TLE 數據缺失"""
        config = {
            'orbital_diversity': {'enabled': True, 'target_orbital_planes': 24}
        }
        optimizer = PoolOptimizer(config)

        # TLE map 為空
        selected = optimizer.optimize_pool(
            candidates=candidates,
            tle_map={},  # 無 TLE
            target_min=10,
            target_max=15
        )

        # 應降級並發出警告
        # 驗證日誌包含 "TLE 數據不可用"
```

### 3.2 錯誤恢復測試

```python
class TestErrorRecovery:
    def test_partial_tle_availability(self):
        """測試部分衛星缺少 TLE"""
        # 50% 衛星有 TLE，50% 沒有
        candidates = self._create_mock_satellites(100)
        tle_map = {
            sat['satellite_id']: {...}
            for sat in candidates[:50]  # 只有前 50 顆有 TLE
        }

        selected = self.optimizer.optimize_pool(
            candidates=candidates,
            tle_map=tle_map,
            target_min=10,
            target_max=15
        )

        # 應成功運行（跳過無 TLE 的衛星）
        assert len(selected) > 0

    def test_malformed_tle_handling(self):
        """測試格式錯誤 TLE 處理"""
        tle_map = {
            'sat1': {
                'line1': 'INVALID',
                'line2': 'INVALID'
            }
        }

        # 應捕獲異常並跳過
        # 不應導致整個優化失敗
```

---

## 4. 系統測試

### 4.1 完整 Stage 4 運行

**測試腳本**: `tests/integration/test_stage4_full_run.sh`

```bash
#!/bin/bash
# Stage 4 完整運行測試

set -e

echo "=== Stage 4 系統測試 ==="

# 1. 運行 Stage 4
./run.sh --stage 4

# 2. 檢查輸出文件
OUTPUT_FILE=$(ls -t data/outputs/stage4/*.json | head -1)
echo "檢查輸出: $OUTPUT_FILE"

# 3. 驗證指標
python tests/integration/verify_stage4_output.py "$OUTPUT_FILE"
```

**驗證腳本**: `tests/integration/verify_stage4_output.py`

```python
import sys
import json

output_file = sys.argv[1]
with open(output_file) as f:
    data = json.load(f)

pool = data['pool_optimization']['optimized_pools']['starlink']

print(f"衛星數量: {len(pool)}")

# 運行分析
import subprocess
result = subprocess.run(
    ['python', '/tmp/analyze_orbital_distribution.py'],
    capture_output=True,
    text=True
)

# 解析結果
output = result.stdout

# 驗證指標
assert "軌道面數量:" in output
assert "Gini 係數:" in output

# 提取數值（簡化版）
# 完整實現需要解析輸出

print("✅ Stage 4 系統測試通過")
```

### 4.2 下游驗證

```bash
#!/bin/bash
# 測試 Stage 5, 6 是否正常運行

# 運行 Stage 5
./run.sh --stage 5
echo "✅ Stage 5 運行成功"

# 運行 Stage 6
./run.sh --stage 6
echo "✅ Stage 6 運行成功"
```

---

## 5. 驗收測試

### 5.1 驗收標準檢查清單

```python
# tests/acceptance/test_acceptance_criteria.py

def test_orbital_plane_count():
    """驗收標準 1: 軌道面數量 ≥ 24"""
    result = run_analysis()
    assert result['orbital_planes'] >= 24

def test_gini_coefficient():
    """驗收標準 2: Gini < 0.3"""
    result = run_analysis()
    assert result['gini'] < 0.3

def test_satellite_count():
    """驗收標準 3: 衛星數 48-72"""
    result = run_analysis()
    assert 48 <= result['satellite_count'] <= 72

def test_coverage_rate():
    """驗收標準 4: 覆蓋率 ≥ 93%"""
    result = run_analysis()
    assert result['coverage_rate'] >= 93.0

def test_satellites_per_plane():
    """驗收標準 5: 每面 2-3 顆"""
    result = run_analysis()
    avg = result['satellites_per_plane']
    assert 2.0 <= avg <= 3.5
```

---

## 6. 性能測試

### 6.1 運行時間測試

```python
import time

def test_performance_overhead():
    """測試性能影響 < 10 秒"""
    # 運行原算法
    start = time.time()
    original_result = run_original_algorithm()
    original_time = time.time() - start

    # 運行新算法
    start = time.time()
    new_result = run_new_algorithm()
    new_time = time.time() - start

    overhead = new_time - original_time

    assert overhead < 10.0, f"性能退化 {overhead:.1f} 秒 (> 10秒)"
```

---

## 7. 測試數據

### 7.1 Mock 數據生成

```python
def _create_mock_satellites(num_bins=24, sats_per_bin=3):
    """
    創建 mock 衛星數據

    結構:
    - num_bins 個軌道面
    - 每個軌道面 sats_per_bin 顆衛星
    - 每顆衛星有 time_series
    """
    satellites = []
    bin_size = 360.0 / num_bins

    for bin_id in range(num_bins):
        for i in range(sats_per_bin):
            raan = bin_id * bin_size + (bin_size / sats_per_bin) * i
            sat_id = f"SAT{bin_id:02d}_{i}"

            satellites.append({
                'satellite_id': sat_id,
                'time_series': _gen_timepoints(190),
                '_mock_raan': raan  # 用於測試
            })

    return satellites

def _create_mock_tle_map(satellites):
    """為 mock 衛星創建 TLE"""
    tle_map = {}

    for sat in satellites:
        raan = sat.get('_mock_raan', 0.0)
        tle_map[sat['satellite_id']] = {
            'line1': f"1 {sat['satellite_id'][:5].ljust(5)} ...",
            'line2': f"2 {sat['satellite_id'][:5].ljust(5)}  53.0540 {raan:8.4f} 0001234 ...",
            'constellation': 'starlink'
        }

    return tle_map
```

---

## 8. 測試執行計劃

### Phase 1 測試
- [ ] `test_raan_extraction_normal()`
- [ ] `test_raan_extraction_edge_cases()`
- [ ] `test_raan_bin_mapping()`

### Phase 2 測試
- [ ] `test_basic_selection()`
- [ ] `test_selection_prefers_high_contribution()`
- [ ] `test_sparse_bins_handling()`

### Phase 3 測試
- [ ] `test_max_per_plane_constraint()`
- [ ] `test_coverage_rate_maintenance()`
- [ ] `test_gini_coefficient_improvement()`

### Phase 4 測試
- [ ] Stage 4 完整運行
- [ ] 下游 Stage 5, 6 驗證
- [ ] 驗收標準檢查

---

**文件結束**
**下一步**: 查看 [03-api-changes.md](03-api-changes.md)
