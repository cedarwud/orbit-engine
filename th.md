  ---
  ✅ 改進建議優先級

  P0 (必須修正)

  1. 在 Stage 4 概述中加入 final.md 的概念澄清
  ## 📖 概述與目標

  ⚠️ **核心概念** (引自 final.md):
  - 「候選衛星池」≠「任意時刻可見數」
  - ~2000 顆候選 = 整個軌道週期內「曾經可見」的衛星總數
  - 任意時刻只有 10-15 顆 Starlink 同時可見
  - Stage 4.2 必須優化選出 ~500 顆，確保時空分布均勻
  2. 修正 Stage 4.2 的「待實現」標記
  ⚠️ **實現狀態**:
  - 階段 4.1: ✅ 已實現
  - 階段 4.2: 🚧 **必要功能，待實現**

  🔴 **關鍵性**: Stage 4.2 是達成研究目標的**必要步驟**，不是可選優化

  P1 (建議修正)

  3. 修正 Stage 6 的「池規劃」表述
  #### 3. **動態衛星池驗證與監控** (非規劃)
  - 驗證 Stage 4.2 池優化結果
  - 遍歷 time_series[] 計算每個時間點的可見數
  - 生成覆蓋率報告
  4. 在 Stage 4/5 概述中明確 time_series[]
  **輸出**:
  - 可連線候選池 (~2000顆)
  - 每顆衛星包含完整 time_series[] (~95-220 時間點)
  - 每個時間點包含 is_connectable 狀態標記

   ---
  📊 總結：文檔改進建議優先級

  | 問題點                  | 嚴重度  | 改進方法                                   |
  |----------------------|------|----------------------------------------|
  | Stage 4.2 規劃時未重申關鍵概念 | 🔴 高 | 在 Line 102-110 增加「候選總數 vs 任意時刻可見數」的對比框 |
  | 數據結構與職責描述分離太遠        | 🔴 高 | 在階段 4.2 描述旁邊內聯數據結構範例                   |
  | Final.md 缺乏時間維度解釋    | 🟡 中 | 在計算規模說明中增加「驗證方法」偽代碼                    |
  | 「狀態分析」用詞模糊           | 🟡 中 | 改為「狀態驗證（基於時間序列遍歷）」                     |

 ---
  📝 文檔可以改進的地方（非常微小）

  1. Stage 4.2 部分

  當前寫法 (Line 108):
  ⚠️ **重要**: 階段 4.2 當前為文檔規劃階段，實際代碼尚未實現
  待實際執行測試後，將根據真實數據調整數字和策略

  可能的誤導:
  讀者可能誤以為「規劃階段」= 「可選功能」

  建議微調:
  ⚠️ **CRITICAL**: 階段 4.2 為**必要功能**，當前為文檔規劃階段，實際代碼尚未實現
  這是「動態衛星池」概念的核心算法步驟，缺少此步驟將無法保證「任意時刻維持目標數量可見」
  待實際執行測試後，將根據真實數據調整數字和策略

  2. Stage 5 部分

  當前寫法 (Line 14):
  **核心職責**: 基於可連線衛星的精確信號品質分析

  可能的歧義:
  「可連線衛星」可能被誤解為「當前時刻可連線」

  建議微調:
  **核心職責**: 基於可連線衛星池（含完整時間序列）的精確信號品質分析

  ---

    ✅ 修正建議

  修正方案：在文檔關鍵位置明確強調時間序列處理

  1. 概述部分 (Line 10-12):
  - **輸入**: Stage 4 的可連線衛星池
  - **輸出**: RSRP/RSRQ/SINR 信號品質數據
  + **輸入**: Stage 4 的可連線衛星池（包含完整時間序列，~95-220 時間點/衛星）
  + **輸出**: 每個時間點的 RSRP/RSRQ/SINR 時間序列信號品質數據
  + **處理方式**: 遍歷每顆衛星的時間序列，逐時間點計算信號品質

  2. 職責說明 (Line 78-82):
    #### 1. **3GPP 標準信號計算**
  + - **時間序列處理**: 對每顆衛星的 ~95-220 個時間點逐點計算
    - **RSRP (Reference Signal Received Power)**: 基於 3GPP TS 38.214
  + - **動態信號追蹤**: 追蹤信號品質隨時間變化（衛星移動導致）

  3. 輸出格式 (Line 451-486):
    'signal_analysis': {
        'satellite_id_1': {
  +         'time_series': [  # ← 時間序列數組
  +             {
  +                 'timestamp': '2025-09-27T08:00:00Z',
                    'signal_quality': {
                        'rsrp_dbm': -85.2,
                        ...
  +                 },
  +                 'is_connectable': True
  +             },
  +             # ... ~95-220 個時間點
  +         ]
  -         'signal_quality': {
  -             'rsrp_dbm': -85.2,  # 錯誤：單一時間點

  ---

    建議：在 Stage 6 文檔開頭加入明確的數據結構說明

  當前 Stage 6 Line 317 範例代碼:
  # ❌ 當前範例（錯誤實現）
  connectable_satellites = stage4_result.data['connectable_satellites']
  starlink_count = len(connectable_satellites['starlink'])  # 錯誤方法

  建議改為 (在範例前加入註解):
  # ⚠️ 重要數據結構說明:
  # connectable_satellites 包含完整時間序列，結構如下:
  # {
  #     'starlink': [
  #         {
  #             'satellite_id': 'STARLINK-1234',
  #             'time_series': [  # ← 完整時間序列，非單一時間點
  #                 {'timestamp': '...', 'is_connectable': True, ...},
  #                 {'timestamp': '...', 'is_connectable': False, ...},
  #                 ...
  #             ]
  #         },
  #         ...
  #     ]
  # }

  # ✅ 正確的池驗證方法: 遍歷所有時間點
  def verify_pool_maintenance_correct(stage4_result):
      connectable_satellites = stage4_result.data['connectable_satellites']

      # 收集所有時間戳
      all_timestamps = set()
      for sat in connectable_satellites['starlink']:
          for tp in sat['time_series']:
              all_timestamps.add(tp['timestamp'])

      # 逐時間點驗證
      coverage_stats = []
      for timestamp in sorted(all_timestamps):
          visible_count = 0
          for sat in connectable_satellites['starlink']:
              for tp in sat['time_series']:
                  if tp['timestamp'] == timestamp and tp['is_connectable']:
                      visible_count += 1
                      break

          coverage_stats.append({
              'timestamp': timestamp,
              'visible_count': visible_count,
              'target_met': 10 <= visible_count <= 15
          })

      return coverage_stats

  ---