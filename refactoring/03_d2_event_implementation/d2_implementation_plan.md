# P0-3: D2 事件完整实现计划

**优先级**: P0（核心功能修复）
**工作量**: 2-3天
**依据**: 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a

---

## 🚨 问题分析

### 当前实现错误

**文件**: `src/stages/stage6_research_optimization/gpp_event_detector.py`

**错误代码** (Lines 463, 476):
```python
serving_distance = serving_satellite['physical_parameters']['distance_km']
neighbor_distance = neighbor['physical_parameters']['distance_km']
# ❌ 这是 3D 斜距（UE → 卫星直线距离）
```

### 3GPP 标准要求

**docs/ts.md Lines 145-150**:
```
Ml1 = distance between UE and a moving reference location
      └─ Moving reference location determined based on:
         ├─ movingReferenceLocation parameter
         ├─ Epoch time
         └─ satellite ephemeris (broadcast in SIB19)
```

**关键词解读**:
- **moving reference location** = 卫星的地面投影点（sub-satellite point）
- **distance** = UE 到地面投影点的 2D 地面距离（大圆距离）
- **单位** = 米 (meters)，不是公里

### 错误对比

| 场景 | 3D 斜距（错误） | 2D 地面距离（正确） | 误差 |
|------|----------------|-------------------|------|
| 卫星在头顶 (90°) | 550 km | ~0 km | 550 km |
| 中等仰角 (45°) | 780 km | ~550 km | 230 km |
| 地平线 (5°) | 2300 km | ~2000 km | 300 km |

---

## ✅ 正确实现方案

### 实现步骤概览

1. **ECEF → Geodetic 坐标转换** - 将卫星 3D 位置转换为地理坐标
2. **地面投影点提取** - 获取 (lat, lon)，忽略高度
3. **Haversine 距离计算** - 计算 UE 到投影点的大圆距离

---

## 🔧 新增模块设计

### 模块 1: `coordinate_converter.py`

**功能**: ECEF → Geodetic 坐标转换

**SOURCE**:
- WGS84 椭球参数: NIMA TR8350.2 (2000)
- 转换算法: Bowring (1985) 快速迭代法

**代码框架**:
```python
def ecef_to_geodetic(x_m, y_m, z_m):
    \"\"\"
    ECEF → WGS84 Geodetic 坐标转换

    SOURCE: Bowring, B. R. (1985). "The accuracy of geodetic latitude and height equations"

    Args:
        x_m, y_m, z_m: ECEF 坐标 (米)

    Returns:
        (lat_deg, lon_deg, alt_m): 大地坐标 (度, 度, 米)
    \"\"\"
    # WGS84 椭球参数
    a = 6378137.0  # 长半轴 (m) - SOURCE: NIMA TR8350.2
    f = 1.0 / 298.257223563  # 扁率

    # Bowring 迭代算法
    # ...
```

### 模块 2: `ground_distance_calculator.py`

**功能**: 地面大圆距离计算

**SOURCE**:
- Haversine formula: Sinnott, R.W. (1984) "Virtues of the Haversine"
- Vincenty formula (高精度备选): Vincenty, T. (1975)

**代码框架**:
```python
def haversine_distance(lat1_deg, lon1_deg, lat2_deg, lon2_deg):
    \"\"\"
    计算两点之间的地面大圆距离

    SOURCE: Sinnott, R.W. (1984). "Virtues of the Haversine"
            Sky & Telescope, 68(2), 159

    Args:
        lat1_deg, lon1_deg: 第一点大地坐标 (度)
        lat2_deg, lon2_deg: 第二点大地坐标 (度)

    Returns:
        distance_m: 地面距离 (米)
    \"\"\"
    R = 6371000.0  # 地球半径 (m) - SOURCE: IUGG mean radius

    # Haversine 公式
    # ...
```

### 模块 3: 重构 `detect_d2_events`

**修改**: `gpp_event_detector.py` Lines 431-510

