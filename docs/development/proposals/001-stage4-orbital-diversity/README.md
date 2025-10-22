# Proposal 001: Stage 4 軌道面多樣性約束

**狀態**: 📋 待審核
**創建日期**: 2025-10-22
**作者**: Orbit Engine 開發團隊
**預計工期**: 3-4 小時
**難度**: ⭐⭐ 中等

---

## 🎯 快速概覽

**問題**: Stage 4 池優化算法僅優化時間覆蓋，導致衛星聚集於少數軌道面（19 個面，Gini 0.429）

**解決方案**: 實施兩階段選擇算法 - 階段 1 均勻採樣 24 個軌道面，階段 2 Greedy 填補覆蓋缺口

**影響範圍**:
- ✅ 改進 RL 訓練數據質量
- ✅ 對齊學術論文方法論
- ✅ 穩定換手頻率

**關鍵指標**:

| 指標 | 當前 | 目標 | 改善 |
|------|------|------|------|
| 軌道面數量 | 19 | 24+ | +26% |
| Gini 係數 | 0.429 | <0.3 | -30% |
| 衛星總數 | 98 | 48-72 | -27% ~ -51% |
| 時間覆蓋率 | 96.3% | ≥93% | -3% (可接受) |

---

## 📚 文檔結構

本提案包含以下文檔：

### 主要文檔

1. **[00-proposal.md](00-proposal.md)** - 完整計劃書
   - 問題陳述與根因分析
   - 目標與成功標準
   - 解決方案設計（三個方案對比）
   - 實施計劃（5 個階段）
   - 驗證計劃
   - 風險評估

2. **[01-technical-design.md](01-technical-design.md)** - 技術設計細節
   - 算法偽代碼
   - 數據結構設計
   - API 接口定義
   - 配置參數說明

3. **[02-test-plan.md](02-test-plan.md)** - 測試計劃
   - 單元測試用例
   - 整合測試場景
   - 性能測試
   - 驗收標準

4. **[03-api-changes.md](03-api-changes.md)** - API/接口變更
   - 配置文件變更
   - 函數簽名變更
   - 數據格式變更
   - 向後兼容性說明

### 補充資料

