#!/usr/bin/env python3
"""
文檔同步驗證工具

目的: 自動檢查文檔聲稱的功能是否與實際代碼實現一致
用法: python scripts/verify_documentation_sync.py --stage 4
"""

import re
import sys
from pathlib import Path


class DocumentationVerifier:
    """文檔與代碼同步驗證器"""

    def __init__(self, stage_num: int):
        self.stage_num = stage_num
        self.errors = []
        self.warnings = []

    def verify_stage4(self):
        """驗證 Stage 4 文檔同步性"""
        print(f"🔍 開始驗證 Stage {self.stage_num} 文檔同步性...\n")

        # 1. 讀取驗證矩陣 (唯一真相來源)
        matrix = self._read_verification_matrix()

        # 2. 讀取主文檔聲稱的驗證項目
        doc_claims = self._read_doc_claims()

        # 3. 讀取驗證腳本實際實現
        script_implementations = self._read_script_implementations()

        # 4. 交叉驗證
        self._cross_verify(matrix, doc_claims, script_implementations)

        # 5. 報告結果
        self._report_results()

    def _read_verification_matrix(self):
        """讀取驗證狀態矩陣"""
        matrix_path = Path('docs/stages/STAGE4_VERIFICATION_MATRIX.md')

        if not matrix_path.exists():
            self.errors.append("❌ 致命錯誤: STAGE4_VERIFICATION_MATRIX.md 不存在")
            return None

        content = matrix_path.read_text(encoding='utf-8')

        # 解析表格 (簡化版本：逐行解析)
        matrix = {}
        lines = content.split('\n')

        for line in lines:
            # 跳過表頭和分隔線
            if not line.startswith('|') or '---' in line or '驗證項目' in line:
                continue

            # 分割列
            columns = [col.strip() for col in line.split('|')]
            if len(columns) < 8:  # 至少要有 8 個欄位（包括首尾空欄）
                continue

            try:
                item_id = int(columns[1])
                name = columns[2].replace('*', '').strip()  # 移除加粗標記
                # code_impl_location = columns[3]  # 暫不使用
                script_impl_location = columns[4]
                force_exec = columns[5]
                status_with_mark = columns[6]

                # 判斷腳本是否實現
                script_implemented = '❌' not in script_impl_location

                # 判斷強制執行
                force_execution = '✅' in force_exec

                # 提取狀態文字
                status_match = re.search(r'\*\*([^*]+)\*\*', status_with_mark)
                status = status_match.group(1).strip() if status_match else status_with_mark.strip()

                matrix[name] = {
                    'id': item_id,
                    'script_implemented': script_implemented,
                    'force_execution': force_execution,
                    'status': status
                }
            except (ValueError, IndexError) as e:
                # 跳過解析失敗的行
                continue

        print(f"✅ 讀取驗證矩陣: {len(matrix)} 個驗證項目\n")
        return matrix

    def _read_doc_claims(self):
        """讀取主文檔聲稱的驗證項目"""
        doc_path = Path('docs/stages/stage4-link-feasibility.md')

        if not doc_path.exists():
            self.errors.append("❌ 錯誤: stage4-link-feasibility.md 不存在")
            return []

        content = doc_path.read_text(encoding='utf-8')

        claims = []
        # 查找所有驗證項目聲明
        pattern = r'\*\*(\d+)\.\s+(\w+)\*\*\s*-.*?\(([^)]+)\)'

        for match in re.finditer(pattern, content):
            item_id = int(match.group(1))
            name = match.group(2)
            status_text = match.group(3)

            claims.append({
                'id': item_id,
                'name': name,
                'status_text': status_text
            })

        print(f"✅ 讀取主文檔聲稱: {len(claims)} 個驗證項目\n")
        return claims

    def _read_script_implementations(self):
        """讀取驗證腳本實際實現"""
        script_path = Path('scripts/run_six_stages_with_validation.py')

        if not script_path.exists():
            self.errors.append("❌ 錯誤: run_six_stages_with_validation.py 不存在")
            return {}

        content = script_path.read_text(encoding='utf-8')

        # 查找 Stage 4 驗證段落
        stage4_section_match = re.search(
            r'# Stage 4 專用檢查.*?(?=# Stage \d+|elif stage_num ==|\Z)',
            content,
            re.DOTALL
        )

        if not stage4_section_match:
            self.errors.append("❌ 錯誤: 找不到 Stage 4 驗證段落")
            return {}

        stage4_code = stage4_section_match.group(0)

        # 檢查註釋中標記的驗證項目
        implementations = {}

        # 查找 ✅ 已實現標記
        implemented = re.findall(r'# ✅ 已實現:\s*#\d+\s+(\w+)', stage4_code)
        for name in implemented:
            implementations[name] = True

        # 查找 ❌ 未實現標記
        not_implemented = re.findall(r'# ❌ 未實現:\s*#\d+\s+(\w+)', stage4_code)
        for name in not_implemented:
            implementations[name] = False

        print(f"✅ 讀取驗證腳本: {len(implemented)} 個已實現, {len(not_implemented)} 個未實現\n")
        return implementations

    def _cross_verify(self, matrix, doc_claims, script_implementations):
        """交叉驗證三個來源的一致性"""
        if not matrix:
            return

        print("🔍 開始交叉驗證...\n")

        # 檢查1: 矩陣與腳本一致性
        for name, info in matrix.items():
            script_status = script_implementations.get(name, None)

            if info['script_implemented'] and script_status is False:
                self.errors.append(
                    f"❌ 矛盾: 矩陣聲稱 {name} 已實現，但腳本標記為未實現"
                )
            elif not info['script_implemented'] and script_status is True:
                self.errors.append(
                    f"❌ 矛盾: 矩陣聲稱 {name} 未實現，但腳本標記為已實現"
                )

        # 檢查2: 主文檔與矩陣一致性
        for claim in doc_claims:
            name = claim['name']
            status_text = claim['status_text']

            if name not in matrix:
                self.warnings.append(
                    f"⚠️ 警告: 主文檔提到 {name}，但矩陣中不存在"
                )
                continue

            matrix_status = matrix[name]['status']

            # 檢查狀態描述是否一致
            if '已實現' in status_text and matrix_status == '未驗證':
                self.errors.append(
                    f"❌ 矛盾: 主文檔聲稱 {name} 已實現，但矩陣標記為未驗證"
                )
            elif '未實現' in status_text and matrix_status == '已實現':
                self.errors.append(
                    f"❌ 矛盾: 主文檔聲稱 {name} 未實現，但矩陣標記為已實現"
                )

    def _report_results(self):
        """報告驗證結果"""
        print("\n" + "=" * 60)
        print("📊 驗證結果總結")
        print("=" * 60 + "\n")

        if self.errors:
            print(f"🔴 發現 {len(self.errors)} 個錯誤:\n")
            for error in self.errors:
                print(f"  {error}")
            print()

        if self.warnings:
            print(f"🟡 發現 {len(self.warnings)} 個警告:\n")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ 所有檢查通過！文檔與代碼完全同步。\n")
            return 0
        elif not self.errors:
            print("✅ 無致命錯誤，但有警告需要注意。\n")
            return 0
        else:
            print("❌ 發現不一致問題，請修正後再提交。\n")
            return 1


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(description='驗證文檔與代碼同步性')
    parser.add_argument('--stage', type=int, default=4, help='階段編號')
    args = parser.parse_args()

    verifier = DocumentationVerifier(args.stage)

    if args.stage == 4:
        verifier.verify_stage4()
    else:
        print(f"❌ 暫不支持 Stage {args.stage} 驗證")
        return 1

    return verifier._report_results()


if __name__ == '__main__':
    sys.exit(main())
