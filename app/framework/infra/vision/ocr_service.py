from __future__ import annotations

from app.framework.infra.vision.ocr_runtime import ocr


def run_ocr(image, extract=None, *, is_log=False):
    """Framework OCR facade backed by shared OCR runtime singleton."""
    if ocr is None:
        return []
    return ocr.run(image, extract, is_log=is_log)
