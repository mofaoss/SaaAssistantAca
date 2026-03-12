import os
import shutil
import sys
import unittest
from pathlib import Path

# 设置项目根目录
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "PerfectBuild"))

from PerfectBuild.prepare_build import prepare_nuitka_stage, cleanup_stage_dir

class TestPrepareBuildAST(unittest.TestCase):
    def setUp(self):
        # 创建一个模拟项目根目录，避免污染主项目
        self.mock_project = ROOT / "runtime" / "temp" / "mock_project"
        self.mock_project.mkdir(parents=True, exist_ok=True)
        self.stage_dir_name = ".test_nuitka_stage"
        self.stage_dir = self.mock_project / self.stage_dir_name

        # 1. 正常的日志代码文件
        (self.mock_project / "valid_code.py").write_text("""
import logging
logger = logging.getLogger(__name__)
def ok():
    logger.info(f"User {name} logged in")
""", encoding="utf-8")

        # 2. 含有语法错误的文件 (预编译不应崩溃)
        (self.mock_project / "bad_syntax.py").write_text("""
def broken_syntax(
    print("Missing closing parenthesis"
""", encoding="utf-8")

        # 3. 带 BOM 的 UTF-8 文件
        bom_content = "\ufeffimport logging\nlogger = logging.getLogger('bom')\ndef test(): logger.info('Hello BOM')".encode("utf-8")
        (self.mock_project / "with_bom.py").write_bytes(bom_content)

        # 4. 深度嵌套目录
        deep_dir = self.mock_project / "app" / "features" / "deep"
        deep_dir.mkdir(parents=True, exist_ok=True)
        (deep_dir / "deep_module.py").write_text("def run(): self.logger.error(f'Deep error {msg}')", encoding="utf-8")

    def tearDown(self):
        if self.mock_project.exists():
            shutil.rmtree(self.mock_project)

    def test_pipeline_robustness(self):
        """测试 prepare_build 的完整预编译管道"""
        
        print("\n[1] 启动 prepare_nuitka_stage...")
        # 运行预编译逻辑
        result = prepare_nuitka_stage(
            project_root=self.mock_project,
            stage_dir_name=self.stage_dir_name
        )

        print(f"    - 扫描文件数: {result.py_files_scanned}")
        print(f"    - 修改文件数: {result.py_files_changed}")
        print(f"    - 剩余动态 f-string: {result.remaining_dynamic_fstring_calls}")

        # 验证结果
        self.assertTrue(self.stage_dir.exists(), "Stage 目录应当被创建")

        # 1. 验证正常文件是否转换成功
        valid_stage = self.stage_dir / "valid_code.py"
        content = valid_stage.read_text(encoding="utf-8")
        self.assertIn("logger.info(_('User {name} logged in').format(name=name))", content)
        print("    [✓] 正常文件转换成功")

        # 2. 验证语法错误文件是否被安全跳过
        bad_stage = self.stage_dir / "bad_syntax.py"
        self.assertTrue(bad_stage.exists(), "坏文件也应该被拷贝到 stage")
        # 如果没有崩溃，说明 skip 逻辑生效了
        print("    [✓] 语法错误文件已安全跳过")

        # 3. 验证带 BOM 的文件
        bom_stage = self.stage_dir / "with_bom.py"
        bom_content = bom_stage.read_text(encoding="utf-8")
        self.assertIn("logger.info(_('Hello BOM'))", bom_content)
        print("    [✓] 带 BOM 的文件处理成功")

        # 4. 验证深度目录
        deep_stage = self.stage_dir / "app" / "features" / "deep" / "deep_module.py"
        deep_content = deep_stage.read_text(encoding="utf-8")
        self.assertIn("self.logger.error(_('Deep error {msg}').format(msg=msg))", deep_content)
        print("    [✓] 深度嵌套目录转换成功")

        print("\n[✓] prepare_build AST 预编译管道测试全部通过")

if __name__ == "__main__":
    unittest.main()
