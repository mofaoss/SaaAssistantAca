import ast
import sys
from pathlib import Path

# Add PerfectBuild to sys.path
sys.path.append(str(Path.cwd() / "PerfectBuild"))

from ast_i18n_transformer import I18nFStringTransformer

source = """
from app.framework.i18n import _
name = "World"
print(_(f"Hello {name}"))
print(_(f"Count: {1+1}"))
print(_("Just a string"))
"""

tree = ast.parse(source)
transformer = I18nFStringTransformer()
new_tree = transformer.visit(tree)
print(ast.unparse(new_tree))
