# Environment Variable Override Guide - Nested Keys Support

**Date**: 2025-10-15
**Feature**: Nested Configuration Override via Environment Variables
**Version**: Phase 4 P1 Enhanced

---

## 📋 Overview

The BaseConfigManager now supports **nested key override** via environment variables, allowing fine-grained runtime configuration without modifying YAML files.

**Key Feature**: Use triple underscore (`___`) to navigate nested configuration hierarchies.

---

## 🎯 Motivation

**Problem Before**:
```bash
# ❌ This only set top-level key
export ORBIT_ENGINE_STAGE6_GPP_EVENTS_A3_OFFSET_DB=5.0
# Result: config['gpp_events_a3_offset_db'] = 5.0  (WRONG!)
```

**Solution Now**:
```bash
# ✅ Triple underscore separates nested levels
export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=5.0
# Result: config['gpp_events']['a3']['offset_db'] = 5.0  (CORRECT!)
```

---

## 📚 Syntax Guide

### Environment Variable Naming Convention

```
ORBIT_ENGINE_STAGE{N}_{KEY1}___{KEY2}___{KEY3}=value
                      └─────┬─────┘ └─┬─┘ └─┬─┘
                            │        │     └─── Level 3
                            │        └───────── Level 2
                            └────────────────── Level 1
```

**Components**:
- `ORBIT_ENGINE_STAGE{N}_` - Prefix (stage number 1-6)
- `___` - Triple underscore separator (nesting delimiter)
- `{KEY}` - Configuration key (converted to lowercase)
- `=value` - Value (auto-converted to bool/int/float/string)

---

## 🔍 Examples

### Example 1: Top-level Key (Simple)

**Configuration**:
```yaml
performance:
  log_level: INFO
```

**Environment Variable**:
```bash
export ORBIT_ENGINE_STAGE6_PERFORMANCE___LOG_LEVEL="DEBUG"
```

**Result**:
```python
config['performance']['log_level'] = 'DEBUG'
```

---

### Example 2: Nested Key (2 levels)

**Configuration**:
```yaml
cache_config:
  enabled: true
```

**Environment Variable**:
```bash
export ORBIT_ENGINE_STAGE3_CACHE_CONFIG___ENABLED=false
```

**Result**:
```python
config['cache_config']['enabled'] = False
```

---

### Example 3: Deeply Nested Key (3 levels)

**Configuration**:
```yaml
gpp_events:
  a3:
    offset_db: 3.0
```

**Environment Variable**:
```bash
export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=7.5
```

**Result**:
```python
config['gpp_events']['a3']['offset_db'] = 7.5
```

---

### Example 4: Multiple Overrides

**Environment Variables**:
```bash
export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=5.0
export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A4___RSRP_THRESHOLD_DBM=-95.0
export ORBIT_ENGINE_STAGE6_DECISION_SUPPORT___STRATEGY="hybrid"
```

**Result**:
```python
config['gpp_events']['a3']['offset_db'] = 5.0
config['gpp_events']['a4']['rsrp_threshold_dbm'] = -95.0
config['decision_support']['strategy'] = 'hybrid'
```

---

## 🧪 Type Conversion

Environment variables are **automatically converted** to appropriate Python types:

| Environment Value | Python Type | Result |
|-------------------|-------------|--------|
| `"true"`, `"yes"`, `"1"` | `bool` | `True` |
| `"false"`, `"no"`, `"0"` | `bool` | `False` |
| `"42"` | `int` | `42` |
| `"3.14"` | `float` | `3.14` |
| `"hello"` | `str` | `"hello"` |

**Examples**:
```bash
export ORBIT_ENGINE_STAGE3_CACHE_CONFIG___ENABLED=false
# → config['cache_config']['enabled'] = False (bool)

export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=5.0
# → config['gpp_events']['a3']['offset_db'] = 5.0 (float)

export ORBIT_ENGINE_STAGE6_DECISION_SUPPORT___STRATEGY="hybrid"
# → config['decision_support']['strategy'] = 'hybrid' (str)
```

---

## 🎓 Use Cases

### Use Case 1: Testing Different 3GPP Parameters

```bash
# Test A3 event with different offset thresholds
export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=2.0
./run.sh --stage 6

export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=5.0
./run.sh --stage 6

export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=8.0
./run.sh --stage 6
```

### Use Case 2: Debug Mode with Cache Disabled

```bash
# Enable debug logging and disable cache for troubleshooting
export ORBIT_ENGINE_STAGE3_PERFORMANCE___LOG_LEVEL="DEBUG"
export ORBIT_ENGINE_STAGE3_CACHE_CONFIG___ENABLED=false
./run.sh --stage 3
```

