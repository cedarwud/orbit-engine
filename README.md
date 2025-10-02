# 🛰️ Orbit Engine - LEO衛星動態池研究系統

**學術研究用六階段衛星數據處理系統，支援 Starlink 和 OneWeb 動態衛星池分析與 3GPP NTN 切換優化研究。**

> 📚 **學術研究專用** - 此系統專為學術論文撰寫與研究而設計，符合 NASA JPL、IAU 和 3GPP 學術標準。

---

## ⚠️ 開發者必讀：學術合規性標準

**本專案遵循嚴格的學術研究標準**，確保所有代碼符合同行審查要求。

### 📚 全局標準指南

**📖 [學術合規性標準指南](docs/ACADEMIC_STANDARDS.md)** - 適用所有六個階段

**核心原則**：
- ❌ 禁止：估計值、假設參數、模擬數據、簡化算法
- ✅ 要求：實測數據、學術引用、官方來源、完整實現

### 🔍 需要檢查時

```bash
# 檢查整個專案
make compliance

# 檢查特定階段
python tools/academic_compliance_checker.py src/stages/stage4_link_feasibility/
```

詳見：[學術合規性標準指南](docs/ACADEMIC_STANDARDS.md)

---

## 🎯 研究目標

- **LEO衛星動態池規劃** - 支援時空錯位理論研究
- **3GPP NTN切換優化** - A4/A5/D2事件檢測與強化學習
- **星座感知計算** - Starlink vs OneWeb 軌道週期差異分析
- **學術標準合規** - NASA JPL(<10m)、IAU(<0.5m)、3GPP精度要求

## 🚀 快速開始

### 系統需求
- Python 3.8+
- 學術標準套件（詳見重構計劃）
- 4GB+ RAM (學術研究用途)
- 2GB+ 可用磁碟空間

### 執行方式

#### 當前版本執行
```bash
# 設置測試模式
export ORBIT_ENGINE_TEST_MODE=1

# 執行完整六階段流程
python scripts/run_six_stages_with_validation.py

# 執行特定階段
python scripts/run_six_stages_with_validation.py --stage 1

# 執行階段範圍
python scripts/run_six_stages_with_validation.py --stages "1-3"
```

## 📋 學術研究六階段架構

### 當前系統 vs 學術重構計劃
```
🏗️ 當前版本: TLE數據 → 軌道計算 → 狀態傳播 → 座標轉換 → 優化決策 → 整合API
🎓 重構目標: TLE管理 → 軌道計算 → 座標轉換 → 動態池分析 → 3GPP事件 → RL環境
```

### 學術重構架構 (詳見 refactor-plan/)
1. **Stage 1: TLE管理** - Spacetrack官方API，獨立epoch時間處理
2. **Stage 2: 軌道計算** - Skyfield(NASA JPL) + PyOrbital(LEO最佳化)
3. **Stage 3: 座標轉換** - Astropy(IAU標準) + SciPy信號處理
4. **Stage 4: 動態池分析** - 時空錯位理論，95%覆蓋連續性
5. **Stage 5: 3GPP事件檢測** - A4/A5/D2切換事件，RL訓練數據
6. **Stage 6: RL環境** - Gymnasium標準環境，DQN/PPO/SAC支援

## 🔧 當前系統說明

### 階段一：TLE數據載入
- **功能**：TLE數據載入與解析
- **狀態**：待重構為Spacetrack API
- **輸出**：結構化衛星軌道數據

### 階段二：軌道狀態傳播
- **功能**：SGP4/SDP4軌道狀態計算
- **狀態**：待升級為Skyfield+PyOrbital
- **目標精度**：<10m (NASA JPL標準)

### 階段三：座標轉換
- **功能**：TEME → WGS84 座標轉換
- **狀態**：待重構為Astropy IAU標準
- **目標精度**：<0.5m (IAU標準)

### 階段四：優化決策
- **功能**：衛星選擇優化
- **狀態**：待重構為動態池概念
- **研究目標**：時空錯位理論實現

### 階段五：數據整合
- **功能**：多階段數據整合
- **狀態**：待重構為3GPP事件檢測
- **研究目標**：A4/A5/D2事件優化

### 階段六：API層
- **功能**：數據持久化與介面
- **狀態**：待重構為RL環境
- **研究目標**：強化學習訓練環境

## 📁 專案結構

