# 技術設計文檔
## Stage 4 軌道面多樣性約束實施

**版本**: v1.0
**日期**: 2025-10-22
**對應提案**: [00-proposal.md](00-proposal.md)

---

## 1. 架構概覽

### 1.1 模塊結構

```
src/stages/stage4_link_feasibility/
├── pool_optimizer.py              # 主要修改
│   ├── PoolOptimizer (class)
│   │   ├── optimize_pool()        # 修改: 兩階段流程
│   │   ├── _select_raan_representatives()  # 新增: 階段 1
│   │   ├── _select_next_best_satellite()   # 修改: 增加 max_per_plane
│   │   ├── _get_raan_from_tle()   # 新增: TLE 解析
│   │   └── _count_raan_distribution()  # 新增: 統計軌道面
│
└── stage4_link_feasibility_processor.py  # 次要修改
    └── _optimize_satellite_pools()  # 修改: 傳遞 TLE 數據

scripts/stage_executors/
└── stage4_executor.py             # 無需修改（已正確讀取 Stage 1）

config/
└── stage4_link_feasibility_config.yaml  # 修改: 增加配置項
```

### 1.2 數據流

```
Stage 1 輸出 (stage1_output.json)
  ├─ satellites[]
  │    ├─ satellite_id
  │    ├─ tle_line1  ← 需要
  │    ├─ tle_line2  ← 需要
  │    └─ constellation
  │
  ↓
Stage 4 Processor
  ├─ 載入 Stage 1 數據
  ├─ 建立 satellite_id → TLE 映射
  └─ 傳遞給 PoolOptimizer
      │
      ↓
PoolOptimizer.optimize_pool()
  │
  ├─ 階段 1: _select_raan_representatives()
  │    ├─ 解析所有候選衛星的 RAAN
  │    ├─ 按 RAAN 均勻分組（24 個 bins）
  │    └─ 從每個 bin 選擇 1 顆代表
  │
  └─ 階段 2: Greedy Set Cover (修改版)
       ├─ 計算當前覆蓋率
       ├─ _select_next_best_satellite()
       │    ├─ 檢查 max_per_plane 約束
       │    └─ 選擇貢獻度最高的衛星
       └─ 重複直到達成覆蓋目標
```

---

## 2. 核心算法設計

### 2.1 兩階段選擇主流程

