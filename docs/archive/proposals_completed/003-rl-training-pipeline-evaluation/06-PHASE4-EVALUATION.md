# Proposal 003: Phase 4 - Evaluation Framework

**文檔版本**: v2.0
**最後更新**: 2025-10-23
**預計時間**: 2 天

---

## 📋 概述

Phase 4 實現完整的評估框架，比較 DQN baseline 與 RSRP-based baseline 的性能，並為未來算法提供標準評估基準。

**關鍵設計**:
- ✅ **標準評估指標** - 換手次數、信號品質、QoS 滿足率
- ✅ **雙基準比較** - DQN vs RSRP-based
- ✅ **視覺化報告** - 圖表和統計分析
- ✅ **可擴展架構** - 便於未來算法比較

---

## 🎯 目標

1. 定義標準評估指標
2. 實現 RSRP-based baseline（貪婪策略）
3. 建立評估管道（測試集評估）
4. 生成比較報告（表格 + 圖表）
5. 建立未來算法比較框架

---

## 📦 模組設計

詳見 [02-ARCHITECTURE.md](02-ARCHITECTURE.md) Module 4

### 核心組件

1. **Evaluation Metrics** - 評估指標計算
2. **RSRP Baseline** - 貪婪策略實現
3. **Evaluation Pipeline** - 測試流程
4. **Report Generator** - 報告生成

---

## 📊 評估指標定義

### 核心指標

```python
class EvaluationMetrics:
    """標準評估指標

    SOURCE: Badini et al. (2024) IEEE TAES, Section IV.B
            "Performance Evaluation Metrics"
    """

    @staticmethod
    def calculate_handover_metrics(handover_events: List[dict]) -> dict:
        """計算換手相關指標

        Args:
            handover_events: 換手事件列表

        Returns:
            metrics (dict): 換手指標
                - total_handovers: 總換手次數
                - handover_rate: 每分鐘換手率
                - unnecessary_handovers: 不必要換手次數
                - handover_failure_rate: 換手失敗率
        """
        total_handovers = len(handover_events)

        # 計算不必要換手（短時間內切回原衛星）
        unnecessary_handovers = 0
        for i, event in enumerate(handover_events[:-1]):
            next_event = handover_events[i + 1]
            if (next_event['target_satellite'] == event['source_satellite'] and
                next_event['timestamp'] - event['timestamp'] < 60):  # 60秒內
                unnecessary_handovers += 1

        return {
            'total_handovers': total_handovers,
            'handover_rate': total_handovers / (len(handover_events) / 60),
            'unnecessary_handovers': unnecessary_handovers,
            'unnecessary_handover_rate': unnecessary_handovers / total_handovers
        }

    @staticmethod
    def calculate_qos_metrics(signal_quality_data: List[dict]) -> dict:
        """計算 QoS 相關指標

        Args:
            signal_quality_data: 信號品質數據列表

        Returns:
            metrics (dict): QoS 指標
                - avg_rsrp: 平均 RSRP (dBm)
                - avg_snr: 平均 SNR (dB)
                - coverage_rate: 覆蓋率（RSRP > -110 dBm）
                - qos_satisfaction_rate: QoS 滿足率
        """
        rsrp_values = [d['rsrp_dbm'] for d in signal_quality_data]
        snr_values = [d['snr_db'] for d in signal_quality_data]

        # 3GPP 門檻: RSRP > -110 dBm 視為可服務
        # SOURCE: 3GPP TS 38.133 Section 10.1.16
        coverage_count = sum(1 for rsrp in rsrp_values if rsrp > -110)

        # QoS 滿足: RSRP > -95 dBm AND SNR > 0 dB
        qos_satisfied = sum(
            1 for rsrp, snr in zip(rsrp_values, snr_values)
            if rsrp > -95 and snr > 0
        )

        return {
            'avg_rsrp': np.mean(rsrp_values),
            'avg_snr': np.mean(snr_values),
            'coverage_rate': coverage_count / len(rsrp_values),
            'qos_satisfaction_rate': qos_satisfied / len(rsrp_values)
        }

    @staticmethod
    def calculate_reward_metrics(rewards: List[float]) -> dict:
        """計算獎勵相關指標

        Args:
            rewards: 獎勵值列表

        Returns:
            metrics (dict): 獎勵指標
                - total_reward: 總獎勵
                - avg_reward: 平均獎勵
                - reward_std: 獎勵標準差
        """
        return {
            'total_reward': np.sum(rewards),
            'avg_reward': np.mean(rewards),
            'reward_std': np.std(rewards)
        }
```

