1. 程式唯一
請仔細檢查被歸類在階段一執行會使用到的所有檔案中，是否所有檔案中的程式都有被使用?是否所有邏輯都只有一個執行方法，沒有類似、重複、過時的程式，也沒有硬編碼、模擬數據、簡化算法等問題，或是檔案中存在不屬於階段一的程式，是其他階段在使用的程式?本來就定義是共用的程式或是檔案除外，整個階段一的程式都有符合 @docs/stages/stage1-specification.md 的描述

以及 @docs/ACADEMIC_STANDARDS.md 的標準，也有符合 @docs/final.md 中預期六階段之中的分工

2. 文件-程式同步
請仔細檢查目前六階段中的階段一的文件 @docs/stages/stage1-specification.md 跟程式 @scripts/run_six_stages_with_validation.py --stage 1 是否同步，沒有哪一個超前或落後的狀況

3. 程式沒有硬編碼
請再檢查階段四的程式中是否存在任何硬編碼、模擬數據、簡化算法，不能只用關鍵字搜尋，要實際查看演算法跟參數，請參考
  @docs/ACADEMIC_STANDARDS.md 跟 @docs/CODE_COMMENT_TEMPLATES.md 的標準

4. 程式跟驗證快照同步
請再仔細確認階段一的程式跟驗證快照的內容是否同步

5. 驗證快沒有硬編碼
請再檢查階段六的驗證快照中是否存在任何硬編碼、模擬數據、簡化算法，不能只用關鍵字搜尋，要實際查看演算法跟參數，請參考
  @docs/ACADEMIC_STANDARDS.md 跟 @docs/CODE_COMMENT_TEMPLATES.md 的標準

6. 回退機制
請再仔細檢查階段四的程式是否有任何回退機制，整個專案要使用 Fail-Fast 方式來開發
請再仔細檢查階段四的驗證快照是否有任何回退機制，整個專案要使用 Fail-Fast 方式來開發