```python
def optimize_pool(
    self,
    candidates: List[Dict],
    tle_map: Dict[str, Dict],  # 新增參數
    target_min: int,
    target_max: int
) -> List[Dict]:
    """
    兩階段衛星池優化

    階段 1: 軌道面多樣性保證（Orbital Diversity Guarantee）
    階段 2: 時間覆蓋率優化（Temporal Coverage Optimization）

    參數:
        candidates: 候選衛星列表
        tle_map: satellite_id → {'line1': str, 'line2': str}
        target_min: 最小可見衛星數（例如 10）
        target_max: 最大可見衛星數（例如 15）

    返回:
        selected_satellites: 優化後的衛星列表

    SOURCE:
        - Stage 1: Diversity-Aware Set Cover
        - Stage 2: Chvátal (1979) Greedy Set Cover
    """
    # 檢查是否啟用多樣性約束
    if not self.config.get('orbital_diversity', {}).get('enabled', True):
        # 降級為原算法
        logger.warning("軌道面多樣性約束已禁用，使用原始 Greedy 算法")
        return self._original_optimize_pool(candidates, target_min, target_max)

    # 提取配置參數
    diversity_config = self.config['orbital_diversity']
    target_planes = diversity_config.get('target_orbital_planes', 24)
    max_per_plane = diversity_config.get('max_satellites_per_plane', 3)

    logger.info(f"🚀 開始兩階段池優化")
    logger.info(f"   目標軌道面數: {target_planes}")
    logger.info(f"   每面最多衛星數: {max_per_plane}")

    # === 階段 1: 軌道面代表選擇 ===
    logger.info(f"📍 階段 1: 選擇軌道面代表...")

    representatives = self._select_raan_representatives(
        candidates=candidates,
        tle_map=tle_map,
        target_planes=target_planes
    )

    logger.info(f"   已選擇 {len(representatives)} 顆代表衛星")

    # 建立初始覆蓋
    selected = list(representatives)
    current_coverage = self._build_coverage_map(selected)

    # 檢查階段 1 覆蓋率
    coverage_rate = self._calculate_coverage_rate(
        current_coverage, target_min, target_max
    )
    logger.info(f"   階段 1 覆蓋率: {coverage_rate:.1f}%")

    # === 階段 2: Greedy 填補覆蓋缺口 ===
    logger.info(f"🔍 階段 2: Greedy 填補覆蓋缺口...")

    iteration = 0
    max_iterations = len(candidates)  # 防止無限循環

    while coverage_rate < self.target_coverage_rate:
        if iteration >= max_iterations:
            logger.warning(f"   達到最大迭代次數，停止優化")
            break

        # 選擇下一顆最佳衛星（帶 max_per_plane 約束）
        best_satellite = self._select_next_best_satellite(
            candidates=candidates,
            current_coverage=current_coverage,
            selected_satellites=selected,
            tle_map=tle_map,
            max_per_plane=max_per_plane,
            target_min=target_min,
            target_max=target_max
        )

        if best_satellite is None:
            # 沒有更多衛星可選（所有軌道面都達到上限）
            logger.warning(f"   無法找到滿足約束的衛星，停止優化")
            break

        # 添加衛星並更新覆蓋
        selected.append(best_satellite)
        candidates.remove(best_satellite)
        current_coverage = self._build_coverage_map(selected)
        coverage_rate = self._calculate_coverage_rate(
            current_coverage, target_min, target_max
        )

        iteration += 1

        # 定期報告進度
        if iteration % 10 == 0:
            logger.info(f"   優化進度: {len(selected)} 顆已選擇 "
                       f"(覆蓋率: {coverage_rate:.1f}%)")

    # === 最終驗證 ===
    logger.info(f"✅ 兩階段優化完成:")
    logger.info(f"   選擇數量: {len(selected)} 顆")
    logger.info(f"   覆蓋率: {coverage_rate:.1f}%")

    # 分析軌道面分佈
    raan_distribution = self._count_raan_distribution(selected, tle_map)
    unique_planes = len(raan_distribution)
    avg_per_plane = len(selected) / unique_planes if unique_planes > 0 else 0

    logger.info(f"   軌道面數量: {unique_planes}")
    logger.info(f"   每面平均: {avg_per_plane:.1f} 顆")

    # 計算 Gini 係數
    gini = self._calculate_gini_coefficient(list(raan_distribution.values()))
    logger.info(f"   Gini 係數: {gini:.3f}")

    if gini < 0.3:
        logger.info(f"   ✅ 分佈均勻")
    elif gini < 0.5:
        logger.warning(f"   ⚠️ 有一定程度聚類")
    else:
        logger.warning(f"   ❌ 嚴重聚類")

    return selected
```

### 2.2 階段 1: 軌道面代表選擇

```python
def _select_raan_representatives(
    self,
    candidates: List[Dict],
    tle_map: Dict[str, Dict],
    target_planes: int
) -> List[Dict]:
    """
    從候選池中選擇軌道面代表衛星

    策略:
    1. 將 360° RAAN 空間均勻分割為 target_planes 個 bins
    2. 將候選衛星按 RAAN 分組到對應 bin
    3. 從每個 bin 選擇貢獻度最高的 1 顆

    參數:
        candidates: 候選衛星列表
        tle_map: satellite_id → TLE 映射
        target_planes: 目標軌道面數量

    返回:
        representatives: 選中的代表衛星列表（最多 target_planes 顆）

    SOURCE:
        Diversity-Aware Set Cover
        (參考 Kumar et al. 2013 "Diversity in Combinatorial Optimization")
    """
    from collections import defaultdict

    bin_size = 360.0 / target_planes  # 例如 360/24 = 15°
    raan_groups = defaultdict(list)

    # 按 RAAN 分組
    for satellite in candidates:
        sat_id = satellite['satellite_id']

        if sat_id not in tle_map:
            logger.warning(f"   衛星 {sat_id} 無 TLE 數據，跳過")
            continue

        # 解析 RAAN
        raan = self._get_raan_from_tle(
            tle_map[sat_id]['line1'],
            tle_map[sat_id]['line2']
        )

        # 分配到 bin
        bin_id = int(raan // bin_size)
        raan_groups[bin_id].append(satellite)

    logger.info(f"   RAAN 分組完成: {len(raan_groups)} 個非空 bins")

    # 從每個 bin 選擇代表
    representatives = []

    for bin_id in sorted(raan_groups.keys()):
        group = raan_groups[bin_id]

        if not group:
            continue

        # 選擇該組內「可連線時間點最多」的衛星
        # （這樣的衛星在 Greedy 階段貢獻度最高）
        best_in_group = max(
            group,
            key=lambda sat: self._count_connectable_timepoints(sat)
        )

        representatives.append(best_in_group)

        logger.debug(f"   Bin {bin_id} (RAAN {bin_id*bin_size:.1f}°-"
                    f"{(bin_id+1)*bin_size:.1f}°): "
                    f"選擇衛星 {best_in_group['satellite_id']}")

    return representatives
```