---

## 🏆 RSRP Baseline 實現

### 貪婪策略（Greedy RSRP-based）

```python
class RSRPBaselinePolicy:
    """RSRP 貪婪策略 Baseline

    策略: 始終選擇 RSRP 最高的鄰居衛星

    SOURCE: 3GPP TS 38.331 v18.5.1 Section 5.5.4.2
            "A3: Neighbour becomes offset better than serving"
            (簡化為貪婪策略)
    """

    def __init__(self, hysteresis_db: float = 3.0):
        """初始化 RSRP Baseline

        Args:
            hysteresis_db: 遲滯門檻（避免乒乓效應）
                SOURCE: 3GPP TS 38.331 Section 5.5.4.4
        """
        self.hysteresis_db = hysteresis_db

    def select_action(self, state: np.ndarray) -> int:
        """選擇切換動作

        Args:
            state: 環境狀態
                [serving_rsrp, neighbor1_rsrp, neighbor2_rsrp, neighbor3_rsrp, ...]

        Returns:
            action (int): 0=保持當前, 1-N=切換到鄰居N
        """
        serving_rsrp = state[0]
        neighbor_rsrp = state[1:4]  # 3 個候選衛星

        # 找到 RSRP 最高的鄰居
        max_neighbor_rsrp = np.max(neighbor_rsrp)
        max_neighbor_idx = np.argmax(neighbor_rsrp)

        # 貪婪策略 + 遲滯門檻
        if max_neighbor_rsrp > serving_rsrp + self.hysteresis_db:
            return max_neighbor_idx + 1  # 切換到該鄰居
        else:
            return 0  # 保持當前衛星
```

---

## 🔄 評估管道

### 測試流程

```python
class EvaluationPipeline:
    """評估管道"""

    def __init__(self, test_env, metrics_calculator):
        self.test_env = test_env
        self.metrics_calculator = metrics_calculator

    def evaluate_policy(self, policy, episodes: int = 100) -> dict:
        """評估單個策略

        Args:
            policy: 策略實例（DQN Agent 或 RSRP Baseline）
            episodes: 測試回合數

        Returns:
            results (dict): 評估結果
        """
        all_rewards = []
        all_handovers = []
        all_qos_data = []

        for episode in range(episodes):
            state, info = self.test_env.reset()
            episode_rewards = []
            episode_handovers = []
            episode_qos = []

            while True:
                # 選擇動作（不使用探索）
                if hasattr(policy, 'select_action_greedy'):
                    action = policy.select_action_greedy(state)  # DQN
                else:
                    action = policy.select_action(state)  # RSRP Baseline

                next_state, reward, terminated, truncated, info = self.test_env.step(action)
                done = terminated or truncated

                episode_rewards.append(reward)

                # 記錄換手事件
                if action > 0:  # 發生換手
                    episode_handovers.append({
                        'source_satellite': info['current_satellite'],
                        'target_satellite': info['selected_satellite'],
                        'timestamp': info['current_time']
                    })

                # 記錄信號品質
                episode_qos.append({
                    'rsrp_dbm': info['rsrp'],
                    'snr_db': info['snr']
                })

                state = next_state
                if done:
                    break

            all_rewards.extend(episode_rewards)
            all_handovers.extend(episode_handovers)
            all_qos_data.extend(episode_qos)

        # 計算所有指標
        handover_metrics = self.metrics_calculator.calculate_handover_metrics(all_handovers)
        qos_metrics = self.metrics_calculator.calculate_qos_metrics(all_qos_data)
        reward_metrics = self.metrics_calculator.calculate_reward_metrics(all_rewards)

        return {
            'handover': handover_metrics,
            'qos': qos_metrics,
            'reward': reward_metrics
        }

    def compare_policies(self, policies: dict) -> pd.DataFrame:
        """比較多個策略

        Args:
            policies: {policy_name: policy_instance}

        Returns:
            comparison_df (pd.DataFrame): 比較結果表格
        """
        results = {}
        for name, policy in policies.items():
            print(f"Evaluating {name}...")
            results[name] = self.evaluate_policy(policy)

        # 構建比較表格
        comparison_data = []
        for name, metrics in results.items():
            comparison_data.append({
                'Policy': name,
                'Total Handovers': metrics['handover']['total_handovers'],
                'Unnecessary HO Rate': f"{metrics['handover']['unnecessary_handover_rate']:.2%}",
                'Avg RSRP (dBm)': f"{metrics['qos']['avg_rsrp']:.2f}",
                'QoS Satisfaction': f"{metrics['qos']['qos_satisfaction_rate']:.2%}",
                'Total Reward': f"{metrics['reward']['total_reward']:.2f}"
            })

        return pd.DataFrame(comparison_data)
```