5. **diagrams/** - 圖表與流程圖
   - `algorithm-flow.mermaid` - 兩階段算法流程圖
   - `data-flow.mermaid` - TLE 數據流
   - `raan-distribution-before.png` - 改進前 RAAN 分佈
   - `raan-distribution-after.png` - 改進後 RAAN 分佈（預期）

6. **implementation/** - 實施過程文檔
   - `phase1-log.md` - Phase 1 實施記錄（待填寫）
   - `phase2-log.md` - Phase 2 實施記錄（待填寫）
   - `phase3-log.md` - Phase 3 實施記錄（待填寫）
   - `phase4-log.md` - Phase 4 驗證記錄（待填寫）
   - `phase5-log.md` - Phase 5 調優記錄（待填寫）

---

## 🚀 快速開始

### 閱讀順序（審核者）

1. **快速了解** → 本 README
2. **詳細計劃** → [00-proposal.md](00-proposal.md) 第 1-3 節
3. **技術細節** → [01-technical-design.md](01-technical-design.md)
4. **測試驗證** → [02-test-plan.md](02-test-plan.md)
5. **影響評估** → [03-api-changes.md](03-api-changes.md)

### 實施順序（開發者）

1. **審核通過後** → 創建 feature branch `feature/stage4-orbital-diversity`
2. **Phase 1** → 實施 TLE 讀取與 RAAN 解析（30 分鐘）
3. **Phase 2** → 實施軌道面代表選擇（45 分鐘）
4. **Phase 3** → 重構兩階段優化主流程（60 分鐘）
5. **Phase 4** → 運行 Stage 4 驗證效果（60 分鐘）
6. **Phase 5** → 參數調優（如需要，30 分鐘）

---

## 🔍 核心技術方案

### 當前算法（有問題）

```python
# Greedy Set Cover - 只優化時間覆蓋
for satellite in candidates:
    contribution = count_uncovered_timepoints(satellite)
    if contribution > best:
        best_satellite = satellite
```

**問題**: 可能選到來自相同軌道面的衛星

### 改進算法（兩階段）

```python
# 階段 1: 均勻採樣軌道面（保證多樣性）
representatives = select_raan_representatives(
    candidates,
    target_planes=24  # 確保 24 個軌道面
)

# 階段 2: Greedy 填補覆蓋缺口（優化覆蓋率）
while not coverage_achieved(selected):
    best = select_next_best_satellite(
        candidates,
        max_per_plane=3  # 限制每面最多 3 顆
    )
    selected.append(best)
```

**優勢**: 同時保證軌道面多樣性和時間覆蓋率

---

## 📊 預期結果

### 改進前（2025-10-22 實測）

```
✅ 時間覆蓋: 96.3% (優秀)
❌ 空間分佈:
   - 19 個軌道面（不足）
   - Gini 0.429（中度聚類）
   - 部分軌道面 12 顆衛星（過度）
```

### 改進後（預期）

```
✅ 時間覆蓋: 93-98% (良好)
✅ 空間分佈:
   - 24 個軌道面（對齊論文）
   - Gini < 0.3（均勻分佈）
   - 每面 2-3 顆（合理）
```

### 與論文對比

| 配置 | 論文典型 | 改進前 | 改進後 | 達標 |
|------|---------|--------|--------|------|
| 衛星數 | 48-50 | 98 | 48-72 | ✅ |
| 軌道面 | ~24 | 19 | 24 | ✅ |
| 每面數 | 2 | 5.2 | 2-3 | ✅ |

---

## ⚠️ 風險與緩解

### 主要風險

1. **覆蓋率下降** (概率: 中, 影響: 中)
   - 緩解: 階段 2 Greedy 保證覆蓋率 ≥ 93%
   - 監控: 單元測試中設置下限

2. **破壞下游** (概率: 低, 影響: 高)
   - 緩解: 保持輸出格式不變
   - 驗證: 運行 Stage 5, 6 測試

3. **參數調優耗時** (概率: 中, 影響: 中)
   - 緩解: 提供預設值（24 面 × 3 顆）
   - 回滾: 配置開關 `enabled: false`

### 回滾計劃

```yaml
# 立即禁用新算法
orbital_diversity:
  enabled: false
```

或代碼回滾：
```bash
git revert <commit-hash>
```

---

## 📅 時間線

| 階段 | 預計時間 | 狀態 |
|------|---------|------|
| 文檔撰寫 | 2 小時 | ✅ 完成 |
| 審核批准 | 1-2 天 | 📋 待審核 |
| Phase 1 實施 | 30 分鐘 | ⏳ 待開始 |
| Phase 2 實施 | 45 分鐘 | ⏳ 待開始 |
| Phase 3 實施 | 60 分鐘 | ⏳ 待開始 |
| Phase 4 驗證 | 60 分鐘 | ⏳ 待開始 |
| Phase 5 調優 | 30 分鐘 | ⏳ 待開始 |
| **總計** | **5-6 小時** | - |

---

## ✅ 審核檢查清單

**技術審核**:
- [ ] 算法邏輯正確性（架構師）
- [ ] 性能影響可接受（< 10 秒增加）
- [ ] 代碼複雜度合理（~200 行）

**學術審核**:
- [ ] 符合學術標準（有文獻引用）
- [ ] 對齊論文方法論
- [ ] 不破壞研究結果可比性

**業務審核**:
- [ ] 不影響下游 Stage 5, 6
- [ ] 配置可選（向後兼容）
- [ ] 文檔完整

**批准簽字**:
- [ ] 技術負責人: ___________
- [ ] 研究負責人: ___________
- [ ] 項目經理: ___________

---

## 📞 聯繫方式

**問題與討論**: 請在對應文檔中創建 comments 或提交 Issue

**實施更新**: 填寫 `implementation/phaseN-log.md`

---

**最後更新**: 2025-10-22
**版本**: v1.0
