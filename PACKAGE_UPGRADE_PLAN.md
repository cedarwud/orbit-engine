# 📦 Orbit Engine 成熟套件升級計畫

## 🎯 計畫目標

基於學術研究標準與可靠性考量，將 Orbit Engine 六階段處理系統中的自建組件替換為成熟的開源套件，以提升：
- ✅ **學術可靠性**：使用經過同行審查的專業實現
- ✅ **計算精度**：符合 IAU/3GPP 國際標準
- ✅ **維護效率**：減少自建組件的維護負擔
- ✅ **研究聚焦**：專注於創新點而非基礎工程

## 📊 現狀分析

### 當前實現評估
| 階段 | 現有實現 | 問題 | 風險等級 |
|------|----------|------|----------|
| **Stage 1** | 自建TLE解析器 | 複雜包裝層 | ⚠️ 中等 |
| **Stage 2** | 自建SGP4Calculator | 精度未驗證 | 🚨 高 |
| **Stage 3** | 自建座標轉換引擎 | 缺乏IAU標準驗證 | 🚨 高 |
| **Stage 4** | 自建衛星池分析 | 概念需澄清 | ⚠️ 中等 |
| **Stage 5** | 3GPP事件檢測 | 基本正確 | ✅ 低 |
| **Stage 6** | 缺乏RL標準接口 | 無gymnasium整合 | 🚨 高 |

### 成熟套件評估 (v2.0優化版)
| 套件類別 | 推薦套件 | 學術地位 | 用途 | 優先級 |
|----------|----------|----------|------|--------|
| **軌道計算** | skyfield + pyorbital | NASA JPL精度標準 | Stage 1-2 高精度替換 | 🔴 P0 |
| **軌道備選** | poliastro + astropy | 天體物理學標準 | 軌道機動與任務規劃 | 🟡 P1 |
| **TLE管理** | spacetrack + beyond | Space-Track.org官方 | TLE自動更新與ESA標準 | 🔴 P0 |
| **數值計算** | scipy + numpy | Python科學計算核心 | 信號處理與優化 | 🔴 P0 |
| **強化學習** | gymnasium + stable-baselines3 | RL社群標準 | Stage 6 增強 | 🔴 P0 |
| **實驗追蹤** | wandb + optuna | ML實驗標準 | 超參數優化與監控 | 🟡 P1 |
| **傳統ML** | scikit-learn | 機器學習標準庫 | 對比實驗與特徵工程 | 🟡 P1 |
| **視覺化** | plotly + dash + cesiumpy | 科學可視化標準 | 研究展示 | 🟢 P2 |
| **測試框架** | pytest + hypothesis | Python測試標準 | 單元測試與屬性測試 | 🟡 P1 |

#### **軌道計算套件選擇理由**
- **Skyfield優勢**:
  - 直接支援TLE格式，無需轉換
  - NASA JPL級精度（<10m誤差）
  - 專為衛星過境預測優化
  - 內建SGP4/SDP4傳播器
- **PyOrbital優勢**:
  - LEO衛星專用算法
  - 快速過境計算
  - 輕量級實現
- **Poliastro用途**:
  - 軌道機動計算（備選）
  - 任務規劃分析（進階需求）

## 🚀 升級計畫

### 階段一：基礎計算層升級 (2-3週)
**目標**：確保軌道計算與座標轉換的學術可靠性

#### Stage 1-2: 軌道計算升級
```bash
# 安裝核心套件 (優先使用Skyfield)
pip install skyfield pyorbital spacetrack astropy scipy

# 替換組件
❌ 移除：自建 SGP4Calculator
❌ 移除：自建 orbit-predictor 封裝
✅ 導入：skyfield.api.EarthSatellite (主要)
✅ 導入：pyorbital.orbital (LEO專用)
✅ 導入：astropy.time.Time
✅ 導入：scipy.optimize (優化算法)

# 備選方案（特殊需求時）
pip install poliastro  # 軌道機動計算時使用
```

**實施步驟**：
1. **Day 1-3**: Skyfield 高精度軌道傳播實現
   ```python
   from skyfield.api import load, EarthSatellite
   from pyorbital.orbital import Orbital

   # 使用Skyfield處理TLE（主要方案）
   ts = load.timescale()
   satellite = EarthSatellite(line1, line2, name, ts)

   # 各星座獨立軌道週期計算
   # Starlink: 90-95分鐘週期
   # OneWeb: 109-115分鐘週期
   t = ts.now()
   starlink_positions = [satellite.at(t + minutes) for minutes in range(95)]
   oneweb_positions = [satellite.at(t + minutes) for minutes in range(115)]

   # PyOrbital快速過境計算（輔助）
   orb = Orbital("STARLINK-1234", tle_file="starlink.tle")
   passes = orb.get_next_passes(t, 24, lon, lat, alt)
   ```

