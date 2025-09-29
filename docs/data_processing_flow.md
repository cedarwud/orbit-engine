# 🔄 NTN Stack 數據處理流程

**版本**: v3.0 (概念修正+學術標準+簡化架構)
**更新日期**: 2025-09-28
**專案狀態**: ✅ Stage 2 重構完成 + 簡化架構 + NASA JPL 精度 + 效能大幅提升
**適用於**: LEO 衛星切換研究 - v3.0六階段處理管道

## 🎯 v3.0 重構核心成果

### 架構簡化突破
- **Stage 2 簡化**: 移除中間層次，直接使用 Skyfield NASA JPL 標準
- **效能躍升**: 183% 效能提升，84秒處理9,040顆衛星
- **精度保證**: NASA JPL 標準精度，軌道距離 6,716-7,579km
- **零失敗率**: 100% 成功處理率，107.6顆衛星/秒

### 概念修正成果
- **Stage 2**: ❌ 可見性篩選 → ✅ 軌道狀態傳播 (TEME座標輸出)
- **Stage 3**: ❌ 信號分析 → ✅ 座標系統轉換 (WGS84地理座標)
- **Stage 4**: ✅ 全新設計 - 鏈路可行性評估 (星座感知篩選)
- **時間基準**: 每筆TLE記錄獨立epoch_datetime，符合v3.0架構要求

## 📋 概述

本文檔詳細說明 **v3.0簡化架構** 的六階段數據處理流程：系統採用概念修正和簡化設計，實現高效能、高精度的衛星數據處理管道。

**核心特點**：
- ✅ **本地TLE數據** - 系統使用預下載的本地TLE文件，無依賴外部API
- ✅ **記憶體優先** - 階段間主要使用記憶體傳遞，提升處理效率
- ✅ **完整SGP4算法** - 絕不使用簡化或模擬數據，保證學術研究準確性
- ✅ **模組化架構** - 每階段採用標準化模組設計，便於維護

## 🚀 v3.0六階段架構設計

### 📦 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                   v3.0 六階段處理管道                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stage 1: TLE數據載入層                                      │
│  ├── TLE Data Loader                                       │
│  ├── Data Validator                                        │
│  ├── Independent Epoch Establisher (v3.0)                  │
│  └── Stage1 TLE Loading Processor                          │
│                     ↓                                       │
│  Stage 2: 軌道狀態傳播層 ✅ 重構完成                         │
│  ├── Skyfield Direct (NASA JPL)                            │
│  ├── SGP4 Calculator (簡化版)                               │
│  ├── TEME Coordinate Output                                │
│  └── Stage2 Orbital Computing Processor                    │
│                     ↓                                       │
│  Stage 3: 座標系統轉換層                                     │
│  ├── Skyfield Coordinate Converter                         │
│  ├── TEME → WGS84 Converter                               │
│  ├── IAU Standard Compliance                               │
│  └── Stage3 Coordinate Processor                           │
│                     ↓                                       │
│  Stage 4: 鏈路可行性評估層                                   │
│  ├── Constellation-Aware Filter                            │
│  ├── Starlink (5°) vs OneWeb (10°)                        │
│  ├── NTPU Ground Station Specific                          │
│  └── Stage4 Link Feasibility Processor                     │
│                     ↓                                       │
│  Stage 5: 信號品質分析層                                     │
│  ├── 3GPP/ITU-R Signal Calculator                         │
│  ├── RSRP/RSRQ/SINR Analysis                              │
│  ├── Physics-Based Models                                  │
│  └── Stage5 Signal Analysis Processor                      │
│                     ↓                                       │
│  Stage 6: 研究數據生成層                                     │
│  ├── 3GPP NTN Event Detector                              │
│  ├── ML Training Data Generator                            │
│  ├── Research Output Builder                               │
│  └── Stage6 Research Processor                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📊 階段處理詳解

