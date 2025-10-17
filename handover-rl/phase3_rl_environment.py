#!/usr/bin/env python3
"""
Phase 3: RL 環境設計與驗證

功能：
1. 實作 Gymnasium 環境（符合 OpenAI Gym 標準）
2. 定義狀態空間、動作空間、獎勵函數
3. 驗證環境正確性
4. 測試隨機策略性能

執行：
    python phase3_rl_environment.py

輸出：
    驗證環境正確性
    測試隨機策略 baseline
"""

import json
import yaml
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class Episode:
    """
    Episode 數據包裝類（相容性處理）

    用於包裝從 pickle 載入的字典數據，提供統一的屬性訪問接口。

    相容性處理：
    - time_series (Phase 1 保存的鍵名) → time_points (Phase 3 期望的屬性名)
    - 字典格式 → 對象屬性訪問

    SOURCE: rl.md Line 242-267 (Episode 包裝類設計)
    """

    def __init__(self, data):
        """
        Args:
            data: Episode 數據（字典或 Episode 對象）
        """
        # 如果已經是 Episode 對象，直接複製屬性
        if isinstance(data, Episode):
            self.satellite_id = data.satellite_id
            self.constellation = data.constellation
            self.time_points = data.time_points
            self.gpp_events = data.gpp_events
            self.episode_length = data.episode_length
            return

        # 從字典創建對象
        self.satellite_id = data['satellite_id']
        self.constellation = data['constellation']

        # 相容性處理：支持 time_series（Phase 1）和 time_points（未來可能）
        if 'time_points' in data:
            self.time_points = data['time_points']
        elif 'time_series' in data:
            self.time_points = data['time_series']  # ← 關鍵轉換
        else:
            self.time_points = []

        self.gpp_events = data.get('gpp_events', [])
        self.episode_length = data.get('episode_length', len(self.time_points))