2. **Day 4-7**: 驗證數據一致性
   - 對比新舊實現輸出
   - 確保衛星池狀態計算正確
   - 驗證軌道週期分離計算

#### Stage 3: 座標轉換與信號處理升級
```bash
# 座標系統與數值計算專業庫 (astropy已在階段一安裝)
pip install scikit-learn

# 替換組件
❌ 移除：自建 SkyfieldCoordinateEngine
❌ 移除：自建 IERS/WGS84 管理器
✅ 導入：astropy.coordinates (座標轉換)
✅ 導入：scipy.signal (信號處理)
✅ 導入：scikit-learn.preprocessing (特徵標準化)
```

**實施步驟**：
1. **Day 8-12**: astropy 座標轉換實現
   ```python
   from astropy.coordinates import TEME, ITRS, EarthLocation
   from astropy.time import Time

   # 標準座標轉換鏈
   teme_coord = TEME(x, y, z, obstime=time, representation_type='cartesian')
   itrs_coord = teme_coord.transform_to(ITRS(obstime=time))
   geographic = EarthLocation.from_geocentric(*itrs_coord.cartesian.xyz)
   ```

2. **Day 13-15**: 信號處理與特徵工程增強
   ```python
   from scipy.signal import butter, filtfilt
   from sklearn.preprocessing import StandardScaler
   from sklearn.ensemble import RandomForestClassifier

   # RSRP/RSRQ信號濾波處理
   def filter_signal_quality(rsrp_data):
       b, a = butter(3, 0.1, 'low')
       return filtfilt(b, a, rsrp_data)

   # 特徵標準化 (改善RL訓練)
   scaler = StandardScaler()
   normalized_features = scaler.fit_transform(satellite_features)

   # 傳統ML基準建立 (對比RL效果)
   rf_baseline = RandomForestClassifier()
   rf_baseline.fit(features, handover_decisions)
   ```

3. **Day 16**: 精度驗證與效能測試
   - IAU 標準合規檢查
   - 座標轉換精度驗證 (目標: 0.5m)
   - 信號處理品質評估

### 階段二：衛星池分析優化 (1-2週)
**目標**：澄清動態衛星池概念，優化分析邏輯

#### Stage 4: 衛星池分析增強
**實施步驟**：
1. **Day 17-19**: 動態池概念實現
   ```python
   # 時空錯置池規劃驗證
   def validate_satellite_pool(constellation, orbital_period_minutes):
       """驗證動態衛星池狀態"""
       for time_point in range(orbital_period_minutes):
           visible_sats = count_visible_satellites(
               constellation=constellation,
               elevation_threshold=get_constellation_threshold(constellation),
               time=time_point
           )

           # 星座特定池狀態檢查
           if constellation == "starlink":
               assert 10 <= visible_sats <= 15
           elif constellation == "oneweb":
               assert 3 <= visible_sats <= 6
   ```

2. **Day 20-22**: 星座週期分離實現
   - Starlink: 90-95分鐘獨立計算
   - OneWeb: 109-115分鐘獨立計算
   - 覆蓋連續性驗證

### 階段三：強化學習標準化 (2-3週)
**目標**：建立標準RL訓練環境，支援多算法研究

#### Stage 6: RL 環境標準化
```bash
# RL 標準套件
pip install gymnasium stable-baselines3[extra]

# 可選研究套件
pip install cleanrl jupyter
```

**實施步驟**：
1. **Day 23-27**: Gymnasium 環境構建
   ```python
   import gymnasium as gym
   from gymnasium import spaces
   from stable_baselines3 import PPO, DQN, SAC

   class SatelliteHandoverEnv(gym.Env):
       """衛星換手環境標準接口"""
       def __init__(self):
           # 狀態空間: [衛星位置, RSRP, 仰角, 距離, 池狀態]
           self.observation_space = spaces.Box(
               low=-np.inf, high=np.inf, shape=(25,), dtype=np.float32
           )

           # 動作空間: [保持, 切換至候選1-5]
           self.action_space = spaces.Discrete(6)
   ```