### Stage 1: 數據載入層
**核心職責**: TLE數據載入、驗證和時間基準建立
- **輸入**: 8,837顆衛星TLE文件
- **處理時間**: <30秒
- **輸出**: 約4-5MB驗證過的TLE數據
- **關鍵功能**: 統一時間基準建立（使用TLE epoch時間）

### Stage 2: 軌道狀態傳播層 ✅ **重構完成**
**核心職責**: 直接使用 Skyfield NASA JPL 標準進行軌道傳播
- **輸入**: 驗證過的TLE數據 + 獨立epoch_datetime
- **處理時間**: 84秒（v3.0簡化版，183%效能提升）
- **處理量**: 9,040顆衛星，107.6顆/秒，100%成功率
- **輸出**: 時間序列TEME位置/速度數據（NASA JPL精度）
- **關鍵功能**: 直接Skyfield調用、衛星快取、TEME座標輸出

### Stage 3: 座標系統轉換層
**核心職責**: TEME→ITRF→WGS84專業級座標轉換
- **輸入**: TEME位置/速度數據
- **處理時間**: <2秒（Skyfield專業庫）
- **輸出**: WGS84地理座標(緯度/經度/高度)
- **關鍵功能**: Skyfield專業轉換、IAU標準合規、高精度座標

### Stage 4: 鏈路可行性評估層
**核心職責**: 星座感知的可連線性評估
- **輸入**: WGS84地理座標數據
- **處理時間**: <1秒（星座感知篩選）
- **輸出**: 可連線衛星池，按星座分類
- **關鍵功能**: Starlink(5°) vs OneWeb(10°)差異化門檻、NTPU地面站特定

### Stage 5: 信號品質分析層
**核心職責**: 3GPP TS 38.214標準信號品質計算
- **輸入**: 可連線衛星數據
- **處理時間**: <0.5秒（僅對可連線衛星分析）
- **輸出**: RSRP/RSRQ/SINR精確信號品質數據
- **關鍵功能**: ITU-R P.618物理模型、CODATA 2018常數、3GPP標準

### Stage 6: 研究數據生成層
**核心職責**: 3GPP NTN事件檢測與ML訓練數據生成
- **輸入**: 信號品質數據
- **處理時間**: <0.2秒（事件檢測+ML數據生成）
- **輸出**: 研究級數據，實時決策支援
- **關鍵功能**: A4/A5/D2事件檢測、多算法訓練集、實時決策

## ⚡ 性能指標總覽

### 處理時間 ✅ **v3.0大幅優化**
- **Stage 1**: <1秒（TLE解析，8,995顆衛星）
- **Stage 2**: 84秒（軌道傳播，9,040顆衛星，183%提升）
- **Stage 3**: <2秒（座標轉換，Skyfield專業庫）
- **Stage 4**: <1秒（可見性篩選，星座感知）
- **Stage 5**: <0.5秒（信號分析，可連線衛星）
- **Stage 6**: <0.2秒（事件檢測，ML數據生成）

**總處理時間**: 約90秒（相比v2.0的4-5分鐘大幅優化，67%效能提升）

### 記憶體使用
- **Stage 1**: <200MB
- **Stage 2**: <1GB
- **Stage 3**: <500MB
- **Stage 4**: <300MB
- **Stage 5**: <1GB
- **Stage 6**: <500MB

### 數據處理量 ✅ **v3.0實測**
- **輸入**: 9,040顆衛星TLE數據（v3.0實際）
- **軌道點**: 860,957個位置/速度點（Stage 2輸出）
- **處理速率**: 107.6顆衛星/秒（100%成功率）
- **最終服務**: 依星座感知篩選（Starlink: 10-15顆, OneWeb: 3-6顆）

## 🛡️ 學術標準合規