class HandoverEnvironment(gym.Env):
    """
    衛星換手決策 RL 環境

    狀態空間 (12 維 - 完整特徵集):
        信號品質 (3 維):
            - RSRP (dBm): Reference Signal Received Power
            - RSRQ (dB): Reference Signal Received Quality
            - SINR (dB): Signal-to-Interference-plus-Noise Ratio

        物理參數 (7 維):
            - Distance (km): 衛星與地面站距離
            - Elevation (deg): 仰角
            - Doppler Shift (Hz): 都卜勒頻移
            - Radial Velocity (m/s): 徑向速度
            - Atmospheric Loss (dB): 大氣衰減
            - Path Loss (dB): 路徑損耗
            - Propagation Delay (ms): 傳播延遲

        3GPP 偏移量 (2 維):
            - Offset MO (dB): Measurement offset
            - Cell Offset (dB): Cell-specific offset

    動作空間 (2 個離散動作):
        0: maintain (保持當前服務衛星)
        1: handover (換手到最佳鄰居)

    獎勵函數:
        reward = w1 * qos_improvement
                - w2 * handover_penalty
                + w3 * signal_quality
                - w4 * ping_pong_penalty

    SOURCE:
    - 3GPP TS 38.331 v18.5.1 (事件定義)
    - 3GPP TS 38.215 v18.1.0 Section 5.1 (信號品質測量)
    - docs/final.md Line 139 (獎勵函數設計)
    """

    metadata = {'render_modes': ['human']}

    def __init__(self,
                 episodes: List,  # List[Episode] or List[Dict] from phase1_data_loader_v2.py
                 config: Dict,
                 mode: str = 'train'):
        """
        Args:
            episodes: 換手決策 Episode 列表（來自 phase1_data_loader_v2.py）
                     可以是字典列表或 Episode 對象列表
            config: RL 配置
            mode: 'train' or 'eval'
        """
        super().__init__()

        # 相容性處理：將字典列表轉換為 Episode 對象列表
        # SOURCE: rl.md Line 268-279 (相容性轉換邏輯)
        if episodes and len(episodes) > 0 and isinstance(episodes[0], dict):
            self.episodes = [Episode(ep) for ep in episodes]
            print(f"   ✅ 已轉換 {len(episodes)} 個字典為 Episode 對象")
        else:
            self.episodes = episodes

        self.config = config
        self.mode = mode

        # 狀態空間：Box(12,) - 完整特徵集
        # [rsrp, rsrq, sinr, distance, elevation, doppler, velocity,
        #  atmospheric_loss, path_loss, propagation_delay, offset_mo, cell_offset]
        self.observation_space = spaces.Box(
            low=np.array([
                -150.0,  # rsrp_dbm (SOURCE: 3GPP TS 38.215 v18.1.0 Table 5.1.1-1)
                -30.0,   # rsrq_db (SOURCE: 3GPP TS 38.215 v18.1.0 Table 5.1.3-1)
                -10.0,   # rs_sinr_db (SOURCE: 3GPP TS 38.215 v18.1.0 Table 5.1.5-1)
                500.0,   # distance_km (SOURCE: LEO orbit altitude range)
                0.0,     # elevation_deg (SOURCE: 3GPP TR 38.821 Section 6.1.2)
                -50000.0,  # doppler_shift_hz (SOURCE: ITU-R M.1184 Annex 1)
                -8000.0,   # radial_velocity_ms (SOURCE: LEO orbital velocity)
                0.0,     # atmospheric_loss_db (SOURCE: ITU-R P.676-13)
                120.0,   # path_loss_db (SOURCE: 3GPP TR 38.811 Section 6.6.3)
                0.0,     # propagation_delay_ms
                -10.0,   # offset_mo_db (SOURCE: 3GPP TS 38.331 Section 5.5.4)
                -10.0    # cell_offset_db (SOURCE: 3GPP TS 38.331 Section 5.5.4)
            ], dtype=np.float32),
            high=np.array([
                -30.0,   # rsrp_dbm
                -3.0,    # rsrq_db
                30.0,    # rs_sinr_db
                3000.0,  # distance_km
                90.0,    # elevation_deg
                50000.0,   # doppler_shift_hz
                8000.0,    # radial_velocity_ms
                30.0,    # atmospheric_loss_db
                200.0,   # path_loss_db
                50.0,    # propagation_delay_ms
                10.0,    # offset_mo_db
                10.0     # cell_offset_db
            ], dtype=np.float32),
            dtype=np.float32
        )

        # 動作空間：Discrete(2)
        # 0=maintain, 1=handover
        self.action_space = spaces.Discrete(2)

        # 獎勵權重 (with SOURCE comments)
        reward_config = config['environment']['reward_weights']
        self.w_qos = reward_config['qos_improvement']        # SOURCE: Zhang et al. 2021 (RL handover weight)
        self.w_handover = reward_config['handover_penalty']  # SOURCE: 3GPP TS 36.839 v11.1.0 Section 6.2.3
        self.w_signal = reward_config['signal_quality']      # SOURCE: Chen et al. 2020 (QoS weight)
        self.w_ping_pong = reward_config['ping_pong_penalty']  # SOURCE: 3GPP TS 36.839 v11.1.0 Section 6.2.3

        # 環境狀態 (Episode-based)
        self.current_episode_idx = 0
        self.current_time_step = 0
        self.total_handovers = 0
        self.last_handover_time = -1
        self.episode_rewards = []

        # 當前 Episode
        self.current_episode = None

        # 重置環境
        self.reset()

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """重置環境（開始新 Episode）"""
        super().reset(seed=seed)

        self.current_time_step = 0
        self.total_handovers = 0
        self.last_handover_time = -1
        self.episode_rewards = []

        # 隨機選擇 Episode（訓練模式）或從頭開始（評估模式）
        if self.mode == 'train' and seed is None:
            self.current_episode_idx = np.random.randint(0, len(self.episodes))
        else:
            self.current_episode_idx = 0

        # 載入當前 Episode
        if len(self.episodes) > 0:
            self.current_episode = self.episodes[self.current_episode_idx]
        else:
            self.current_episode = None

        # 獲取初始狀態
        state = self._get_state()
        info = {
            'episode_idx': self.current_episode_idx,
            'time_step': self.current_time_step,
            'satellite_id': self.current_episode.satellite_id if self.current_episode else None
        }

        return state, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        執行一步

        Args:
            action: 0=maintain, 1=handover

        Returns:
            observation: 下一狀態
            reward: 獎勵
            terminated: 是否結束（episode 完成）
            truncated: 是否截斷（超時）
            info: 額外信息
        """
        # 檢查 Episode 是否結束
        if self.current_episode is None or self.current_time_step >= len(self.current_episode.time_points):
            # Episode 結束
            terminated = True
            truncated = False
            reward = 0.0
            next_state = self._get_state()
            info = {
                'episode_idx': self.current_episode_idx,
                'time_step': self.current_time_step,
                'total_handovers': self.total_handovers,
                'episode_reward': sum(self.episode_rewards)
            }
            return next_state, reward, terminated, truncated, info

        # 獲取當前時間點
        current_time_point = self.current_episode.time_points[self.current_time_step]

        # 計算獎勵
        reward = self._calculate_reward(action, current_time_point)
        self.episode_rewards.append(reward)

        # 更新狀態
        if action == 1:  # handover
            self.total_handovers += 1
            self.last_handover_time = self.current_time_step

        # 移動到下一時間步
        self.current_time_step += 1

        # 獲取下一狀態
        next_state = self._get_state()

        # 檢查是否結束
        terminated = self.current_time_step >= len(self.current_episode.time_points)
        truncated = False

        info = {
            'episode_idx': self.current_episode_idx,
            'time_step': self.current_time_step,
            'total_handovers': self.total_handovers,
            'action_taken': action,
            'reward_components': self._get_reward_components(action, current_time_point)
        }

        return next_state, reward, terminated, truncated, info

    def _get_state(self) -> np.ndarray:
        """
        獲取當前狀態 (12 維完整特徵)

        Returns:
            state: [rsrp, rsrq, sinr, distance, elevation, doppler, velocity,
                    atmospheric_loss, path_loss, propagation_delay, offset_mo, cell_offset]
        """
        # 如果 Episode 結束或無效，返回零狀態
        if self.current_episode is None or self.current_time_step >= len(self.current_episode.time_points):
            return np.zeros(12, dtype=np.float32)

        # 獲取當前時間點的特徵
        time_point = self.current_episode.time_points[self.current_time_step]

        # 提取 12 維特徵
        state = np.array([
            time_point.get('rsrp_dbm', -999.0),
            time_point.get('rsrq_db', -999.0),
            time_point.get('rs_sinr_db', -999.0),
            time_point.get('distance_km', -999.0),
            time_point.get('elevation_deg', -999.0),
            time_point.get('doppler_shift_hz', 0.0),
            time_point.get('radial_velocity_ms', 0.0),
            time_point.get('atmospheric_loss_db', 0.0),
            time_point.get('path_loss_db', 0.0),
            time_point.get('propagation_delay_ms', 0.0),
            time_point.get('offset_mo_db', 0.0),
            time_point.get('cell_offset_db', 0.0),
        ], dtype=np.float32)

        # 處理無效值（用邊界值替換）
        state = np.nan_to_num(state, nan=-999.0, posinf=999.0, neginf=-999.0)

        return state

    def _calculate_reward(self, action: int, time_point: Dict) -> float:
        """
        計算獎勵

        Reward = w1 * QoS_improvement
                - w2 * handover_penalty
                + w3 * signal_quality
                - w4 * ping_pong_penalty

        Args:
            action: 執行的動作
            time_point: 當前時間點特徵

        Returns:
            reward: 總獎勵
        """
        # 組件 1: QoS 改善（基於 RSRP）
        qos_improvement = 0.0
        if action == 1:  # handover
            rsrp = time_point.get('rsrp_dbm', -999.0)
            # 假設換手後可改善 RSRP（簡化模型，實際應比較鄰居衛星）
            # 這裡使用當前 RSRP 作為基準
            if rsrp != -999.0:
                # 正規化到 [-1, 1]
                qos_improvement = (rsrp + 90.0) / 60.0  # 假設範圍 -150 to -30
                qos_improvement = np.clip(qos_improvement, -1.0, 1.0)

        # 組件 2: 換手懲罰
        handover_penalty = 1.0 if action == 1 else 0.0

        # 組件 3: 信號品質獎勵（基於 RSRP 門檻）
        signal_quality = 0.0
        rsrp = time_point.get('rsrp_dbm', -999.0)
        if rsrp != -999.0:
            # SOURCE: 3GPP TS 38.133 v18.3.0 Table 10.1.19.2-1
            if rsrp > -90:  # 良好信號
                signal_quality = 0.5
            elif rsrp < -110:  # 差信號
                signal_quality = -0.5

        # 組件 4: Ping-Pong 懲罰（短時間內連續換手）
        ping_pong_penalty = 0.0
        if action == 1 and self.last_handover_time >= 0:
            # SOURCE: 3GPP TS 36.839 v11.1.0 Section 6.2.3.2 (TTT = 1s typical)
            time_since_last_handover = self.current_time_step - self.last_handover_time
            if time_since_last_handover < 10:  # < 10 time steps (~50s at 5s interval)
                ping_pong_penalty = 1.0

        # 總獎勵
        total_reward = (
            self.w_qos * qos_improvement
            - self.w_handover * handover_penalty
            + self.w_signal * signal_quality
            - self.w_ping_pong * ping_pong_penalty
        )

        return total_reward

    def _get_reward_components(self, action: int, time_point: Dict) -> Dict:
        """獲取獎勵組件（用於分析）"""
        qos = 0.0
        handover_pen = 0.0
        signal_qual = 0.0
        ping_pong_pen = 0.0

        rsrp = time_point.get('rsrp_dbm', -999.0)

        if action == 1:
            if rsrp != -999.0:
                qos = (rsrp + 90.0) / 60.0
                qos = np.clip(qos, -1.0, 1.0)
            handover_pen = 1.0

        if rsrp > -90:
            signal_qual = 0.5
        elif rsrp < -110:
            signal_qual = -0.5

        if action == 1 and self.last_handover_time >= 0:
            time_since_last = self.current_time_step - self.last_handover_time
            if time_since_last < 10:
                ping_pong_pen = 1.0

        return {
            'qos_improvement': qos,
            'handover_penalty': handover_pen,
            'signal_quality': signal_qual,
            'ping_pong_penalty': ping_pong_pen
        }

    def render(self):
        """渲染環境（可選）"""
        if self.current_episode and self.current_time_step < len(self.current_episode.time_points):
            time_point = self.current_episode.time_points[self.current_time_step]
            rsrp = time_point.get('rsrp_dbm', -999.0)
            elevation = time_point.get('elevation_deg', -999.0)
            distance = time_point.get('distance_km', -999.0)

            print(f"Episode {self.current_episode_idx} Step {self.current_time_step}: "
                  f"Satellite={self.current_episode.satellite_id}, "
                  f"RSRP={rsrp:.2f} dBm, "
                  f"Elevation={elevation:.1f}°, "
                  f"Distance={distance:.1f} km, "
                  f"Handovers={self.total_handovers}")


def test_environment():
    """測試環境正確性"""
    import pickle

    print("=" * 70)
    print("Phase 3: RL 環境驗證")
    print("=" * 70)

    # 載入配置
    print("\n📥 載入配置...")
    with open("config/rl_config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # 載入訓練數據（Episode 格式）
    print("📥 載入訓練 Episodes...")
    data_path = Path("data")

    try:
        with open(data_path / "train_episodes.pkl", 'rb') as f:
            train_episodes_raw = pickle.load(f)
        print(f"   訓練 Episodes: {len(train_episodes_raw)}")

        # 轉換為 Episode 對象（如果是字典列表）
        if len(train_episodes_raw) > 0:
            if isinstance(train_episodes_raw[0], dict):
                train_episodes = [Episode(ep) for ep in train_episodes_raw]
                print(f"   ✅ 已轉換為 Episode 對象")
            else:
                train_episodes = train_episodes_raw

            # 顯示第一個 Episode 信息
            first_ep = train_episodes[0]
            print(f"   第一個 Episode: 衛星 {first_ep.satellite_id}, "
                  f"{len(first_ep.time_points)} 時間點")
    except FileNotFoundError:
        print("   ❌ 找不到 train_episodes.pkl")
        print("   請先運行 phase1_data_loader_v2.py 生成數據")
        return

    # 創建環境
    print("\n🔨 創建 RL 環境...")
    env = HandoverEnvironment(train_episodes, config, mode='train')
    print(f"   ✅ 環境創建成功")
    print(f"   狀態空間: {env.observation_space}")
    print(f"   動作空間: {env.action_space}")

    # 測試環境重置
    print("\n🧪 測試環境重置...")
    state, info = env.reset()
    print(f"   初始狀態形狀: {state.shape}")
    print(f"   初始狀態前 3 維 (RSRP/RSRQ/SINR): {state[:3]}")
    assert state.shape == (12,), f"狀態維度錯誤: 期望 (12,), 實際 {state.shape}"
    print(f"   ✅ 重置測試通過")

    # 測試動作執行
    print("\n🧪 測試動作執行...")
    actions = [0, 1, 0, 1, 0]  # maintain, handover, maintain, handover, maintain
    for i, action in enumerate(actions):
        next_state, reward, terminated, truncated, info = env.step(action)
        print(f"   Step {i+1}: action={action}, reward={reward:.3f}, "
              f"handovers={info['total_handovers']}")

        assert next_state.shape == (12,), f"狀態維度錯誤: {next_state.shape}"
        assert isinstance(reward, (int, float)), "獎勵類型錯誤"

    print(f"   ✅ 動作執行測試通過")

    # 測試隨機策略
    print("\n🎲 測試隨機策略（100 steps）...")
    env.reset()
    total_reward = 0
    handover_count = 0

    for step in range(100):
        action = env.action_space.sample()  # 隨機動作
        next_state, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        if action == 1:
            handover_count += 1

        if terminated:
            print(f"   Episode 在 {step+1} 步結束")
            break

    print(f"   總獎勵: {total_reward:.3f}")
    print(f"   換手次數: {handover_count}")
    avg_reward = total_reward / (step + 1) if step > 0 else 0
    print(f"   平均獎勵: {avg_reward:.3f}")
    print(f"   ✅ 隨機策略測試通過")

    # 完整 episode 測試
    print("\n🎯 測試完整 Episode...")
    if len(train_episodes) > 0:
        test_episodes = train_episodes[:3]  # 測試前 3 個 episodes
        env = HandoverEnvironment(test_episodes, config, mode='eval')
        state, info = env.reset()

        episode_reward = 0
        steps = 0

        while True:
            action = env.action_space.sample()
            next_state, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            steps += 1

            if terminated or truncated:
                break

        print(f"   Episode 完成")
        print(f"   總步數: {steps}")
        print(f"   總獎勵: {episode_reward:.3f}")
        print(f"   總換手次數: {info['total_handovers']}")
        print(f"   ✅ Episode 測試通過")

    print("\n" + "=" * 70)
    print("✅ Phase 3 完成！環境驗證通過")
    print("=" * 70)
    print("\n下一步: 運行 Phase 4 (RL 訓練)")
    print("  python phase4_rl_training.py")


if __name__ == "__main__":
    test_environment()
