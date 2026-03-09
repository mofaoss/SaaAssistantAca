from app.framework.ui.widgets.custom_message_box import CustomMessageBox
from app.framework.ui.shared.text import ui_text


class RedeemCodesView:
    def __init__(self):
        self._is_dialog_open = False

    def prompt_import_codes(self, parent):
        if self._is_dialog_open:
            return None

        self._is_dialog_open = True
        try:
            dialog = CustomMessageBox(parent, "导入兑换码", "text_edit")
            dialog.content.setEnabled(True)
            dialog.content.setPlaceholderText(
                ui_text("一行一个兑换码", "One code per line")
            )
            if dialog.exec():
                return dialog.content.toPlainText()
            return None
        finally:
            self._is_dialog_open = False