```
orbit-engine/
├── refactor-plan/                           # 🎓 學術重構計劃
│   ├── README.md                           # 主重構指南 (35頁)
│   ├── stage1-tle-management/              # Stage 1: Spacetrack API
│   ├── stage2-orbital-computation/         # Stage 2: Skyfield+PyOrbital
│   ├── stage3-coordinate-transformation/   # Stage 3: Astropy+SciPy
│   ├── stage4-satellite-pool/              # Stage 4: 動態池分析
│   ├── stage5-3gpp-events/                # Stage 5: 3GPP事件檢測
│   └── stage6-rl-environment/              # Stage 6: RL環境
├── scripts/
│   └── run_six_stages_with_validation.py   # 當前系統執行腳本
├── src/
│   ├── stages/                             # 當前階段處理器 (待重構)
│   │   ├── stage1_orbital_calculation/
│   │   ├── stage2_orbital_computing/
│   │   ├── stage3_coordinate_transformation/
│   │   ├── stage4_optimization/
│   │   ├── stage5_data_integration/
│   │   └── stage6_persistence_api/
│   └── shared/                             # 共享組件
├── data/
│   ├── outputs/                            # 各階段輸出
│   └── tle_data/                          # TLE數據 (待升級Spacetrack)
├── docs/                                   # 🎓 研究文檔
│   ├── final.md                           # 研究目標與動態池概念
│   ├── academic_standards_clarification.md # 學術標準說明
│   └── stages/                            # 階段文檔
└── visualization_*.py                      # 🎨 學術視覺化展示
```

## 🎓 學術重構計劃

### 重構時程 (5-6週)
- **Week 1**: Stage 1-2 (TLE管理 + 軌道計算)
- **Week 2**: Stage 3 (Astropy座標轉換)
- **Week 3**: Stage 4 (動態池分析)
- **Week 4**: Stage 5 (3GPP事件檢測)
- **Week 5**: Stage 6 (RL環境)
- **Week 6**: 整合測試與論文支援

### 學術標準合規
- **NASA JPL**: 軌道精度 <10m
- **IAU**: 座標轉換精度 <0.5m
- **3GPP**: A4/A5/D2事件檢測標準
- **Gymnasium**: 標準RL環境介面

## 🎨 視覺化功能 (學術展示用)

### 前端衛星池展示
- `visualization_demo.py` - 動態池概念視覺化
- `satellite_3d_demo.html` - 3D衛星軌道展示
- `satellite_dashboard_demo.html` - 學術儀表板

### 研究數據視覺化
- Starlink vs OneWeb 軌道週期對比
- 時空錯位理論視覺化展示
- 3GPP切換事件分析圖表
- RL訓練過程視覺化

## ⚙️ 開發設置

### 環境配置
```bash
# 測試模式 (跳過容器檢查)
export ORBIT_ENGINE_TEST_MODE=1

# 當前系統測試
python scripts/run_six_stages_with_validation.py --stage 1
```

### 重構開發流程
1. **研讀重構計劃**: `refactor-plan/README.md`
2. **按階段實施**: 依照學術標準逐步重構
3. **學術驗證**: 符合NASA JPL、IAU、3GPP標準
4. **視覺化測試**: 確保前端展示功能正常

## 📊 學術研究指標

### 精度目標 (學術標準)
- **軌道精度**: <10m (NASA JPL要求)
- **座標轉換**: <0.5m (IAU標準)
- **時間處理**: 微秒級精度
- **覆蓋連續性**: >95% (動態池要求)

### 系統性能 (研究用途)
- **處理時間**: <60秒 (學術研究可接受)
- **記憶體使用**: <4GB (研究環境)
- **衛星支援**: Starlink(10-15顆) + OneWeb(3-6顆)
- **研究數據**: 支援論文撰寫與分析

### 星座差異分析
| 指標 | Starlink | OneWeb |
|------|----------|--------|
| 軌道週期 | 90-95分鐘 | 109-115分鐘 |
| 可見衛星 | 10-15顆 | 3-6顆 |
| 仰角閾值 | 5° | 10° |
| 研究重點 | 高密度切換 | 長期連接 |

## 🎯 下一步行動

### 立即可執行
```bash
# 測試當前系統
export ORBIT_ENGINE_TEST_MODE=1
python scripts/run_six_stages_with_validation.py

# 查看重構計劃
cd refactor-plan/
ls -la  # 查看所有階段計劃
```

### 學術重構順序
1. **實施 Stage 1**: Spacetrack API整合
2. **升級 Stage 2**: Skyfield精度提升
3. **重構 Stage 3**: Astropy標準合規
4. **開發 Stage 4**: 動態池概念實現
5. **建構 Stage 5**: 3GPP事件檢測
6. **完成 Stage 6**: RL環境標準化

---

**專案狀態**: 學術重構計劃完成，準備實施 🎓
**版本**: v1.1 學術研究特化版
**更新日期**: 2025-09-29
**用途**: 學術論文撰寫與前端視覺化展示