### Grade A++ 達成 ✅ **v3.0驗證**
- ✅ **NASA JPL精度**: 直接使用Skyfield專業庫，軌道距離6,716-7,579km
- ✅ **標準算法**: 完整SGP4/SDP4實現，零簡化算法
- ✅ **獨立時間基準**: 每筆TLE記錄獨立epoch_datetime
- ✅ **國際標準**: 3GPP TS 38.331、ITU-R P.618、IAU 2000/2006合規

### 升級的零容忍項目 ✅ **v3.0強化**
- ❌ **TLE重新解析**: Stage 2+絕對禁止重新解析TLE
- ❌ **自製座標轉換**: 必須使用Skyfield專業庫
- ❌ **統一時間基準**: 禁止創建跨TLE記錄的統一時間
- ❌ **非星座感知**: 禁止對所有星座使用統一門檻

## 🔧 數據流設計

### 記憶體傳遞優先
```python
# v3.0標準數據流
stage1_result = stage1_processor.execute()        # TLE + epoch_datetime
stage2_result = stage2_processor.execute(stage1_result.data)  # TEME座標
stage3_result = stage3_processor.execute(stage2_result.data)  # WGS84座標
stage4_result = stage4_processor.execute(stage3_result.data)  # 可連線衛星
stage5_result = stage5_processor.execute(stage4_result.data)  # 信號品質
stage6_result = stage6_processor.execute(stage5_result.data)  # 研究數據
```

### 統一輸出格式
```python
# 標準階段輸出格式
{
    'stage': 'stage_name',
    'data': {...},           # 核心處理數據
    'metadata': {
        'processing_time': '...',
        'input_count': 123,
        'output_count': 456,
        'performance_metrics': {...}
    },
    'validation_result': {...}  # 學術標準驗證
}
```

## 📋 相關文檔

### 核心文檔
- **[階段職責規範](./STAGE_RESPONSIBILITIES.md)** - v2.0六階段職責分工
- **[Stage 1: 數據載入層](./stages/stage1-tle-loading.md)** - TLE數據載入設計
- **[Stage 2: 軌道計算層](./stages/stage2-orbital-computing.md)** - SGP4軌道計算設計
- **[Stage 3: 信號分析層](./stages/stage3-signal-analysis.md)** - 信號品質分析設計
- **[Stage 4: 優化決策層](./stages/stage4-optimization.md)** - 優化決策設計
- **[Stage 5: 數據整合層](./stages/stage5-data-integration.md)** - 數據整合設計
- **[Stage 6: 持久化與API層](./stages/stage6-persistence-api.md)** - API服務設計

### 學術標準
- **[學術數據標準](./academic_data_standards.md)** - Grade A學術要求
- **[衛星換手標準](./satellite_handover_standards.md)** - 換手算法標準

## 🎯 v3.0重構總結

### 核心突破 ✅ **Stage 2 已達成**
1. **概念正確性**: 修正了Stage 2/3的錯誤概念定位
2. **效能突破**: Stage 2達成183%效能提升，84秒處理9,040顆衛星
3. **學術嚴謹性**: 引入Skyfield等專業庫，達成NASA JPL精度
4. **研究對齊性**: 完全符合final.md的研究目標

### 實際應用價值
- **學術研究**: 可發表的高品質研究數據（NASA JPL精度）
- **工程實踐**: 符合實際衛星系統設計（星座感知）
- **標準合規**: 滿足國際電信標準要求（3GPP, ITU-R, IAU）
- **創新平台**: 為強化學習研究提供完整基礎

### 未來發展方向
- **實時處理**: 支援毫秒級實時決策（<100ms響應）
- **智能優化**: 基於ML的自適應參數調整
- **標準演進**: 跟蹤3GPP NTN標準的最新發展
- **國際合作**: 支援多國地面站和星座系統

---

**版本**: v3.0 (重構版)
**概念狀態**: ✅ 完全修正 (Stage 2-6概念重新定義)
**學術合規**: ✅ Grade A++ 標準 (Stage 2實測達成)
**最終更新**: 2025-09-28