2. **Day 28-32**: 多算法支援與傳統ML對比
   ```python
   # DQN/PPO/SAC/A3C 統一接口
   algorithms = {
       'DQN': DQN("MlpPolicy", env, verbose=1),
       'PPO': PPO("MlpPolicy", env, verbose=1),
       'SAC': SAC("MlpPolicy", env, verbose=1)
   }

   # 批量訓練與比較
   for name, model in algorithms.items():
       model.learn(total_timesteps=100000)
       model.save(f"satellite_handover_{name}")

   # 傳統ML基準對比
   from sklearn.ensemble import RandomForestClassifier
   from sklearn.metrics import classification_report

   rf_model = RandomForestClassifier(n_estimators=100)
   rf_model.fit(traditional_features, handover_labels)
   rf_predictions = rf_model.predict(test_features)

   print("Traditional ML vs RL Performance Comparison")
   print(classification_report(test_labels, rf_predictions))
   ```

### 階段四：視覺化增強 (1週)
**目標**：提升研究成果展示品質

#### 視覺化套件整合
```bash
# 科學可視化套件
pip install plotly dash cesiumpy jupyter
```

**實施步驟**：
1. **Day 33-35**: 3D軌道可視化
   ```python
   import plotly.graph_objects as go
   import cesiumpy

   # 衛星軌道3D渲染
   # 池狀態動態展示
   # 換手事件時序分析
   ```

2. **Day 36-37**: 研究儀表板
   - Dash 互動式監控面板
   - RL 訓練過程可視化
   - 3GPP 事件統計圖表

## 📋 實施時程規劃

### 總體時程：5-6週
```
Week 1: Stage 1-2 軌道計算升級 (poliastro + astropy + scipy基礎)
Week 2: Stage 3 座標轉換與信號處理升級 (astropy + scipy + scikit-learn)
Week 3: Stage 4 衛星池分析優化
Week 4: Stage 6 RL環境標準化 (gymnasium + stable-baselines3)
Week 5: 傳統ML對比實驗 + 視覺化增強
Week 6: 整合測試 + 文檔更新 + 最終驗證
```

### 每週里程碑
| 週次 | 主要成果 | 驗證標準 |
|------|----------|----------|
| Week 1 | poliastro軌道計算 + scipy優化 | 與現有輸出數據一致性 >95% |
| Week 2 | astropy座標轉換 + 信號處理 | IAU標準合規，精度 <0.5m，信號濾波效果 |
| Week 3 | 動態衛星池分析 | Starlink: 10-15顆, OneWeb: 3-6顆穩定維持 |
| Week 4 | RL標準環境 + 多算法支援 | gymnasium環境檢查通過，4種RL算法正常運行 |
| Week 5 | 傳統ML對比 + 視覺化完整 | RL vs ML性能報告，3D軌道渲染 |
| Week 6 | 系統整合 + 文檔更新 | 端到端六階段處理，完整套件升級文檔 |

## 💰 資源需求

### 人力需求
- **主要開發者**: 1人，6週全職投入
- **測試驗證**: 兼職，每週2-3天
- **文檔更新**: 兼職，每週1天

### 技術需求 (v2.0優化版)
```bash
# 核心軌道計算 (立即安裝 - P0優先級)
skyfield>=1.48              # NASA JPL精度軌道計算
pyorbital>=1.8              # LEO衛星過境預測
spacetrack>=1.2             # Space-Track.org API
astropy>=5.3                # 天文學標準
scipy>=1.10.0               # 數值計算與信號處理

# 強化學習環境 (P0優先級)
gymnasium>=0.29.0           # RL環境標準
stable-baselines3>=2.0.0    # RL算法庫
wandb                       # 實驗追蹤
optuna>=3.5                 # 超參數優化

# 機器學習與特徵工程 (P1優先級)
scikit-learn>=1.3.0         # 傳統ML與特徵工程
pandas>=2.0                 # 資料處理
numpy>=1.24                 # 數值運算

# 視覺化套件 (P2優先級)
plotly>=5.17.0              # 互動式圖表
dash>=2.14.0                # Web儀表板
cesiumpy>=0.3.3             # 3D地球渲染
czml3                       # Cesium資料格式

# 測試框架 (P1優先級)
pytest>=7.4                 # 單元測試
pytest-cov                  # 覆蓋率測試
pytest-benchmark            # 效能測試
hypothesis                  # 屬性測試

# 備選套件 (按需安裝)
poliastro>=0.17.0           # 軌道機動計算（特殊需求）
beyond>=0.7                 # ESA標準支援
cleanrl                     # 研究友好RL (深度客製化)
```

