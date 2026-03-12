from __future__ import annotations

import builtins
import inspect
import re
from pathlib import Path

from app.framework.i18n.runtime import _ as _runtime_translate, tr, TranslatableMessage, get_catalog, load_i18n_catalogs


def _frame_module_name(frame) -> str:
    try:
        return str(getattr(getattr(frame, "f_globals", {}), "get", lambda *_: "")("__name__", "") or "")
    except Exception:
        return ""


def _is_i18n_internal_frame(frame) -> bool:
    module_name = _frame_module_name(frame).lower()
    if module_name.startswith("app.framework.i18n"):
        return True

    file_name = getattr(getattr(frame, "f_code", None), "co_filename", "")
    normalized = str(file_name).replace("\\", "/").lower()
    if "/app/framework/i18n/" in normalized:
        return True
    dotted = normalized.replace("/", ".")
    if "app.framework.i18n." in dotted:
        return True
    return False


def _first_external_callsite_frame():
    """Return the first frame outside app.framework.i18n package."""
    frame = inspect.currentframe()
    if frame is None:
        return None
    frame = frame.f_back
    while frame is not None:
        if not _is_i18n_internal_frame(frame):
            return frame
        frame = frame.f_back
    return None


def _is_ui_callsite() -> bool:
    """Detect common UI callsites to auto-materialize TranslatableMessage -> str."""
    try:
        caller = _first_external_callsite_frame()
        if caller is None:
            return False

        module_name = _frame_module_name(caller).lower()
        module_ui_indicators = (".ui.", ".views.", ".widgets.", ".shared.localizer")
        if any(ind in module_name for ind in module_ui_indicators):
            return True
            
        file_path_str = getattr(getattr(caller, "f_code", None), "co_filename", "")
        if not file_path_str:
            return False
            
        normalized = file_path_str.replace("\\", "/").lower()
        # Robust detection for UI callsites even in packaged/compiled environments.
        ui_indicators = {"/ui/", "/views/", "/widgets/", "/shared/localizer"}
        if any(ind in normalized for ind in ui_indicators):
            return True
            
        # Fallback to parts check for complex path structures.
        file_path = Path(file_path_str)
        parts = [p.lower() for p in file_path.parts]
        if "ui" in parts or "views" in parts or "widgets" in parts:
            return True
            
    except Exception:
        return False
    return False


def _infer_owner_hints_from_callsite() -> dict:
    """Best-effort owner/callsite inference when AST rewrite metadata is unavailable."""
    hints: dict = {}
    try:
        caller = _first_external_callsite_frame()
        code = getattr(caller, "f_code", None)
        file_name = Path(getattr(code, "co_filename", ""))
        module_name = _frame_module_name(caller)
        lower_module_name = module_name.lower()
        parts = [p.lower() for p in file_name.parts]

        owner_scope = "framework"
        owner_module = None
        if lower_module_name.startswith("app.features.utils") or "features.utils." in lower_module_name:
            owner_scope = "module"
            owner_module = "utils"
        elif lower_module_name.startswith("app.features.modules."):
            tail = module_name[len("app.features.modules."):]
            module_id = re.split(r"[.:/\\]", tail, maxsplit=1)[0]
            if module_id:
                owner_scope = "module"
                owner_module = module_id
        elif "features.modules." in lower_module_name:
            tail = module_name.split("features.modules.", 1)[1]
            module_id = re.split(r"[.:/\\]", tail, maxsplit=1)[0]
            if module_id:
                owner_scope = "module"
                owner_module = module_id
        else:
            try:
                mod_idx = parts.index("modules")
                owner_scope = "module"
                owner_module = file_name.parts[mod_idx + 1]
            except Exception:
                normalized_for_infer = str(file_name).replace("\\", "/")
                lower_infer = normalized_for_infer.lower()
                match = re.search(r"(?:^|[./\\])modules[./\\]([a-z0-9_]+)(?:[./\\]|$)", lower_infer)
                if match:
                    owner_scope = "module"
                    owner_module = match.group(1)
                else:
                    if re.search(r"(?:^|[./\\])features[./\\]utils(?:[./\\]|$)", lower_infer):
                        owner_scope = "module"
                        owner_module = "utils"
                    else:
                        dotted = re.search(r"features\.modules\.([a-z0-9_]+)", lower_infer)
                        if dotted:
                            owner_scope = "module"
                            owner_module = dotted.group(1)
                    if owner_scope == "framework" and (
                        "framework" in parts or ".framework." in lower_infer or ".framework." in lower_module_name
                    ):
                        owner_scope = "framework"
                        owner_module = None

        normalized_path = str(file_name).replace("\\", "/")
        callsite_anchor = normalized_path if normalized_path and normalized_path != "." else ""
        if not callsite_anchor and module_name:
            callsite_anchor = module_name.replace(".", "/")
        if not callsite_anchor:
            callsite_anchor = "<unknown>"
        callsite_key = (
            f"{callsite_anchor}:{getattr(caller, 'f_lineno', 0)}:0"
            if caller is not None
            else None
        )

        context_hint = "ui" if _is_ui_callsite() else "log"

        hints["__i18n_owner_scope__"] = owner_scope
        hints["__i18n_owner_module__"] = owner_module
        if callsite_key:
            hints["__i18n_callsite_key__"] = callsite_key
        hints["__i18n_context_hint__"] = context_hint
    except Exception:
        return {}
    return hints


def _builtin_translate(text, *, msgid=None, **kwargs):
    """Builtin `_` bridge: keep authoring API native while avoiding Qt type crashes."""
    # If import rewrite metadata is missing, recover owner/callsite so keys still land
    # in module catalogs instead of incorrectly falling back to framework.*.
    if "__i18n_owner_scope__" not in kwargs:
        kwargs.update(_infer_owner_hints_from_callsite())
    value = _runtime_translate(text, msgid=msgid, **kwargs)
    if _is_ui_callsite():
        return str(value) if value is not None else ""
    return value


def _(text, *, msgid=None, **kwargs):
    """Public `_` export with automatic Qt-safe adaptation on UI callsites."""
    return _builtin_translate(text, msgid=msgid, **kwargs)


def install_global_translate_symbol() -> None:
    """Expose `_` as a global builtin so modules can use native `_()` authoring."""
    try:
        setattr(builtins, "_", _builtin_translate)
    except Exception:
        # Never block startup if builtin injection fails in restricted runtimes.
        pass


install_global_translate_symbol()

__all__ = ["_", "tr", "TranslatableMessage", "load_i18n_catalogs", "get_catalog"]
