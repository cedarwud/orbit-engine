# ML Data Generator - DEPRECATED

**歸檔日期**: 2025-10-24
**原位置**: `orbit-engine/tools/ml_data_generator/`
**歸檔原因**: 功能已被 ml_training_data_generator 取代

---

## 廢棄原因

### 問題

1. **功能過時** ⚠️
   - 不支援 temporal features（velocity, prediction）
   - 不支援 D2 Integration
   - 狀態維度固定為 53 維（已過時）

2. **功能重複** ⚠️
   - `ml_training_data_generator/` 提供完全相同功能，且更完整
   - 維護兩份數據生成器違反 DRY 原則

3. **未被使用** ⚠️
   - 當前 RL 訓練使用 `ml_training_data_generator/` 生成的數據
   - 此版本已停止使用

---

## 替代方案

### 使用 ml_training_data_generator

**位置**: `/home/sat/satellite/orbit-engine/tools/ml_training_data_generator/`

**功能對照**:

| 此歸檔版本 | ml_training_data_generator | 狀態 |
|-----------|---------------------------|------|
| 狀態維度 | 53 維 | ✅ **77 維**（含 temporal features） |
| Temporal Features | ❌ 不支援 | ✅ **支援**（velocity, prediction） |
| D2 Integration | ❌ 不支援 | ✅ **支援** |
| State Extraction | 基礎實現 | ✅ **完整實現**（TemporalFeatureCalculator） |
| Reward Calculation | 基礎實現 | ✅ **完整實現**（含 D2 加權） |
| Dataset Builder | 基礎實現 | ✅ **完整實現**（train/val/test split） |

**ml_training_data_generator 的優勢**:
- ✅ 支援 77-dim temporal features
- ✅ 支援 D2 Integration
- ✅ 支援 Elite/Candidate pool
- ✅ 更好的模組化設計（core/ 模組）
- ✅ 完整的測試覆蓋

---

## 歸檔內容

### 文件結構

```
ml_data_generator_deprecated_20251024/
├── rl_data_generator.py    # 舊的 HDF5 數據生成器（~300 行）
├── __init__.py
└── README_DEPRECATED.md    # 本文件
```

### 代碼統計

- **總行數**: ~300 行
- **文件數**: 2 個 Python 文件
- **創建日期**: 2025-10-23
- **最後修改**: 2025-10-23

---

## 歷史價值

### 保留此歸檔的原因

1. **歷史記錄**: 記錄 Proposal 003 Phase 1 的初始實現
2. **設計演進**: 展示從基礎版本到完整版本的演進過程
3. **學術追溯**: 保留完整的開發歷史

---

## 功能演進

### Version 1: ml_data_generator（此歸檔版本）

**創建**: 2025-10-23
**功能**:
- 基礎 HDF5 數據生成
- 53-dim 狀態空間
- 簡單的 reward 計算

**限制**:
- ❌ 無 temporal features
- ❌ 無 D2 Integration
- ❌ 無 pool 分離

### Version 2: ml_training_data_generator（當前版本）

**創建**: 2025-10-24
**功能**:
- ✅ 77-dim 狀態空間（含 temporal features）
- ✅ TemporalFeatureCalculator（velocity, prediction）
- ✅ D2 Integration 支援
- ✅ Elite/Candidate pool 支援
- ✅ 完整的模組化設計

**HDF5 數據集**:
- 文件: `rl_training_dataset_temporal.h5`
- 生成日期: 2025-10-24 09:52
- 狀態維度: 77
- Train: 1,812 transitions (70%)
- Val: 388 transitions (15%)
- Test: 390 transitions (15%)
- Total: 2,590 transitions

---

## 如果需要恢復

如果未來需要恢復此代碼（不建議），執行：

```bash
# 恢復到 tools/
mv /home/sat/satellite/orbit-engine/tools/archive/ml_data_generator_deprecated_20251024 \
   /home/sat/satellite/orbit-engine/tools/ml_data_generator

# 但建議：直接使用 ml_training_data_generator
```

---

## 當前數據生成流程

### 正確的數據生成方式

```bash
# 使用 ml_training_data_generator（當前版本）
cd /home/sat/satellite/orbit-engine/tools/ml_training_data_generator
python generate_dataset.py \
    --stage5 ../../data/outputs/stage5/stage5_signal_analysis_elite_pool_*.json \
    --stage6 ../../data/outputs/stage6/stage6_research_optimization_elite_pool_*.json \
    --output ../../data/ml_training/rl_training_dataset_temporal.h5
```

**輸出**:
- 77-dim 狀態空間（含 temporal features）
- 支援 D2 Integration
- Train/Val/Test split
- 總計 2,590 transitions（Elite pool: 123 satellites）

---

**歸檔狀態**: ✅ 已歸檔，功能已由 ml_training_data_generator 完整取代
**維護狀態**: ❌ 不再維護
**建議操作**: 使用 ml_training_data_generator 生成訓練數據
