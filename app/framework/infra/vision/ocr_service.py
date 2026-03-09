from __future__ import annotations

import importlib


def run_ocr(image, extract=None, *, is_log=False):
    """Framework OCR facade. Concrete OCR implementation is resolved at runtime."""
    module = importlib.import_module("app.features.modules.ocr.ocr")
    runner = getattr(module, "ocr", None)
    if runner is None:
        return []
    return runner.run(image, extract, is_log=is_log)

