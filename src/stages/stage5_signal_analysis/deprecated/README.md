# Deprecated Modules

This directory contains deprecated modules that are no longer used in the project.

## physics_calculator.deprecated.py

**Deprecated since**: 2025-10-02  
**Will be removed in**: v2.0.0  
**Reason**: Violates Grade A academic standards (使用簡化算法)

- Oxygen absorption: 12 lines (標準要求 44 lines)  
- Water vapor absorption: 28 lines (標準要求 35 lines)  
- Simplified scintillation model

**Replacement**:
- Atmospheric attenuation: `itur_p676_atmospheric_model.py` (完整 ITU-R P.676-13 實現)
- Doppler calculation: `doppler_calculator.py` (使用 Stage 2 實際速度)
- Free space loss: 直接使用 Friis 公式 (20*log10(d) + 20*log10(f) + 92.45)

**Reference**: docs/ACADEMIC_STANDARDS.md Line 234-244

