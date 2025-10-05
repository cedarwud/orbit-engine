1. 文件-程式同步
請仔細檢查目前六階段中的階段一的文件 @docs/stages/stage1-specification.md 跟程式 @scripts/run_six_stages_with_validation.py --stage 1 是否同步，沒有哪一個超前或落後的狀況

2. 程式唯一
請仔細檢查 @src/stages/stage1_orbital_calculation/ 中的所有程式是否都沒有重複、過時、沒有在使用的，使用
  @scripts/run_six_stages_with_validation.py --stage 1 執行時，只會有一組程式在執行，不存在多個執行入口

 請仔細檢查 @src/stages/stage2_orbital_computing/ 中的所有程式是否都沒有重複、過時、沒有在使用的，使用
  @scripts/run_six_stages_with_validation.py --stage 2 執行時，只會有一組程式在執行，不存在多個執行入口

請仔細檢查 @src/stages/stage3_coordinate_transformation/ 中的所有程式是否都沒有重複、過時、沒有在使用的，使用
  @scripts/run_six_stages_with_validation.py --stage 3 執行時，只會有一組程式在執行，不存在多個執行入口

請仔細檢查 @src/stages/stage4_link_feasibility/ 中的所有程式是否都沒有重複、過時、沒有在使用的，使用
  @scripts/run_six_stages_with_validation.py --stage 4 執行時，只會有一組程式在執行，不存在多個執行入口

請仔細檢查 @src/stages/stage5_signal_analysis/ 中的所有程式是否都沒有重複、過時、沒有在使用的，使用
  @scripts/run_six_stages_with_validation.py --stage 5 執行時，只會有一組程式在執行，不存在多個執行入口

請仔細檢查 @src/stages/stage6_research_optimization/ 中的所有程式是否都沒有重複、過時、沒有在使用的，使用
  @scripts/run_six_stages_with_validation.py --stage 6 執行時，只會有一組程式在執行，不存在多個執行入口

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
