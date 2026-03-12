import ast
import shutil
import sys
import unittest
from pathlib import Path

# 设置路径
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "PerfectBuild"))

from scripts.extract_module_i18n import _extract_marked_strings_from_file
from PerfectBuild.ast_i18n_transformer import process_file

class TestLogAutoI18nComplex(unittest.TestCase):
    def setUp(self):
        self.test_dir = ROOT / "runtime" / "temp" / "test_i18n_complex"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_file = self.test_dir / "complex_logger.py"
        
        # 准备“地狱级”测试源码
        self.source_code = """
import logging
logger = logging.getLogger(__name__)

def test_complex_cases(name, val, data, user):
    # 1. 重复占位符 (Extractor 应生成 name 和 name_2)
    logger.info(f"Duplicate: {name} and {name}")
    
    # 2. 复杂表达式 (应生成 value_N)
    logger.warning(f"Calc: {1 + 1} and {data['key']}")
    
    # 3. 深度属性访问 (应生成 user_profile_name)
    logger.error(f"User: {user.profile.metadata.name}")
    
    # 4. 格式化规范与转换 (应保留 :.2f 和 !r)
    logger.debug(f"Format: {val:.2f} and {name!r}")
    
    # 5. 转义大括号 (应正确处理 {{ }})
    logger.info(f"Braces: {{literal}} and {val}")
    
    # 6. 多行 f-string
    logger.info(f\"\"\"Line 1: {name}
    Line 2: {val}\"\"\")

    # 7. 二进制加法连接的 f-string
    logger.info("Prefix: " + f"Value is {val}")
"""
        self.test_file.write_text(self.source_code, encoding="utf-8")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_extraction_and_transformation_alignment(self):
        """核心测试：验证提取出的 Template 集合与转换后的 Template 集合是否 100% 匹配"""
        
        # --- 步骤 1: 执行 AST 转换 ---
        process_file(self.test_file)
        new_source = self.test_file.read_text(encoding="utf-8")
        
        # --- 步骤 2: 提取转换后的源码中的 _() 模板 ---
        # 我们直接解析转换后的文件，看它里面的 _() 调用
        tree_new = ast.parse(new_source)
        transformed_templates = []
        for node in ast.walk(tree_new):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_":
                if node.args and isinstance(node.args[0], ast.Constant):
                    transformed_templates.append(node.args[0].value)
        
        # --- 步骤 3: 提取原始源码中的模板 (模拟 scripts/extract_module_i18n.py) ---
        # 注意：我们需要用原始文件内容，因为提取器是跑在源码上的
        original_source = """
import logging
logger = logging.getLogger(__name__)

def test_complex_cases(name, val, data, user):
    logger.info(f"Duplicate: {name} and {name}")
    logger.warning(f"Calc: {1 + 1} and {data['key']}")
    logger.error(f"User: {user.profile.metadata.name}")
    logger.debug(f"Format: {val:.2f} and {name!r}")
    logger.info(f"Braces: {{literal}} and {val}")
    logger.info(f\"\"\"Line 1: {name}
    Line 2: {val}\"\"\")
    logger.info("Prefix: " + f"Value is {val}")
"""
        tree_orig = ast.parse(original_source)
        extracted_entries, _, _ = _extract_marked_strings_from_file(self.test_file, tree_orig)
        extracted_templates = [item[3] for item in extracted_entries]

        print("\n[1] 提取到的模板清单:")
        for t in sorted(extracted_templates):
            print(f"    - {t!r}")

        print("\n[2] 转换后的模板清单:")
        for t in sorted(transformed_templates):
            print(f"    - {t!r}")

        # --- 步骤 4: 100% 匹配验证 ---
        self.assertEqual(len(extracted_templates), len(transformed_templates), "模板数量应一致")
        
        for t in extracted_templates:
            # 提取器提取出的模板 (解开了转义) 必须在转换后的代码中作为 _() 参数出现 (保持转义)
            # 例如: 提取器拿到了 'Braces: {literal} and {val}'
            # 转换后的源码里应该是 'Braces: {{literal}} and {val}'
            # 这里需要处理转义差异
            t_escaped = t.replace("{", "{{").replace("}", "}}")
            # 简单的 placeholder 里的 {{var}} 不需要双重转义，这里逻辑稍微复杂一点
            # 但既然我们验证的是生成的 .json 能否匹配运行时，只要两者生成的 key 算法一致即可
            
        # 最简单有效的验证：两者的集合通过相同的规范化处理后应完全一致
        self.assertSetEqual(set(extracted_templates), set(transformed_templates), "模板内容集合应完全匹配")

        print("\n[✓] 压力测试通过: 复杂 f-string 的提取与转换逻辑 100% 对齐")

if __name__ == "__main__":
    unittest.main()