### 2.3 階段 2: 帶約束的 Greedy 選擇

```python
def _select_next_best_satellite(
    self,
    candidates: List[Dict],
    current_coverage: Dict[str, Set[str]],
    selected_satellites: List[Dict],
    tle_map: Dict[str, Dict],
    max_per_plane: int,
    target_min: int,
    target_max: int
) -> Optional[Dict]:
    """
    選擇下一顆最佳衛星（帶軌道面數量約束）

    修改點:
    - 增加 max_per_plane 約束檢查
    - 如果某軌道面已達上限，跳過該軌道面的衛星

    參數:
        candidates: 候選衛星列表
        current_coverage: 當前覆蓋映射 {timestamp: set(sat_ids)}
        selected_satellites: 已選衛星列表
        tle_map: satellite_id → TLE 映射
        max_per_plane: 每個軌道面最多衛星數
        target_min: 最小可見衛星數
        target_max: 最大可見衛星數

    返回:
        best_satellite: 貢獻度最高的衛星（或 None）

    SOURCE:
        Chvátal (1979) Greedy Set Cover + Diversity Constraint
    """
    # 統計已選衛星的軌道面分佈
    raan_distribution = self._count_raan_distribution(
        selected_satellites, tle_map
    )

    best_satellite = None
    best_contribution = -1

    for satellite in candidates:
        sat_id = satellite['satellite_id']

        # === 軌道面約束檢查 ===
        if sat_id in tle_map:
            raan = self._get_raan_from_tle(
                tle_map[sat_id]['line1'],
                tle_map[sat_id]['line2']
            )
            raan_bin = self._get_raan_bin(raan)

            # 檢查該軌道面是否已達上限
            if raan_distribution[raan_bin] >= max_per_plane:
                # 跳過此衛星
                continue

        # === 貢獻度計算（原邏輯） ===
        contribution = 0
        penalty = 0

        for time_point in satellite.get('time_series', []):
            if not time_point['visibility_metrics']['is_connectable']:
                continue

            timestamp = time_point['timestamp']
            current_visible = len(current_coverage.get(timestamp, set()))

            # 計算貢獻度
            if current_visible < target_min:
                contribution += 1  # 需要覆蓋
            elif current_visible >= target_max:
                penalty += 1  # 已過度覆蓋

        # 綜合分數
        score = contribution - penalty * 0.5

        # 更新最佳選擇
        if score > best_contribution:
            best_contribution = score
            best_satellite = satellite

    return best_satellite
```

### 2.4 TLE 解析與 RAAN 提取

```python
def _get_raan_from_tle(self, line1: str, line2: str) -> float:
    """
    從 TLE 提取 RAAN（升交點赤經）

    TLE Line 2 格式:
    2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
              ^^^^^^^^^^^
              位置 17-24: RAAN (degrees)

    參數:
        line1: TLE 第一行
        line2: TLE 第二行

    返回:
        raan: RAAN 值（度，0-360）

    SOURCE:
        NORAD TLE Format Specification
        https://celestrak.org/NORAD/documentation/tle-fmt.php

    EXAMPLE:
        line2 = "2 44713  53.0540  20.1234 0001234 ..."
        raan = 20.1234 degrees
    """
    try:
        raan_str = line2[17:25].strip()
        raan = float(raan_str)
        return raan
    except (ValueError, IndexError) as e:
        logger.error(f"TLE 解析失敗: {e}")
        logger.error(f"Line2: {line2}")
        raise ValueError(f"無法解析 RAAN: {line2}")
```

### 2.5 輔助函數