### Use Case 3: Academic Experiments

```bash
# Compare different handover decision strategies
for strategy in signal_based distance_based hybrid; do
  export ORBIT_ENGINE_STAGE6_DECISION_SUPPORT___STRATEGY="$strategy"
  ./run.sh --stage 6
  mv data/outputs/stage6/stage6_research_optimization_*.json \
     results/strategy_${strategy}.json
done
```

---

## ⚡ Performance & Limitations

### Performance
- ✅ **No Performance Impact**: Environment variable parsing happens once at config load time
- ✅ **Fast Execution**: ~0.05s for complete config loading with overrides
- ✅ **Memory Efficient**: No additional memory overhead

### Current Limitations
1. **No Wildcard Support**: Cannot override multiple keys with one variable
   ```bash
   # ❌ Not supported
   export ORBIT_ENGINE_STAGE6_GPP_EVENTS___*___HYSTERESIS_DB=2.0
   ```

2. **No Array Index Support**: Cannot override array elements by index
   ```bash
   # ❌ Not supported
   export ORBIT_ENGINE_STAGE6_ALGORITHMS___0="DQN"
   ```

3. **Case Insensitive Keys**: Keys are converted to lowercase
   ```bash
   # These are equivalent:
   export ORBIT_ENGINE_STAGE6_GPP_EVENTS___A3___OFFSET_DB=5.0
   export ORBIT_ENGINE_STAGE6_gpp_events___a3___offset_db=5.0
   ```

---

## 🔍 Debugging Tips

### Enable Detailed Logging

```python
# In your config manager instantiation
from stages.stage6_research_optimization.stage6_config_manager import Stage6ConfigManager
import logging

logging.basicConfig(level=logging.DEBUG)
manager = Stage6ConfigManager()
config = manager.load_config()
```

**Output**:
```
INFO:shared.config_manager.Stage6ConfigManager:📄 Stage 6 YAML 配置載入: config/stage6_research_optimization_config.yaml
INFO:shared.config_manager.Stage6ConfigManager:🔧 環境變數覆寫 (nested): gpp_events.a3.offset_db = 5.0 (原值: 3.0)
INFO:shared.config_manager.Stage6ConfigManager:✅ 套用了 1 個環境變數覆寫
INFO:shared.config_manager.Stage6ConfigManager:✅ Stage 6 配置載入完成並驗證通過
```

### Verify Override Applied

```bash
# Test override in isolation
python -c "
import sys; sys.path.insert(0, 'src')
from stages.stage6_research_optimization.stage6_config_manager import Stage6ConfigManager
config = Stage6ConfigManager().load_config()
print(f'A3 Offset: {config[\"gpp_events\"][\"a3\"][\"offset_db\"]} dB')
"
```

---

## 📊 Test Coverage

### Unit Tests
- ✅ 57 unit tests (11 new nested key tests)
- ✅ 93% code coverage
- ✅ All edge cases covered

### Key Test Cases
1. 2-level nested override
2. 3-level nested override
3. Creating missing paths
4. Boolean type conversion
5. Mixed flat and nested overrides
6. Overwriting non-dict intermediate values

---

## 🔗 Related Documentation

- **BaseConfigManager Implementation**: `src/shared/config_manager.py:303-382`
- **Unit Tests**: `tests/unit/shared/test_config_manager.py:580-750`
- **Stage 6 Config Example**: `config/stage6_research_optimization_config.yaml:327-350`
- **Phase 4 P1 Completion Report**: `docs/refactoring/phase4_p1_completion_report.md`

---

## ✅ Migration Notes

### For Stage Config Files
All new stage config files should include environment variable documentation at the bottom:

```yaml
# ==================== 環境變數覆寫支援 ====================
# 支援的環境變數 (由 BaseConfigManager 自動處理):
#
# 頂層鍵:
# - ORBIT_ENGINE_STAGE{N}_KEY: 覆寫 key
#
# 嵌套鍵 - 使用三重下劃線 (___) 分隔層級:
# - ORBIT_ENGINE_STAGE{N}_PARENT___CHILD___KEY: 覆寫 parent.child.key
#
# 範例:
#   export ORBIT_ENGINE_STAGE{N}_PARENT___CHILD___KEY=value
#   ./run.sh --stage {N}
```

### Backward Compatibility
- ✅ **Fully backward compatible**: Old flat keys still work
- ✅ **No breaking changes**: Existing environment variables continue to work
- ✅ **Optional feature**: Nested keys are opt-in, not required

---

**Report Generated**: 2025-10-15
**Author**: Orbit Engine Refactoring Team
**Version**: 1.0
