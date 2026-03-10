#!/usr/bin/env python
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.framework.core.module_system.naming import humanize_name, infer_module_id
from app.framework.i18n.runtime import (
    TranslatableMessage,
    build_key,
    classify_source_language,
    validate_msgid,
)

APP_ROOT = ROOT / "app"
MODULES_ROOT = APP_ROOT / "features" / "modules"
FRAMEWORK_ROOT = APP_ROOT / "framework"
SUPPORTED_SOURCE_LANGS = ["en", "zh_CN"]

_EN_DECL_RE = re.compile(r"^[\x20-\x7E]+$")
LOG_METHODS = {"debug", "info", "warning", "error", "exception", "critical"}


def _validate_english_declaration(text: str, *, field: str) -> None:
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{field} must be a non-empty English string")
    if not _EN_DECL_RE.fullmatch(text):
        raise ValueError(
            f"{field} must use English ASCII declaration text only (found unsupported chars): {text!r}"
        )


def _literal(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def _extract_fields(fields_node: ast.AST) -> dict[str, dict[str, str | None]]:
    result: dict[str, dict[str, str | None]] = {}
    if not isinstance(fields_node, ast.Dict):
        return result

    for key_node, value_node in zip(fields_node.keys, fields_node.values):
        param_name = _literal(key_node)
        if not isinstance(param_name, str):
            continue

        field_id = param_name
        label = humanize_name(param_name)
        help_text = None

        value = _literal(value_node)
        if isinstance(value, str):
            _validate_english_declaration(value, field=f"fields[{param_name}] label")
            label = value
        elif isinstance(value_node, ast.Call) and isinstance(value_node.func, ast.Name) and value_node.func.id == "Field":
            for kw in value_node.keywords:
                if kw.arg == "id":
                    v = _literal(kw.value)
                    if isinstance(v, str) and v.strip():
                        field_id = v.strip()
                elif kw.arg == "label":
                    v = _literal(kw.value)
                    if isinstance(v, str) and v.strip():
                        _validate_english_declaration(v.strip(), field=f"fields[{param_name}] label")
                        label = v.strip()
                elif kw.arg == "help":
                    v = _literal(kw.value)
                    if isinstance(v, str) and v.strip():
                        _validate_english_declaration(v.strip(), field=f"fields[{param_name}] help")
                        help_text = v.strip()

        result[param_name] = {
            "field_id": field_id,
            "label": label,
            "help": help_text,
        }
    return result


def _target_name(node: ast.AST) -> str:
    if isinstance(node, ast.FunctionDef):
        return node.name
    if isinstance(node, ast.ClassDef):
        return node.name
    return "module"


def _owner_from_file(path: Path) -> tuple[str, str | None]:
    rel = path.relative_to(ROOT)
    parts = list(rel.parts)
    if len(parts) >= 5 and parts[0] == "app" and parts[1] == "features" and parts[2] == "modules":
        return "module", parts[3]
    return "framework", None


def _owner_i18n_dir(owner_scope: str, owner_module: str | None) -> Path:
    if owner_scope == "module" and owner_module:
        return MODULES_ROOT / owner_module / "i18n"
    return FRAMEWORK_ROOT / "i18n"


def _extract_declarations_from_file(path: Path, tree: ast.AST) -> list[tuple[str, str | None, str, str, str]]:
    out: list[tuple[str, str | None, str, str, str]] = []
    owner_scope, owner_module = _owner_from_file(path)
    if owner_scope != "module" or owner_module is None:
        return out

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Name):
                continue
            if deco.func.id not in {"on_demand_module", "periodic_module"}:
                continue

            title = _literal(deco.args[0]) if deco.args else None
            if not isinstance(title, str):
                continue
            _validate_english_declaration(title, field=f"{path}: decorator title")

            module_id = None
            fields: dict[str, dict[str, str | None]] = {}
            for kw in deco.keywords:
                if kw.arg == "module_id":
                    v = _literal(kw.value)
                    if isinstance(v, str) and v.strip():
                        module_id = v.strip()
                elif kw.arg == "fields":
                    fields = _extract_fields(kw.value)

            if not module_id:
                dummy = type("Dummy", (), {"__name__": _target_name(node)})
                module_id = infer_module_id(dummy)

            out.append((owner_scope, owner_module, f"module.{module_id}.title", title, "en"))
            for param_name, meta in fields.items():
                field_id = meta["field_id"] or param_name
                out.append(
                    (
                        owner_scope,
                        owner_module,
                        f"module.{module_id}.field.{field_id}.label",
                        meta["label"] or humanize_name(param_name),
                        "en",
                    )
                )
                if meta.get("help"):
                    out.append(
                        (
                            owner_scope,
                            owner_module,
                            f"module.{module_id}.field.{field_id}.help",
                            str(meta["help"]),
                            "en",
                        )
                    )
    return out


