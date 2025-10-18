# Handover-RL V2 重构计划

## 📋 项目概述

**目标**：构建学术级、可扩展的LEO卫星换手强化学习框架

**当前问题**：
- ❌ 使用六阶段输出（10分钟可见时段）- 不足以训练RL
- ❌ 硬编码DQN算法 - 无法扩展到其他算法
- ❌ Episode设计不符合轨道周期
- ❌ 缺少独立的数据生成管道

**V2目标**：
- ✅ 独立的30天训练数据生成
- ✅ 可扩展框架（支持DQN/PPO/A3C等）
- ✅ 基于真实轨道周期的Episode设计
- ✅ 不修改orbit-engine原始代码

---

## 🏗️ 架构设计

### 新旧架构对比

```
V1架构（当前 - 有问题）:
handover-rl/
├── phase1_data_loader_v2.py      # 读取六阶段输出
├── phase3_rl_environment.py       # 硬编码环境
├── phase4_rl_training.py          # 硬编码DQN
└── phase5_evaluation.py

V2架构（新 - 学术级）:
handover-rl/
├── v1_baseline/                   # 保留旧代码
│   └── [旧文件...]
├── v2/                            # ✅ 新架构
│   ├── adapters/                  # 适配器层
│   │   ├── orbit_engine_adapter.py
│   │   └── tle_loader.py
│   ├── core/                      # 核心框架
│   │   ├── base_agent.py
│   │   ├── base_environment.py
│   │   └── trainer.py
│   ├── agents/                    # 算法实现
│   │   ├── dqn_agent.py
│   │   ├── ppo_agent.py (未来)
│   │   └── a3c_agent.py (未来)
│   ├── environments/              # 环境实现
│   │   └── handover_env.py
│   ├── data_generators/           # 数据生成
│   │   ├── rl_data_generator.py
│   │   └── episode_builder.py
│   ├── config/                    # 配置
│   │   ├── data_generation.yaml
│   │   ├── dqn_training.yaml
│   │   └── environment.yaml
│   ├── experiments/               # 实验脚本
│   │   ├── generate_data.py
│   │   ├── train_dqn.py
│   │   └── evaluate.py
│   └── tests/                     # 测试
│       ├── test_adapter.py
│       ├── test_environment.py
│       └── test_agents.py
└── docs/
    └── v2_architecture.md
```

---

## 📅 实施计划

### Phase 0: 准备工作（30分钟）

**任务**：
- [x] 创建重构计划文档
- [ ] 创建 `v2/` 文件夹结构
- [ ] 移动旧代码到 `v1_baseline/`
- [ ] 创建配置文件模板

**输出**：
- `handover-rl/v2/` 完整文件夹结构
- `REFACTOR_PLAN_V2.md`

---

### Phase 1: Orbit-Engine 适配器（2小时）

**目标**：创建非侵入式适配器，复用orbit-engine物理计算

**文件**：
1. `v2/adapters/orbit_engine_adapter.py` (~300行)
2. `v2/adapters/tle_loader.py` (~100行)
3. `v2/tests/test_adapter.py` (~150行)

**功能**：
```python
# 核心接口
adapter = OrbitEngineAdapter(config)
orbital_data = adapter.propagate_orbits(
    tle_list=tle_data,
    start_time=datetime(2025, 10, 18),
    duration_days=30,
    time_step_seconds=5
)
# 返回：30天 × 200颗卫星 × 518,400时间步
```

**依赖**：
- orbit-engine的SGP4Propagator
- orbit-engine的ITU-R计算器
- orbit-engine的3GPP信号计算器

**验证标准**：
- ✅ 不修改orbit-engine代码
- ✅ 生成30天数据
- ✅ 物理计算正确（与orbit-engine Stage 2/5一致）
- ✅ 单元测试覆盖率 >80%

---

### Phase 2: RL 核心框架（3小时）

**目标**：构建可扩展的RL框架基础

**文件**：
1. `v2/core/base_agent.py` (~200行)
2. `v2/core/base_environment.py` (~250行)
3. `v2/core/trainer.py` (~300行)
4. `v2/tests/test_core.py` (~200行)

**设计原则**：
- 符合OpenAI Gym标准
- 算法无关的抽象接口
- 支持可变长Episode
- 易于扩展新算法

**核心抽象**：
```python
class BaseRLAgent(ABC):
    @abstractmethod
    def select_action(state, eval_mode) -> action

    @abstractmethod
    def update(batch) -> metrics

    @abstractmethod
    def save(path) / load(path)

class BaseHandoverEnvironment(gym.Env):
    @abstractmethod
    def reset() -> (state, info)

    @abstractmethod
    def step(action) -> (state, reward, terminated, truncated, info)

    @abstractmethod
    def _calculate_reward(action, state) -> reward
```

