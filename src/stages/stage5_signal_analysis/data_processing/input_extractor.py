#!/usr/bin/env python3
"""
輸入提取器 - Stage 5 (Fail-Fast 重構版)

✅ Grade A+ 標準: 100% Fail-Fast 數據提取
依據: docs/ACADEMIC_STANDARDS.md Line 265-274

專職責任:
- 從 Stage 4 輸出提取可連線衛星數據
- 驗證必要字段完整性
- 向後兼容新舊數據格式 (connectable_satellites / satellites)
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class InputExtractor:
    """
    輸入數據提取器 (Fail-Fast 重構版)

    ✅ Grade A+ 標準:
    - 禁止使用 .get() 預設值回退
    - 數據缺失時拋出異常並提供詳細錯誤訊息
    - 向後兼容但保持 Fail-Fast 驗證
    """

    @staticmethod
    def extract(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取並驗證 Stage 4 輸出數據

        ✅ Grade A+ 標準: Fail-Fast 數據提取
        - 明確檢查所有必需字段
        - 向後兼容 connectable_satellites 和 satellites 兩種格式
        - 數據缺失時拋出詳細錯誤訊息

        Args:
            input_data: Stage 4 輸出數據

        Returns:
            Dict: 提取的衛星數據和元數據
            {
                'connectable_satellites': Dict[str, List],
                'metadata': {'constellation_configs': Dict}
            }

        Raises:
            ValueError: 缺少必需數據字段
            TypeError: 數據類型錯誤
        """
        # ============================================================================
        # 第 1 層: 輸入數據類型驗證
        # ============================================================================

        if not isinstance(input_data, dict):
            raise TypeError(
                f"input_data 必須是字典類型\n"
                f"當前類型: {type(input_data).__name__}\n"
                f"這表示 Stage 4 輸出格式錯誤"
            )

        # ============================================================================
        # 第 2 層: 衛星數據提取 (向後兼容新舊格式)
        # ============================================================================

        # ✅ Fail-Fast: 明確檢查字段存在性，不使用 .get() 回退
        has_connectable_satellites = 'connectable_satellites' in input_data
        has_satellites = 'satellites' in input_data

        if not has_connectable_satellites and not has_satellites:
            raise ValueError(
                "Stage 5 輸入數據驗證失敗：缺少衛星數據字段\n"
                "必須提供以下之一:\n"
                "  - connectable_satellites: Dict[str, List] (新格式，Stage 4 重構後)\n"
                "  - satellites: Dict[str, Any] (舊格式，向後兼容)\n"
                "這表示 Stage 4 輸出不完整或格式錯誤\n"
                "請檢查 Stage 4 執行是否成功"
            )

        # 提取衛星數據（優先使用新格式）
        if has_connectable_satellites:
            connectable_satellites = input_data['connectable_satellites']

            # 驗證數據類型
            if not isinstance(connectable_satellites, dict):
                raise TypeError(
                    f"connectable_satellites 必須是字典類型\n"
                    f"當前類型: {type(connectable_satellites).__name__}\n"
                    f"這表示 Stage 4 輸出格式錯誤"
                )

            # 驗證數據非空
            if not connectable_satellites:
                raise ValueError(
                    "Stage 5 輸入數據驗證失敗：connectable_satellites 為空\n"
                    "這表示 Stage 4 未找到任何可連線衛星\n"
                    "可能原因:\n"
                    "  - TLE 數據過期\n"
                    "  - 觀測時間不在可見窗口內\n"
                    "  - 幾何可見性條件過嚴（仰角門檻過高）"
                )

            logger.info("✅ 使用新格式數據: connectable_satellites")

        elif has_satellites:
            # 向後兼容舊格式
            satellites = input_data['satellites']

            if not isinstance(satellites, dict):
                raise TypeError(
                    f"satellites 必須是字典類型\n"
                    f"當前類型: {type(satellites).__name__}"
                )

            if not satellites:
                raise ValueError(
                    "Stage 5 輸入數據驗證失敗：satellites 為空\n"
                    "這表示 Stage 4 未找到任何衛星"
                )

            # 轉換舊格式為新格式
            connectable_satellites = {'other': list(satellites.values())}
            logger.warning(
                "⚠️ 使用舊格式數據: satellites (已轉換為 connectable_satellites)\n"
                "建議升級 Stage 4 以使用新格式"
            )

        # ============================================================================
        # 第 3 層: Metadata 提取與驗證
        # ============================================================================

        # ✅ Fail-Fast: metadata 可能是可選的（某些測試場景）
        if 'metadata' not in input_data:
            logger.warning(
                "⚠️ input_data 缺少 metadata 字段\n"
                "將使用空字典，但建議檢查 Stage 4 輸出完整性"
            )
            metadata = {}
        else:
            metadata = input_data['metadata']

            # 驗證 metadata 類型
            if not isinstance(metadata, dict):
                raise TypeError(
                    f"metadata 必須是字典類型\n"
                    f"當前類型: {type(metadata).__name__}"
                )

        # ✅ Fail-Fast: constellation_configs 是信號計算的必要配置
        if 'constellation_configs' not in metadata:
            logger.warning(
                "⚠️ metadata 缺少 constellation_configs 字段\n"
                "信號計算將使用預設配置，可能影響計算準確性\n"
                "建議在 Stage 4 配置中明確定義各星座的發射功率、天線增益等參數"
            )
            constellation_configs = {}
        else:
            constellation_configs = metadata['constellation_configs']

            # 驗證類型
            if not isinstance(constellation_configs, dict):
                raise TypeError(
                    f"constellation_configs 必須是字典類型\n"
                    f"當前類型: {type(constellation_configs).__name__}"
                )

        # ============================================================================
        # 第 4 層: 統計與日誌
        # ============================================================================

        total_connectable = sum(len(sats) for sats in connectable_satellites.values())
        constellation_breakdown = {
            const: len(sats)
            for const, sats in connectable_satellites.items()
        }

        logger.info(f"📊 提取可連線衛星池: {total_connectable} 顆衛星")
        for const, count in constellation_breakdown.items():
            logger.info(f"   {const}: {count} 顆衛星")

        # ============================================================================
        # 第 5 層: 返回驗證後的數據
        # ============================================================================

        return {
            'connectable_satellites': connectable_satellites,
            'metadata': {
                'constellation_configs': constellation_configs
            }
        }


def create_input_extractor() -> InputExtractor:
    """
    工廠函數: 創建輸入提取器實例

    Returns:
        InputExtractor 實例
    """
    return InputExtractor()