def _build_parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _detect_context(node: ast.Call, parents: dict[ast.AST, ast.AST]) -> str:
    parent = parents.get(node)
    if isinstance(parent, ast.Call):
        func = parent.func
        if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS:
            if node in parent.args:
                return "log"
            for kw in parent.keywords:
                if kw.value is node:
                    return "log"
    return "ui"


def _extract_marked_strings_from_file(path: Path, tree: ast.AST) -> list[tuple[str, str | None, str, str, str]]:
    out: list[tuple[str, str | None, str, str, str]] = []
    parents = _build_parents(tree)
    owner_scope, owner_module = _owner_from_file(path)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "_"):
            continue
        if not node.args:
            continue

        text = _literal(node.args[0])
        if not isinstance(text, str):
            continue

        msgid = None
        for kw in node.keywords:
            if kw.arg == "msgid":
                v = _literal(kw.value)
                if isinstance(v, str) and v.strip():
                    msgid = validate_msgid(v.strip())

        source_lang = classify_source_language(text)
        context = _detect_context(node, parents)

        message = TranslatableMessage(
            source_text=text,
            source_lang=source_lang,
            msgid=msgid,
            kwargs={},
            owner_scope=owner_scope,
            owner_module=owner_module,
        )
        key = build_key(message, context=context)
        out.append((owner_scope, owner_module, key, text, source_lang))

    return out


def _load_json(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _save_json(path: Path, data: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    owner_lang_entries: dict[tuple[str, str | None], dict[str, dict[str, str]]] = {}
    owner_source_map: dict[tuple[str, str | None], dict[str, str]] = {}

    py_files = sorted(APP_ROOT.rglob("*.py"))
    for py in py_files:
        try:
            tree = ast.parse(py.read_text(encoding="utf-8-sig"))
        except Exception:
            continue

        entries = []
        entries.extend(_extract_declarations_from_file(py, tree))
        entries.extend(_extract_marked_strings_from_file(py, tree))

        for owner_scope, owner_module, key, value, source_lang in entries:
            if source_lang not in SUPPORTED_SOURCE_LANGS:
                continue
            owner = (owner_scope, owner_module)
            owner_lang_entries.setdefault(owner, {})
            owner_lang_entries[owner].setdefault(source_lang, {})
            owner_lang_entries[owner][source_lang][key] = value

            owner_source_map.setdefault(owner, {})
            prev = owner_source_map[owner].get(key)
            if prev and prev != source_lang:
                raise ValueError(
                    f"Conflicting source language for key {key}: {prev} vs {source_lang}"
                )
            owner_source_map[owner][key] = source_lang

    updated_owners = 0
    for owner, by_lang in owner_lang_entries.items():
        owner_scope, owner_module = owner
        i18n_dir = _owner_i18n_dir(owner_scope, owner_module)
        i18n_dir.mkdir(parents=True, exist_ok=True)

        for lang in SUPPORTED_SOURCE_LANGS:
            if lang not in by_lang:
                continue
            path = i18n_dir / f"{lang}.json"
            current = _load_json(path)
            current.update(by_lang[lang])
            _save_json(path, current)

        source_map_path = i18n_dir / "source_map.json"
        source_map = _load_json(source_map_path)
        source_map.update(owner_source_map.get(owner, {}))
        _save_json(source_map_path, dict(sorted(source_map.items(), key=lambda x: x[0])))

        updated_owners += 1

    print(f"updated_owners={updated_owners}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