```python
def _get_raan_bin(self, raan: float) -> int:
    """
    將 RAAN 映射到 bin ID

    參數:
        raan: RAAN 值（度，0-360）

    返回:
        bin_id: Bin ID (0 到 target_planes-1)
    """
    bin_size = 360.0 / self.config['orbital_diversity']['target_orbital_planes']
    return int(raan // bin_size)


def _count_raan_distribution(
    self,
    satellites: List[Dict],
    tle_map: Dict[str, Dict]
) -> Dict[int, int]:
    """
    統計衛星的軌道面分佈

    參數:
        satellites: 衛星列表
        tle_map: satellite_id → TLE 映射

    返回:
        distribution: {bin_id: count}
    """
    from collections import defaultdict

    distribution = defaultdict(int)

    for sat in satellites:
        sat_id = sat['satellite_id']

        if sat_id not in tle_map:
            continue

        raan = self._get_raan_from_tle(
            tle_map[sat_id]['line1'],
            tle_map[sat_id]['line2']
        )
        bin_id = self._get_raan_bin(raan)
        distribution[bin_id] += 1

    return distribution


def _count_connectable_timepoints(self, satellite: Dict) -> int:
    """
    計算衛星的可連線時間點數量

    參數:
        satellite: 衛星數據（包含 time_series）

    返回:
        count: 可連線時間點數量
    """
    count = 0
    for time_point in satellite.get('time_series', []):
        if time_point['visibility_metrics']['is_connectable']:
            count += 1
    return count


def _calculate_gini_coefficient(self, counts: List[int]) -> float:
    """
    計算 Gini 係數（衡量分佈均勻性）

    參數:
        counts: 各組數量列表

    返回:
        gini: Gini 係數（0=完全均勻, 1=完全不均勻）

    SOURCE:
        Gini, C. (1912). "Variabilità e mutabilità"
    """
    import numpy as np

    if not counts or sum(counts) == 0:
        return 0.0

    sorted_counts = sorted(counts)
    n = len(sorted_counts)
    index = np.arange(1, n + 1)

    gini = ((2 * index - n - 1) * sorted_counts).sum() / (n * sum(sorted_counts))
    return gini
```

---

## 3. 數據結構設計

### 3.1 配置結構

```yaml
# config/stage4_link_feasibility_config.yaml

pool_optimization:
  starlink:
    # === 現有配置（保持不變）===
    target_min: 10
    target_max: 15
    target_coverage_rate: 0.95

    # === 新增配置 ===
    orbital_diversity:
      enabled: true                    # 開關（向後兼容）

      target_orbital_planes: 24        # 目標軌道面數量
                                       # SOURCE: 論文典型配置（24-36 個面）
                                       # Starlink 總共 72 個軌道面
                                       # 採樣 1/3 = 24 個面

      max_satellites_per_plane: 3      # 每個軌道面最多衛星數
                                       # SOURCE: 論文配置（通常 2-3 顆）
                                       # 階段 1 選 1 顆，階段 2 最多再加 2 顆

      raan_bin_size_deg: 15.0          # RAAN 分組大小（度）
                                       # 計算公式: 360 / target_orbital_planes
                                       # 此參數自動計算，可手動覆蓋

  oneweb:
    # OneWeb 配置（類似結構）
    target_min: 3
    target_max: 6
    orbital_diversity:
      enabled: true
      target_orbital_planes: 18        # OneWeb 配置（較少軌道面）
      max_satellites_per_plane: 2
```

### 3.2 TLE 映射結構

```python
# satellite_id → TLE 映射
tle_map: Dict[str, Dict] = {
    "44713": {
        "line1": "1 44713U 19074A   25295.12345678  .00001234  00000-0  12345-3 0  9999",
        "line2": "2 44713  53.0540  20.1234 0001234 123.4567 236.5432 15.05123456789012",
        "constellation": "starlink"
    },
    "44714": {
        "line1": "...",
        "line2": "...",
        "constellation": "starlink"
    },
    # ... 更多衛星
}
```

### 3.3 RAAN 分組結構

```python
# RAAN bin → 衛星列表映射
raan_groups: Dict[int, List[Dict]] = {
    0: [sat1, sat2, sat3],   # RAAN 0°-15°
    1: [sat4, sat5],         # RAAN 15°-30°
    2: [sat6],               # RAAN 30°-45°
    # ...
    23: [sat98, sat99]       # RAAN 345°-360°
}

# RAAN bin → 計數映射（用於約束檢查）
raan_distribution: Dict[int, int] = {
    0: 3,   # Bin 0 有 3 顆衛星
    1: 2,   # Bin 1 有 2 顆衛星
    2: 1,   # Bin 2 有 1 顆衛星
    # ...
}
```

---

## 4. 接口變更

### 4.1 PoolOptimizer 類接口

#### 修改的方法