**验证标准**：
- ✅ 通过Gym环境检查
- ✅ 支持DQN算法（Phase 3验证）
- ✅ 未来可无缝添加PPO/A3C
- ✅ 文档完整

---

### Phase 3: 数据生成器（3小时）

**目标**：生成30天RL训练数据

**文件**：
1. `v2/data_generators/rl_data_generator.py` (~400行)
2. `v2/data_generators/episode_builder.py` (~250行)
3. `v2/config/data_generation.yaml` (~100行)
4. `v2/experiments/generate_data.py` (~150行)

**数据规格**：
```yaml
time_span: 30 days
time_step: 5 seconds
total_timesteps: 518,400

satellites:
  starlink: 150 satellites
  oneweb: 50 satellites
  total: 200 satellites

episodes:
  generation_method: sliding_window
  window_size: orbital_period  # Starlink: 95min, OneWeb: 110min
  overlap: 50%

  expected_counts:
    starlink: ~6000 episodes
    oneweb: ~4500 episodes
    total: ~10,500 episodes

  split:
    train: 75% (~7875 episodes)
    val: 12.5% (~1312 episodes)
    test: 12.5% (~1312 episodes)

output:
  format: pickle
  files:
    - v2/data/train_episodes.pkl (~2GB)
    - v2/data/val_episodes.pkl (~330MB)
    - v2/data/test_episodes.pkl (~330MB)
    - v2/data/timestamp_index.pkl (~150MB)
```

**Episode结构**：
```python
{
    'satellite_id': '55487',
    'constellation': 'starlink',
    'episode_length': 1140,  # 95分钟 / 5秒
    'time_series': [
        {
            'timestamp': '2025-10-18T00:00:00+00:00',
            'rsrp_dbm': -45.2,
            'rsrq_db': -12.3,
            # ... 12维特征
            'is_visible': True,
            'neighbors': ['55488', '55490', ...]
        },
        # ... 1140个时间点
    ],
    'metadata': {
        'orbital_period_minutes': 95,
        'start_time': '...',
        'end_time': '...'
    }
}
```

**实现流程**：
```
1. 加载TLE数据（200颗卫星）
2. 调用OrbitEngineAdapter生成30天轨道
3. 计算每个时间点的信号质量
4. 构建时间戳索引（邻居映射）
5. 按轨道周期滑动窗口切分Episode
6. 保存为train/val/test
```

**运行时间估算**：
- SGP4传播：30天 × 200卫星 → ~1小时（并行）
- 信号计算：1亿数据点 → ~2小时（并行）
- Episode构建：10,500 episodes → ~30分钟
- **总计：~4小时**

**验证标准**：
- ✅ 生成 ~10,500 episodes
- ✅ Starlink episode长度 = 1140 steps
- ✅ OneWeb episode长度 = 1320 steps
- ✅ 时间戳索引覆盖30天
- ✅ 数据分割正确（75/12.5/12.5）

---

### Phase 4: DQN Agent 实现（2小时）

**目标**：基于新框架实现DQN算法

**文件**：
1. `v2/agents/dqn_agent.py` (~400行)
2. `v2/environments/handover_env.py` (~350行)
3. `v2/config/dqn_training.yaml` (~80行)
4. `v2/experiments/train_dqn.py` (~200行)

**DQN特性**：
- Experience Replay Buffer (1M transitions)
- Target Network (更新频率：100 episodes)
- ε-greedy探索（1.0 → 0.01）
- Huber Loss
- Adam优化器

**训练配置**：
```yaml
training:
  num_episodes: 5000
  batch_size: 64
  gamma: 0.99
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.995

  replay_buffer:
    capacity: 1000000
    min_size: 10000

  target_network:
    update_frequency: 100

  learning_rate: 0.0001

environment:
  state_dim: 12
  action_dim: 2  # 0: keep, 1: handover

  reward_weights:
    qos_improvement: 1.0
    handover_penalty: -0.5
    signal_quality: 0.3
    ping_pong_penalty: -1.0
```

**验证标准**：
- ✅ 符合BaseRLAgent接口
- ✅ 支持可变长Episode
- ✅ 训练收敛（5000 episodes）
- ✅ 优于Baseline方法

---

### Phase 5: 训练与评估（1小时代码 + 6-8小时训练）

**文件**：
1. `v2/experiments/train_dqn.py`
2. `v2/experiments/evaluate.py` (~250行)
3. `v2/experiments/compare_baselines.py` (~200行)

