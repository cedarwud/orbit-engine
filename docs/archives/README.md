# 📚 文檔歷史歸檔區

## 📋 目錄結構

### `v2.0/` - v2.0架構文檔歷史版本
- `STAGE_RESPONSIBILITIES.md` - v2.0階段責任分工規範
- **狀態**: 已廢棄，僅供歷史參考
- **說明**: v2.0定義與當前v3.0實現不符，已統一遷移到v3.0架構

### `deprecated/` - 廢棄的重複文檔
- `stage4-optimization.md` - 舊版Stage 4定義 (優化決策層)
- `stage5-data-integration.md` - 舊版Stage 5定義 (數據整合層)
- `stage6-persistence-api.md` - 舊版Stage 6定義 (持久化與API層)
- **狀態**: 已廢棄，被v3.0新定義取代

### `stage1/` - Stage 1歷史開發文檔
- 保留Stage 1開發過程的歷史文檔

## 🎯 v3.0當前架構 (權威定義)

### 主要文檔位置
- **權威總覽**: [`/docs/stages/STAGES_OVERVIEW.md`](../stages/STAGES_OVERVIEW.md)
- **詳細規格**: [`/docs/stages/stage*-*.md`](../stages/)

### v3.0正確的階段定義
1. **Stage 1**: TLE數據載入層
2. **Stage 2**: 軌道狀態傳播層 (SGP4計算，TEME輸出)
3. **Stage 3**: 座標系統轉換層 (TEME→WGS84，Skyfield專業庫)
4. **Stage 4**: 鏈路可行性評估層 (星座感知篩選)
5. **Stage 5**: 信號品質分析層 (3GPP/ITU-R標準)
6. **Stage 6**: 研究數據生成與優化層 (3GPP事件+ML)

## ⚠️ 重要提醒

### 開發請使用v3.0文檔
- ❌ **請勿參考**本歸檔區的任何文檔進行開發
- ✅ **請使用**`/docs/stages/`目錄下的v3.0最新文檔
- ✅ **權威總覽**見`STAGES_OVERVIEW.md`

### 文檔整理歷史
- **整理日期**: 2025-09-28
- **整理原因**: 消除v2.0與v3.0架構的版本混亂
- **整理範圍**: 移除衝突定義，保留歷史參考

---

**注意**: 本歷史歸檔僅供文檔演進參考，請勿用於實際開發！