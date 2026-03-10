from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel

from app.framework.ui.views.periodic_base import ModulePageBase


class WeaponUpgradePage(ModulePageBase):
    def __init_self._(self, parent=None):
        super().__init_self._("page_weapon", parent=parent, host_context="periodic", use_default_layout=True)

        self.BodyLabel_weapon_tip = BodyLabel(self)
        self.BodyLabel_weapon_tip.setObjectName("BodyLabel_weapon_tip")
        self.BodyLabel_weapon_tip.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_weapon_tip.setWordWrap(True)
        self.BodyLabel_weapon_tip.setText(
            "### Tips\n* Automatically identifies and consumes upgrade materials\n* Stops when weapon reaches max level"
            if self._is_non_chinese_ui
            else "### 提示\n* 自动从背包选择第一把武器进行强化\n* 自动识别并消耗升级材料，直到武器等级提升或满级"
        )
        self.main_layout.addWidget(self.BodyLabel_weapon_tip)
        self.finalize()
