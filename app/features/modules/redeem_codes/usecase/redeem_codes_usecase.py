from app.framework.i18n.runtime import _
class RedeemCodesUseCase:
    def __init__(self, settings_usecase):
        self.settings_usecase = settings_usecase

    def reset_codes(self, text_edit):
        if text_edit.toPlainText():
            text_edit.setText("")
        return self.settings_usecase.reset_redeem_codes()

    def import_codes(self, raw_codes, text_edit):
        codes = self.settings_usecase.parse_import_codes(raw_codes)
        text_edit.setText("\n".join(codes))
        self.settings_usecase.save_import_codes(codes)
        return codes