---

## 📈 報告生成

### 視覺化報告

```python
class ReportGenerator:
    """評估報告生成器"""

    def generate_comparison_report(
        self,
        comparison_df: pd.DataFrame,
        output_dir: str
    ):
        """生成完整比較報告

        包含:
        - 表格比較
        - 換手次數柱狀圖
        - RSRP 分布圖
        - 獎勵曲線圖
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. 保存比較表格
        table_path = output_path / "comparison_table.csv"
        comparison_df.to_csv(table_path, index=False)
        print(f"✅ Table saved: {table_path}")

        # 2. 生成圖表
        self._plot_handover_comparison(comparison_df, output_path)
        self._plot_qos_comparison(comparison_df, output_path)
        self._plot_reward_comparison(comparison_df, output_path)

        # 3. 生成 Markdown 報告
        self._generate_markdown_report(comparison_df, output_path)

    def _plot_handover_comparison(self, df, output_path):
        """換手次數比較柱狀圖"""
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(x='Policy', y='Total Handovers', kind='bar', ax=ax)
        ax.set_title('Handover Count Comparison')
        ax.set_ylabel('Total Handovers')
        plt.tight_layout()
        plt.savefig(output_path / "handover_comparison.png")
        plt.close()
```

### 報告範例

```markdown
# DQN Baseline Evaluation Report

**生成時間**: 2025-10-23 14:30:00
**測試回合**: 100 episodes
**測試數據**: HDF5 test set

## 📊 性能比較

| Policy | Total Handovers | Unnecessary HO Rate | Avg RSRP (dBm) | QoS Satisfaction | Total Reward |
|--------|----------------|---------------------|----------------|------------------|--------------|
| DQN Baseline | 245 | 8.5% | -35.2 | 92.3% | 4523.5 |
| RSRP Baseline | 312 | 15.2% | -33.8 | 94.1% | 4102.3 |

## 🎯 關鍵發現

1. **換手優化**: DQN 減少 21.5% 換手次數
2. **不必要換手**: DQN 降低 44.1% 乒乓效應
3. **信號品質權衡**: RSRP Baseline 略優 1.4 dB，但換手代價更高
4. **總體性能**: DQN 總獎勵高出 10.3%

## 📈 圖表

![Handover Comparison](handover_comparison.png)
![QoS Metrics](qos_comparison.png)
![Reward Curves](reward_comparison.png)
```

---

## ⏱️ 實施計畫

詳見 [07-IMPLEMENTATION-PLAN.md](07-IMPLEMENTATION-PLAN.md) Phase 4

### Day 8: 評估指標和 RSRP Baseline
- EvaluationMetrics 實現
- RSRPBaselinePolicy 實現
- 單元測試

