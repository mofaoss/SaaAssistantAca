#!/usr/bin/env python
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_SOURCE_LANG = "en"
SUPPORTED_LANGS = ["en", "zh_CN", "zh_HK"]


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


def _resolve_source_lang(
    key: str,
    source_map: dict[str, str],
    maps: dict[str, dict[str, str]],
) -> str | None:
    source_lang = source_map.get(key)
    if source_lang in {"en", "zh_CN", "zh_HK"}:
        return source_lang
    if key in maps.get("en", {}):
        return "en"
    if key in maps.get("zh_CN", {}):
        return "zh_CN"
    if key in maps.get("zh_HK", {}):
        return "zh_HK"
    return None


def _audit_owner(base: Path, owner_name: str) -> dict:
    paths = {lang: base / f"{lang}.json" for lang in SUPPORTED_LANGS}
    maps = {lang: _load_json(path) for lang, path in paths.items()}
    source_map = _load_json(base / "source_map.json")

    missing_files = [lang for lang, path in paths.items() if not path.exists()]

    all_keys: set[str] = set(source_map.keys())
    for m in maps.values():
        all_keys.update(m.keys())

    source_count = {"en": 0, "zh_CN": 0, "zh_HK": 0}
    source_key_missing = {"en": 0, "zh_CN": 0, "zh_HK": 0}
    missing_from_en = {"zh_CN": 0, "zh_HK": 0}
    missing_from_zh_cn = {"en": 0, "zh_HK": 0}

    for key in sorted(all_keys):
        source_lang = _resolve_source_lang(key, source_map, maps)
        if source_lang is None:
            continue

        source_count[source_lang] += 1
        if key not in maps.get(source_lang, {}):
            source_key_missing[source_lang] += 1

        if source_lang == "en":
            if key not in maps["zh_CN"]:
                missing_from_en["zh_CN"] += 1
            if key not in maps["zh_HK"]:
                missing_from_en["zh_HK"] += 1
        elif source_lang == "zh_CN":
            if key not in maps["en"]:
                missing_from_zh_cn["en"] += 1
            if key not in maps["zh_HK"]:
                missing_from_zh_cn["zh_HK"] += 1

    mixed_source = source_count["en"] > 0 and source_count["zh_CN"] > 0

    issue_count = (
        len(missing_files)
        + sum(source_key_missing.values())
        + missing_from_en["zh_CN"]
        + missing_from_en["zh_HK"]
        + missing_from_zh_cn["en"]
        + missing_from_zh_cn["zh_HK"]
    )

    return {
        "owner": owner_name,
        "source_lang": source_count,
        "mixed_source": mixed_source,
        "missing_files": missing_files,
        "source_key_missing": source_key_missing,
        "missing_keys": {
            "from_en->zh_CN": missing_from_en["zh_CN"],
            "from_en->zh_HK": missing_from_en["zh_HK"],
            "from_zh_CN->en": missing_from_zh_cn["en"],
            "from_zh_CN->zh_HK": missing_from_zh_cn["zh_HK"],
        },
        "issue_count": issue_count,
    }


def _discover_registered_module_dirs(modules_root: Path) -> set[str]:
    registered: set[str] = set()
    for py in modules_root.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                continue
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name) and deco.func.id in {"on_demand_module", "periodic_module"}:
                    rel = py.relative_to(modules_root)
                    if rel.parts:
                        registered.add(rel.parts[0])
    return registered


def collect_report() -> dict:
    framework_base = ROOT / "app" / "framework" / "i18n"
    framework_report = _audit_owner(framework_base, "framework")

    modules_root = ROOT / "app" / "features" / "modules"
    registered_dirs = _discover_registered_module_dirs(modules_root)

    module_reports = []
    for module_dir in sorted([p for p in modules_root.iterdir() if p.is_dir()], key=lambda p: p.name):
        if module_dir.name.startswith("__"):
            continue
        if module_dir.name not in registered_dirs:
            continue
        module_reports.append(_audit_owner(module_dir / "i18n", module_dir.name))

    issue_count = framework_report["issue_count"] + sum(item["issue_count"] for item in module_reports)
    mixed_source_modules = [item["owner"] for item in module_reports if item["mixed_source"]]

    return {
        "summary": {
            "issue_count": issue_count,
            "mixed_source_module_count": len(mixed_source_modules),
            "mixed_source_modules": mixed_source_modules,
        },
        "framework": framework_report,
        "modules": module_reports,
    }


def _format_text(report: dict) -> str:
    lines: list[str] = []
    lines.append("[framework]")
    fw = report["framework"]
    lines.append(f"{fw['owner']}:")
    lines.append(f"  source_lang: en={fw['source_lang']['en']}, zh_CN={fw['source_lang']['zh_CN']}, zh_HK={fw['source_lang']['zh_HK']}")
    lines.append(f"  mixed_source: {'yes' if fw['mixed_source'] else 'no'}")
    lines.append(f"  missing_files: {', '.join(fw['missing_files']) if fw['missing_files'] else 'none'}")
    lines.append(
        "  source_key_missing: "
        f"en={fw['source_key_missing']['en']}, "
        f"zh_CN={fw['source_key_missing']['zh_CN']}, "
        f"zh_HK={fw['source_key_missing']['zh_HK']}"
    )
    lines.append(
        "  missing_keys: "
        f"from_en->zh_CN={fw['missing_keys']['from_en->zh_CN']}, "
        f"from_en->zh_HK={fw['missing_keys']['from_en->zh_HK']}, "
        f"from_zh_CN->en={fw['missing_keys']['from_zh_CN->en']}, "
        f"from_zh_CN->zh_HK={fw['missing_keys']['from_zh_CN->zh_HK']}"
    )

    lines.append("")
    lines.append("[modules]")
    for item in report["modules"]:
        lines.append(f"{item['owner']}:")
        lines.append(f"  source_lang: en={item['source_lang']['en']}, zh_CN={item['source_lang']['zh_CN']}, zh_HK={item['source_lang']['zh_HK']}")
        lines.append(f"  mixed_source: {'yes' if item['mixed_source'] else 'no'}")
        lines.append(f"  missing_files: {', '.join(item['missing_files']) if item['missing_files'] else 'none'}")
        lines.append(
            "  source_key_missing: "
            f"en={item['source_key_missing']['en']}, "
            f"zh_CN={item['source_key_missing']['zh_CN']}, "
            f"zh_HK={item['source_key_missing']['zh_HK']}"
        )
        lines.append(
            "  missing_keys: "
            f"from_en->zh_CN={item['missing_keys']['from_en->zh_CN']}, "
            f"from_en->zh_HK={item['missing_keys']['from_en->zh_HK']}, "
            f"from_zh_CN->en={item['missing_keys']['from_zh_CN->en']}, "
            f"from_zh_CN->zh_HK={item['missing_keys']['from_zh_CN->zh_HK']}"
        )

    if report["summary"]["mixed_source_module_count"]:
        lines.append("")
        lines.append("[warnings]")
        lines.append(
            "  mixed_source_modules: "
            + ", ".join(report["summary"]["mixed_source_modules"])
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit i18n completeness and source-language consistency")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON report")
    parser.add_argument("--fail-on-issues", action="store_true", help="Return non-zero when missing files/keys are found")
    args = parser.parse_args()

    report = collect_report()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_format_text(report))

    if args.fail_on_issues and report["summary"]["issue_count"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
