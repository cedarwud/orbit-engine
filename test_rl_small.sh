#!/bin/bash
# 小規模 RL 訓練測試（50 衛星，7 天）

cd /home/sat/satellite/orbit-engine

# 設置測試模式環境變數
export ORBIT_ENGINE_TEST_MODE=1  # 允許在非容器環境執行
export ORBIT_ENGINE_STAGE2_PERFORMANCE___TESTING_MODE___ENABLED=true
export ORBIT_ENGINE_STAGE2_PERFORMANCE___TESTING_MODE___SATELLITE_SAMPLE_SIZE=50

# 執行完整 RL 訓練數據生成（Stage 1-6）
# Stage 6 會生成 A4/D2 換手事件供 handover-rl 使用
./scripts/generate_rl_training_data.sh --stages 1-6