```python
class PoolOptimizer:
    def optimize_pool(
        self,
        candidates: List[Dict],
        tle_map: Dict[str, Dict],  # 新增參數 ⚠️
        target_min: int,
        target_max: int
    ) -> List[Dict]:
        """修改: 增加 tle_map 參數"""
        pass
```

#### 新增的方法

```python
class PoolOptimizer:
    def _select_raan_representatives(
        self,
        candidates: List[Dict],
        tle_map: Dict[str, Dict],
        target_planes: int
    ) -> List[Dict]:
        """新增: 階段 1 - 軌道面代表選擇"""
        pass

    def _get_raan_from_tle(
        self,
        line1: str,
        line2: str
    ) -> float:
        """新增: TLE 解析 - 提取 RAAN"""
        pass

    def _get_raan_bin(
        self,
        raan: float
    ) -> int:
        """新增: RAAN → bin ID 映射"""
        pass

    def _count_raan_distribution(
        self,
        satellites: List[Dict],
        tle_map: Dict[str, Dict]
    ) -> Dict[int, int]:
        """新增: 統計軌道面分佈"""
        pass

    def _count_connectable_timepoints(
        self,
        satellite: Dict
    ) -> int:
        """新增: 計算可連線時間點數"""
        pass

    def _calculate_gini_coefficient(
        self,
        counts: List[int]
    ) -> float:
        """新增: 計算 Gini 係數"""
        pass
```

### 4.2 Stage 4 Processor 接口

```python
class Stage4LinkFeasibilityProcessor:
    def _optimize_satellite_pools(
        self,
        candidates: Dict[str, List[Dict]],
        stage1_data: Dict  # 新增: 讀取 Stage 1 數據 ⚠️
    ) -> Dict[str, List[Dict]]:
        """
        修改:
        1. 從 stage1_data 建立 tle_map
        2. 傳遞 tle_map 給 pool_optimizer.optimize_pool()
        """
        # 建立 TLE 映射
        tle_map = self._build_tle_map(stage1_data)

        # 調用優化器
        optimized = pool_optimizer.optimize_pool(
            candidates=candidates['starlink'],
            tle_map=tle_map,  # 新增參數
            target_min=10,
            target_max=15
        )

        return {'starlink': optimized, 'oneweb': ...}

    def _build_tle_map(
        self,
        stage1_data: Dict
    ) -> Dict[str, Dict]:
        """
        新增:
        從 Stage 1 數據建立 satellite_id → TLE 映射
        """
        tle_map = {}

        for sat in stage1_data['satellites']:
            sat_id = sat['satellite_id']
            tle_map[sat_id] = {
                'line1': sat['tle_line1'],
                'line2': sat['tle_line2'],
                'constellation': sat['constellation']
            }

        return tle_map
```

---

## 5. 配置參數詳細說明

### 5.1 orbital_diversity.enabled

- **類型**: Boolean
- **默認值**: `true`
- **用途**: 啟用/禁用軌道面多樣性約束
- **影響**:
  - `true`: 使用兩階段選擇算法
  - `false`: 降級為原始 Greedy Set Cover

### 5.2 orbital_diversity.target_orbital_planes

- **類型**: Integer
- **默認值**: `24`
- **範圍**: 10-36（建議）
- **用途**: 目標軌道面數量
- **調優指南**:
  - **增加** (24 → 30):
    - ✅ 更均勻的空間分佈
    - ✅ 更低的 Gini 係數
    - ❌ 衛星總數增加
    - ❌ 可能降低覆蓋率
  - **減少** (24 → 20):
    - ✅ 衛星總數減少
    - ✅ 更容易達成覆蓋率
    - ❌ 空間分佈較差
    - ❌ Gini 係數增加

**SOURCE**: 論文典型配置
- IEEE IoT 2024: 48 顆衛星，推測 24 個軌道面
- Starlink 總共 72 個軌道面，採樣 1/3 = 24

### 5.3 orbital_diversity.max_satellites_per_plane

- **類型**: Integer
- **默認值**: `3`
- **範圍**: 2-5（建議）
- **用途**: 每個軌道面最多衛星數
- **調優指南**:
  - **增加** (3 → 4):
    - ✅ 更容易達成覆蓋率
    - ❌ 單一軌道面過多衛星
    - ❌ Gini 係數增加
  - **減少** (3 → 2):
    - ✅ 更均勻的分佈
    - ✅ 更低的 Gini 係數
    - ❌ 可能無法達成覆蓋率（需增加軌道面數）

