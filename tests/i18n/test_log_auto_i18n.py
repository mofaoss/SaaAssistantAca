import ast
import json
import shutil
import sys
import unittest
from pathlib import Path

# 设置路径，确保能导入项目脚本
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "PerfectBuild"))

from scripts.extract_module_i18n import _extract_marked_strings_from_file
from PerfectBuild.ast_i18n_transformer import process_file

class TestLogAutoI18n(unittest.TestCase):
    def setUp(self):
        self.test_dir = ROOT / "runtime" / "temp" / "test_i18n"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_file = self.test_dir / "sample_logger.py"
        
        # 准备测试源码
        self.source_code = """
import logging
logger = logging.getLogger(__name__)

def test_logs(name, count):
    # 1. 静态字符串日志
    logger.info("Static log message")
    
    # 2. f-string 日志 (带变量)
    logger.warning(f"User {name} failed {count} times")
    
    # 3. self.logger 调用
    class A:
        def __init__(self):
            self.logger = logger
        def run(self):
            self.logger.error(f"Error in {self.__class__.__name__}")

    # 4. 混合使用了 _() 的日志 (不应重复包裹)
    logger.debug(_("Already wrapped message"))
"""
        self.test_file.write_text(self.source_code, encoding="utf-8")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_01_extraction(self):
        """测试提取脚本是否能识别日志中的字符串"""
        tree = ast.parse(self.source_code)
        out, dynamic_meta, _ = _extract_marked_strings_from_file(self.test_file, tree)
        
        # 提取到的所有文本内容
        extracted_texts = [item[3] for item in out]
        
        # 验证静态日志提取
        self.assertIn("Static log message", extracted_texts)
        
        # 验证 f-string 日志提取 (应提取出带占位符的模板)
        self.assertIn("User {name} failed {count} times", extracted_texts)
        
        # 验证 self.logger 提取
        self.assertIn("Error in {self___class_____name__}", extracted_texts)
        
        # 验证已手动包裹的 _()
        self.assertIn("Already wrapped message", extracted_texts)
        
        print("\n[✓] 提取测试通过: 成功从日志调用中抓取文本")

    def test_02_transformation(self):
        """测试 AST 转换器是否能自动重构日志调用"""
        # 执行转换
        changed = process_file(self.test_file)
        self.assertTrue(changed, "文件应该被修改")
        
        new_source = self.test_file.read_text(encoding="utf-8")
        
        # 验证静态日志是否被包裹了 _()
        # logger.info("Static log message") -> logger.info(_('Static log message'))
        self.assertIn("logger.info(_('Static log message'))", new_source)
        
        # 验证 f-string 是否被包裹并转换成了 .format()
        # logger.warning(f"User {name}...") -> logger.warning(_('User {name}...').format(name=name...))
        self.assertIn("logger.warning(_('User {name} failed {count} times').format(name=name, count=count))", new_source)
        
        # 验证 self.logger 是否也生效了
        self.assertIn("self.logger.error(_('Error in {self___class_____name__}').format(self___class_____name__=self.__class__.__name__))", new_source)
        
        # 验证手动包裹的 _() 没有被双重包裹
        self.assertIn("logger.debug(_('Already wrapped message'))", new_source)
        self.assertNotIn("logger.debug(_(_(", new_source)
        
        print("[✓] 转换测试通过: 成功在打包前自动包裹 _() 并处理 f-string")

if __name__ == "__main__":
    unittest.main()
