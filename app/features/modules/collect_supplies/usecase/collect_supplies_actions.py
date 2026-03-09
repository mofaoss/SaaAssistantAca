from __future__ import annotations

from typing import Protocol

from PySide6.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

from app.framework.ui.shared.text import ui_text


class RedeemCodesUseCasePort(Protocol):
    def reset_codes(self, text_edit) -> str:
        ...

    def import_codes(self, raw_codes: str, text_edit) -> None:
        ...


class RedeemCodesViewPort(Protocol):
    def prompt_import_codes(self, parent):
        ...


class CollectSuppliesActions:
    """Collect-supplies module actions (redeem-code related)."""

    def __init__(self, *, redeem_codes_usecase: RedeemCodesUseCasePort, redeem_codes_view: RedeemCodesViewPort):
        self.redeem_codes_usecase = redeem_codes_usecase
        self.redeem_codes_view = redeem_codes_view

    def on_reset_codes_click(self, host, text_edit):
        content = self.redeem_codes_usecase.reset_codes(text_edit)
        InfoBar.success(
            title=ui_text("重置成功", "Reset Successful"),
            content=ui_text(f"已重置 导入展示 {content}", f"Successfully reset import and display {content}"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=host,
        )

    def on_import_codes_click(self, host, text_edit):
        raw_codes = self.redeem_codes_view.prompt_import_codes(host)
        if raw_codes is None:
            return
        self.redeem_codes_usecase.import_codes(raw_codes, text_edit)
