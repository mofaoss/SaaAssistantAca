import ast
import sys
from pathlib import Path

# Mock the extractor's logic
def _expr_to_field_name(expr: ast.AST, idx: int) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        parts = []
        cur = expr
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts = list(reversed(parts))
        candidate = "_".join(parts)
        if candidate:
            return candidate
    return f"value_{idx}"

def mock_extractor(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_":
            arg = node.args[0]
            if isinstance(arg, ast.JoinedStr):
                chunks = []
                used = set()
                idx = 1
                for val in arg.values:
                    if isinstance(val, ast.Constant):
                        chunks.append(str(val.value))
                    elif isinstance(val, ast.FormattedValue):
                        field = _expr_to_field_name(val.value, idx)
                        while field in used:
                            idx += 1
                            field = f"{field}_{idx}"
                        used.add(field)
                        chunks.append("{" + field + "}")
                        idx += 1
                return "".join(chunks)
    return None

# Test the transformer
sys.path.append(str(Path.cwd() / "PerfectBuild"))
from ast_i18n_transformer import I18nFStringTransformer

source = '_(f"Hello {name} and {data.key} and {name}")'
extracted = mock_extractor(source)

tree = ast.parse(source)
transformer = I18nFStringTransformer()
new_tree = transformer.visit(tree)
transformed_source = ast.unparse(new_tree)

print(f"Original: {source}")
print(f"Extracted template: {extracted}")
print(f"Transformed source: {transformed_source}")
