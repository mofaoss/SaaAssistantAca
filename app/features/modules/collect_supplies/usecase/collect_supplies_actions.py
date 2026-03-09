from __future__ import annotations

from PySide6.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition

from app.features.modules.redeem_codes.ui.ui_view import RedeemCodesView
from app.features.modules.redeem_codes.usecase.redeem_codes_usecase import RedeemCodesUseCase
from app.features.utils.ui import ui_text


class CollectSuppliesActions:
    """Collect-supplies module actions (redeem-code related)."""

    def __init__(self, settings_usecase):
        self.redeem_codes_usecase = RedeemCodesUseCase(settings_usecase)
        self.redeem_codes_view = RedeemCodesView()

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

