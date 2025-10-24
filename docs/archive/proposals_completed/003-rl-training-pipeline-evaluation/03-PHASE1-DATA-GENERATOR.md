# Proposal 003: Phase 1 - ML Data Generator

**文檔版本**: v2.0
**最後更新**: 2025-10-23
**預計時間**: 2 天

---

## 📋 概述

Phase 1 實現獨立的 ML Training Data Generator，將 Stage 6 JSON 輸出轉換為 RL 訓練數據格式（HDF5）。

**關鍵設計**:
- ✅ **獨立工具** - 不修改 Stage 6 輸出
- ✅ **讀取 JSON** - 解析 Stage 6 標準格式
- ✅ **生成 HDF5** - 輸出訓練數據集

---

## 🎯 目標

1. 從 Stage 6 JSON 提取 (state, action, reward, next_state) 元組
2. 生成 HDF5 格式的訓練數據集
3. 支持 train/val/test 分割
4. 確保 12 種場景變體均衡分佈

---

## 📦 模組設計

詳見 [02-ARCHITECTURE.md](02-ARCHITECTURE.md) Module 1

### 核心組件

1. **JSON Parser** - 解析 Stage 6 輸出
2. **State Extractor** - 提取 RL 狀態
3. **Reward Calculator** - 計算獎勵函數
4. **Dataset Builder** - 構建 HDF5 數據集

---

## ⏱️ 實施計畫

詳見 [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) Phase 1

**Day 1**: JSON Parser + 數據格式
**Day 2**: State Extractor + Reward Calculator + Dataset Builder

---

## ✅ 驗收標準

- [ ] ML Data Generator 正確轉換 Stage 6 JSON
- [ ] HDF5 數據集格式正確
- [ ] 12 種場景變體均衡分佈（每種 ~8.3%）
- [ ] 數據集分割比例正確（70/15/15）
- [ ] 單元測試覆蓋率 > 80%
- [ ] 所有函數有 SOURCE 標註

---

**文檔狀態**: ✅ 完成（簡化版）
**詳細設計**: 參見架構和實施計畫文檔
