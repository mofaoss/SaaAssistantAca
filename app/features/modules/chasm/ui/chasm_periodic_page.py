from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel

from app.framework.ui.views.periodic_page_base import PeriodicPageBase


class ChasmPage(PeriodicPageBase):
    def __init__(self, parent=None):
        super().__init__("page_chasm", parent=parent)

        self.BodyLabel_chasm_tip = BodyLabel(self)
        self.BodyLabel_chasm_tip.setObjectName("BodyLabel_chasm_tip")
        self.BodyLabel_chasm_tip.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_chasm_tip.setWordWrap(True)

        self.main_layout.addWidget(self.BodyLabel_chasm_tip)
        self.finalize()