**训练流程**：
```bash
# 1. 生成数据（一次性，4小时）
cd /home/sat/satellite/orbit-engine/handover-rl
python v2/experiments/generate_data.py --config v2/config/data_generation.yaml

# 2. 训练DQN（6-8小时）
python v2/experiments/train_dqn.py --config v2/config/dqn_training.yaml

# 3. 评估
python v2/experiments/evaluate.py --model results/dqn_best.pth
```

**评估指标**：
- 平均累积奖励
- 换手频率
- Ping-Pong率
- 平均信号质量
- 与Baseline对比（RSRP-based, A3-triggered, Always-handover）

**验证标准**：
- ✅ 训练完成5000 episodes
- ✅ 验证曲线收敛
- ✅ DQN > Baseline methods
- ✅ 生成完整评估报告

---

### Phase 6: 测试与文档（2小时）

**文件**：
1. `v2/tests/` - 完整测试套件
2. `docs/v2_architecture.md` - 架构文档
3. `docs/v2_user_guide.md` - 使用指南
4. `v2/README.md` - 快速开始

**测试覆盖**：
- 单元测试：各模块独立测试
- 集成测试：端到端数据生成→训练
- 性能测试：数据生成速度、训练速度

**文档内容**：
- 架构设计说明
- API文档
- 使用示例
- 扩展指南（如何添加新算法）

---

## 📊 时间估算

| Phase | 任务 | 开发时间 | 运行时间 | 总计 |
|-------|------|---------|---------|------|
| 0 | 准备工作 | 0.5h | - | 0.5h |
| 1 | 适配器 | 2h | - | 2h |
| 2 | 核心框架 | 3h | - | 3h |
| 3 | 数据生成器 | 3h | 4h | 7h |
| 4 | DQN实现 | 2h | - | 2h |
| 5 | 训练评估 | 1h | 6-8h | 7-9h |
| 6 | 测试文档 | 2h | - | 2h |
| **总计** | | **13.5h** | **10-12h** | **23.5-25.5h** |

**日程安排**：
- **Day 1（8小时）**：Phase 0-2完成
- **Day 2（8小时）**：Phase 3开发 + 启动数据生成（后台）
- **Day 3（8小时）**：Phase 4-5开发 + 启动训练（后台）
- **夜间/周末**：数据生成（4h）+ 训练（6-8h）自动运行

**实际日历时间**：2-3天

---

## 🎯 成功标准

### 必要条件（Must Have）
- ✅ 生成30天训练数据（~10,500 episodes）
- ✅ 可变长Episode正确实现
- ✅ DQN训练收敛
- ✅ 不修改orbit-engine代码
- ✅ 框架可扩展（支持未来算法）

### 期望条件（Should Have）
- ✅ 训练速度 < 8小时（5000 episodes）
- ✅ DQN性能 > Baseline 20%
- ✅ 测试覆盖率 > 80%
- ✅ 完整文档

### 加分条件（Nice to Have）
- ✅ 实现PPO算法
- ✅ 可视化训练过程
- ✅ 超参数自动调优

---

## ⚠️ 风险与应对

### 风险1：数据生成时间过长
**影响**：可能超过4小时
**应对**：
- 并行处理（多进程）
- 只生成关键卫星（减少到100颗）
- 分批生成（先生成7天测试）

### 风险2：内存不足
**影响**：30天数据可能占用 >10GB内存
**应对**：
- 流式处理（不一次性加载）
- 压缩存储（pickle → zarr）
- 按需加载episodes

### 风险3：可变长Episode训练问题
**影响**：BatchNorm等层可能报错
**应对**：
- 使用Experience Replay（单个transition）
- 避免使用BatchNorm
- 使用LayerNorm替代

---

## 📝 决策点

在开始实施前，需要确认：

1. **数据量**：200颗卫星 vs 100颗卫星？
   - 200颗：更真实，但生成时间更长
   - 100颗：快速验证，后续可扩展

2. **时间步长**：5秒 vs 10秒？
   - 5秒：精度高，数据量大
   - 10秒：适中，训练快

3. **Episode生成方式**：
   - 不重叠：独立episodes，数量少
   - 50%重叠：数据增强，数量多

4. **优先级**：
   - 先实现完整流程（简化参数）？
   - 还是一次性完整实现？

---

## 🚀 下一步

**立即行动**：

1. **您确认以上计划** ✓
2. **我创建文件夹结构** → Phase 0
3. **逐步实现各Phase** → Phase 1-6
4. **每个Phase完成后确认** → 确保质量

**或者，您想调整**：
- 减少数据量（100颗卫星）？
- 简化第一版（7天数据）？
- 调整优先级？

请告诉我您的决定！