**新逻辑**:
```python
def detect_d2_events(self, serving_satellite, neighbor_satellites):
    # 1. 获取 UE 位置（NTPU 地面站）
    ue_lat = 24.94388888  # SOURCE: GPS Survey
    ue_lon = 121.37083333

    # 2. 计算服务卫星的地面距离
    serving_ecef = serving_satellite['physical_parameters']['position_ecef_m']
    serving_lat, serving_lon, _ = ecef_to_geodetic(*serving_ecef)
    serving_ground_distance_m = haversine_distance(ue_lat, ue_lon, serving_lat, serving_lon)

    # 3. 检查鄰居衛星
    for neighbor in neighbor_satellites:
        neighbor_ecef = neighbor['physical_parameters']['position_ecef_m']
        neighbor_lat, neighbor_lon, _ = ecef_to_geodetic(*neighbor_ecef)
        neighbor_ground_distance_m = haversine_distance(ue_lat, ue_lon, neighbor_lat, neighbor_lon)

        # 4. D2 條件檢查
        if (serving_ground_distance_m - hys_m) > thresh1_m and \
           (neighbor_ground_distance_m + hys_m) < thresh2_m:
            # 觸發 D2 事件
```

---

## 📋 实施步骤详细

### 第 1 天: 基础组件开发

#### 上午 (9:00-12:00): 实现 coordinate_converter.py
- [ ] 研究 Bowring (1985) 算法
- [ ] 实现 ECEF → Geodetic 转换
- [ ] 验证 WGS84 参数来源
- [ ] 编写单元测试

#### 下午 (14:00-17:00): 实现 ground_distance_calculator.py
- [ ] 实现 Haversine 公式
- [ ] 验证地球半径参数
- [ ] 编写单元测试
- [ ] (可选) 实现 Vincenty 高精度版本

### 第 2 天: D2 检测器重构

#### 上午 (9:00-12:00): 检查数据可用性
- [ ] 确认 Stage 5 是否提供 ECEF 位置
- [ ] 如果没有，修改 Stage 5 添加 position_ecef_m 字段
- [ ] 或在 Stage 6 中从其他数据推导

#### 下午 (14:00-17:00): 重构 detect_d2_events
- [ ] 集成 coordinate_converter
- [ ] 集成 ground_distance_calculator
- [ ] 修改 D2 检测逻辑
- [ ] 更新门槛单位（km → m）

### 第 3 天: 测试与验证

#### 上午 (9:00-12:00): 单元测试
- [ ] 测试坐标转换精度
- [ ] 测试距离计算精度
- [ ] 测试 D2 事件检测逻辑

#### 下午 (14:00-17:00): 集成测试
- [ ] 运行完整 Stage 6
- [ ] 验证 D2 事件输出
- [ ] 对比修复前后事件数量
- [ ] 检查事件合理性

---

## ✅ 验证标准

### 坐标转换精度
```python
# 测试案例：已知 ECEF → Geodetic
test_cases = [
    # (x, y, z, expected_lat, expected_lon, expected_alt)
    (6378137, 0, 0, 0.0, 0.0, 0.0),  # 赤道
    (0, 0, 6356752, 90.0, 0.0, 0.0),  # 北极
]
# 精度要求：< 1e-6 度，< 0.1 m
```

### 距离计算精度
```python
# 测试案例：已知距离
test_cases = [
    # (lat1, lon1, lat2, lon2, expected_distance_m)
    (0, 0, 0, 1, 111319.5),  # 赤道 1 度
    (45, 0, 45, 1, 78846.8),  # 45° 纬线 1 度
]
# 精度要求：< 1% 误差
```

### D2 事件合理性
```bash
# 检查 D2 事件输出
jq '.gpp_events.d2_events[0]' data/outputs/stage6/*.json

# 预期字段：
# - serving_ground_distance_m (应该 > 2000000)
# - neighbor_ground_distance_m (应该 < 1500000)
# - 单位：米
```

---

## 📚 参考资料

### 学术文献
- Bowring, B. R. (1985). "The accuracy of geodetic latitude and height equations"
- Sinnott, R.W. (1984). "Virtues of the Haversine", Sky & Telescope
- Vincenty, T. (1975). "Direct and inverse solutions of geodesics on the ellipsoid"

### 标准文档
- 3GPP TS 38.331 v18.5.1 Section 5.5.4.15a - D2 事件定义
- NIMA TR8350.2 (2000) - WGS84 椭球参数
- IUGG - 地球平均半径

---

**完成后**: 继续执行 [集成与迁移](../04_integration/)