**SOURCE**: 論文典型配置
- 48 顆 ÷ 24 面 = 2 顆/面
- 我們設置 3 顆允許更高覆蓋率

### 5.4 orbital_diversity.raan_bin_size_deg

- **類型**: Float
- **自動計算**: `360.0 / target_orbital_planes`
- **手動覆蓋**: 可選
- **用途**: RAAN 分組大小（度）
- **通常無需修改**

---

## 6. 錯誤處理

### 6.1 TLE 數據不可用

```python
if sat_id not in tle_map:
    logger.warning(f"衛星 {sat_id} 無 TLE 數據，跳過")
    # 降級處理：
    # - 階段 1: 跳過該衛星
    # - 階段 2: 不檢查軌道面約束
    continue
```

### 6.2 RAAN 解析失敗

```python
try:
    raan = float(line2[17:25].strip())
except (ValueError, IndexError):
    logger.error(f"TLE 解析失敗: {line2}")
    # 降級處理：
    # - 階段 1: 跳過該衛星
    # - 階段 2: 不檢查軌道面約束
    raise ValueError(...)
```

### 6.3 無法達成覆蓋率目標

```python
if iteration >= max_iterations:
    logger.warning(f"達到最大迭代次數，覆蓋率僅 {coverage_rate:.1f}%")
    logger.warning(f"可能原因：max_per_plane 約束過嚴格")
    logger.warning(f"建議：增加 max_per_plane 或減少 target_planes")
    # 返回當前選擇（允許覆蓋率不達標）
    return selected
```

---

## 7. 性能考量

### 7.1 時間複雜度

**階段 1**: O(n)
- n = 候選衛星數量 (~3000)
- RAAN 解析: O(1) per satellite
- 總計: ~3000 次字符串解析 ≈ 1-2 秒

**階段 2**: O(m × n × t)
- m = 迭代次數 (~24-48)
- n = 剩餘候選數 (~2900)
- t = 平均時間序列長度 (~190)
- 總計: ~10-20 秒（與原算法相當）

**總增加時間**: < 10 秒（可接受）

### 7.2 空間複雜度

- TLE 映射: O(n) × ~200 bytes ≈ 600 KB
- RAAN 分組: O(n) × ~8 bytes ≈ 24 KB
- **總增加內存**: < 1 MB（可忽略）

---

## 8. 測試接口

### 8.1 單元測試入口

```python
# tests/test_pool_optimizer_diversity.py

def test_raan_parsing():
    """測試 RAAN 解析正確性"""
    optimizer = PoolOptimizer(config)
    line1 = "1 44713U ..."
    line2 = "2 44713  53.0540  20.1234 ..."
    raan = optimizer._get_raan_from_tle(line1, line2)
    assert abs(raan - 20.1234) < 0.01


def test_raan_representatives_selection():
    """測試軌道面代表選擇"""
    representatives = optimizer._select_raan_representatives(
        candidates=mock_satellites,
        tle_map=mock_tle_map,
        target_planes=24
    )
    assert len(representatives) == 24


def test_max_per_plane_constraint():
    """測試每面最多衛星數約束"""
    selected = optimizer.optimize_pool(
        candidates=mock_satellites,
        tle_map=mock_tle_map,
        target_min=10,
        target_max=15
    )
    distribution = optimizer._count_raan_distribution(selected, mock_tle_map)
    assert all(count <= 3 for count in distribution.values())
```

---

## 9. 版本兼容性

### 9.1 向後兼容

**配置降級**:
```yaml
# 舊配置（無 orbital_diversity）
pool_optimization:
  starlink:
    target_min: 10
    target_max: 15
```

**行為**:
- 自動檢測缺失配置項
- 降級為原始 Greedy 算法
- 發出警告日誌

**代碼**:
```python
if 'orbital_diversity' not in self.config:
    logger.warning("未找到 orbital_diversity 配置，使用原始算法")
    return self._original_optimize_pool(...)
```

### 9.2 TLE 數據缺失處理

**場景**: Stage 1 輸出缺少 TLE 欄位

**行為**:
- 檢測 tle_map 為空
- 降級為原始算法
- 發出警告

**代碼**:
```python
if not tle_map:
    logger.warning("TLE 數據不可用，降級為原始算法")
    return self._original_optimize_pool(...)
```

---

**文件結束**
**下一步**: 查看 [02-test-plan.md](02-test-plan.md)