### Day 9: 評估管道和報告生成
- EvaluationPipeline 實現
- ReportGenerator 實現
- 視覺化圖表
- 完整評估報告

---

## ✅ 驗收標準

- [ ] 評估指標計算正確
- [ ] RSRP Baseline 策略正常運作
- [ ] 評估管道可以測試 100 回合
- [ ] 比較表格正確生成
- [ ] 視覺化圖表清晰易讀
- [ ] Markdown 報告格式正確
- [ ] DQN vs RSRP 比較結果合理
- [ ] 單元測試覆蓋率 > 80%
- [ ] 所有函數有 SOURCE 標註

---

## 🔬 測試策略

### 單元測試

```python
def test_handover_metrics():
    """測試換手指標計算"""
    handover_events = [
        {'source_satellite': 1, 'target_satellite': 2, 'timestamp': 0},
        {'source_satellite': 2, 'target_satellite': 1, 'timestamp': 30},  # 不必要換手
        {'source_satellite': 1, 'target_satellite': 3, 'timestamp': 100},
    ]
    metrics = EvaluationMetrics.calculate_handover_metrics(handover_events)
    assert metrics['total_handovers'] == 3
    assert metrics['unnecessary_handovers'] == 1

def test_qos_metrics():
    """測試 QoS 指標計算"""
    qos_data = [
        {'rsrp_dbm': -35, 'snr_db': 5},
        {'rsrp_dbm': -90, 'snr_db': 2},
        {'rsrp_dbm': -120, 'snr_db': -5},  # 不滿足 QoS
    ]
    metrics = EvaluationMetrics.calculate_qos_metrics(qos_data)
    assert abs(metrics['avg_rsrp'] - (-81.67)) < 0.1
    assert abs(metrics['qos_satisfaction_rate'] - 0.667) < 0.01

def test_rsrp_baseline():
    """測試 RSRP Baseline 策略"""
    policy = RSRPBaselinePolicy(hysteresis_db=3.0)

    # 鄰居明顯更好 → 應該切換
    state = np.array([-40, -30, -50, -60])  # serving=-40, neighbors=[-30, -50, -60]
    action = policy.select_action(state)
    assert action == 1  # 切換到鄰居 1

    # 鄰居僅略優 → 遲滯機制保持當前
    state = np.array([-40, -38, -50, -60])
    action = policy.select_action(state)
    assert action == 0  # 保持當前
```

---

## 📚 參考文獻

1. **Badini et al. (2024)** - "Reinforcement Learning-based Handover for LEO Satellite Networks", IEEE TAES
   - 評估指標定義
   - RSRP Baseline 比較

2. **3GPP TS 38.331 v18.5.1** - Section 5.5.4
   - A3 事件規範
   - 遲滯機制

3. **3GPP TS 38.133** - Section 10.1.16
   - RSRP 測量門檻
   - QoS 要求

4. **Henderson et al. (2018)** - "Deep Reinforcement Learning that Matters", AAAI
   - RL 評估方法論
   - 報告最佳實踐

---

## 🔮 未來擴展

此評估框架設計為可擴展架構，便於未來整合新算法：

```python
# 未來整合用戶算法的範例
def evaluate_new_algorithm(user_algorithm):
    """評估用戶新算法

    Args:
        user_algorithm: 用戶實現的算法實例

    Returns:
        comparison_report: 與 DQN/RSRP 的比較報告
    """
    pipeline = EvaluationPipeline(test_env, metrics_calculator)

    policies = {
        'DQN Baseline': dqn_agent,
        'RSRP Baseline': rsrp_policy,
        'User Algorithm': user_algorithm  # ← 新算法
    }

    comparison_df = pipeline.compare_policies(policies)
    report_generator.generate_comparison_report(comparison_df, 'reports/')

    return comparison_df
```

---

**文檔狀態**: ✅ 完成
**Proposal 003**: 文檔撰寫完成，準備進入實施階段