#### **一鍵安裝指令**
```bash
# 立即安裝核心套件 (v2.0優化版)
pip install skyfield pyorbital spacetrack astropy scipy scikit-learn gymnasium stable-baselines3[extra] plotly dash cesiumpy

# 實驗追蹤與優化
pip install wandb optuna

# 測試框架
pip install pytest pytest-cov pytest-benchmark hypothesis

# 備選與可選套件
pip install poliastro  # 軌道機動計算（按需）
pip install cleanrl    # 研究友好RL（按需）
pip install beyond     # ESA標準支援（可選）
```

### 硬體需求
- **CPU**: 現有配置足夠 (非即時計算)
- **記憶體**: 8GB+ (處理大型衛星數據)
- **儲存**: 10GB+ (新套件 + 模型儲存)

## 🎯 預期成果

### 量化指標
- **計算精度提升**: 軌道預測誤差從~100m降至<10m (使用Skyfield)
- **可靠性提升**: 基礎計算精度從未知提升至NASA JPL標準級別
- **維護效率**: 自建組件代碼量減少60%+
- **開發速度**: 新功能開發時間縮短40%+
- **效能提升**: LEO衛星過境計算速度提升5x (使用PyOrbital)
- **標準合規**: 100% gymnasium + 3GPP 標準接口

### 研究能力增強
1. **軌道計算**: skyfield + pyorbital NASA JPL級精度保證
2. **TLE管理**: spacetrack 自動更新 + beyond ESA標準支援
3. **數值分析**: scipy 信號處理與優化算法支援
4. **機器學習**: scikit-learn 傳統ML基準 + stable-baselines3 先進RL
5. **實驗管理**: wandb 實驗追蹤 + optuna 超參數優化
6. **對比研究**: RL vs 傳統ML性能評估能力
7. **特徵工程**: scikit-learn 標準化預處理管道
8. **視覺化**: plotly + cesiumpy + czml3 專業級研究成果展示
9. **質量保證**: pytest + hypothesis 完整測試覆蓋
10. **國際接軌**: 100% 符合學術界標準工具鏈

### 長期價值
- ✅ **學術發表**: 符合國際期刊投稿標準
- ✅ **研究擴展**: 易於添加新功能和算法
- ✅ **社群支援**: 受益於開源社群維護
- ✅ **技術傳承**: 標準化實現易於傳授

## ⚠️ 風險評估與應對

### 技術風險
| 風險 | 影響 | 機率 | 應對策略 |
|------|------|------|----------|
| 套件相容性問題 | 中等 | 低 | 版本鎖定，分階段測試 |
| 效能回歸 | 低 | 中等 | 效能基準測試，優化配置 |
| 精度差異 | 高 | 低 | 嚴格驗證標準，對比測試 |
| 學習成本 | 中等 | 中等 | 充分文檔，範例代碼 |

### 時程風險
- **延遲因子**: 新套件學習曲線
- **緩解措施**: 預留緩衝時間，分階段實施
- **應急計畫**: 優先級排序，核心功能優先

## 📚 參考資料

### 學術依據
1. **poliastro**: Lizárraga-Celaya, C. et al. (2020). "poliastro: An Astrodynamics Library in Python"
2. **astropy**: The Astropy Collaboration (2022). "The Astropy Project: Sustaining and Growing a Community-oriented Open-source Project"
3. **gymnasium**: Brockman, G. et al. (2016). "OpenAI Gym" (Gymnasium is the maintained fork)

### 技術文檔
- [poliastro Documentation](https://docs.poliastro.space/)
- [Astropy Coordinates](https://docs.astropy.org/en/stable/coordinates/)
- [Gymnasium Environment Creation](https://gymnasium.farama.org/)
- [Stable-Baselines3 User Guide](https://stable-baselines3.readthedocs.io/)

---

**版本**: v2.0 (優化版)
**建立日期**: 2025-01-15
**更新日期**: 2025-01-29
**負責人**: [待指定]
**核准狀態**: 待審核

**結論**: 此升級計畫將顯著提升 Orbit Engine 的學術可靠性與研究能力，確保符合國際標準，為後續創新研究奠定堅實基礎。建議優先執行 Stage 1-3 的基礎計算升級，以確保研究數據的可靠性。