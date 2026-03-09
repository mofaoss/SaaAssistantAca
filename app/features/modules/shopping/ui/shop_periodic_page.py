from PySide6.QtCore import QSize
from PySide6.QtWidgets import QGridLayout, QWidget
from qfluentwidgets import CheckBox, ScrollArea, StrongBodyLabel

from app.framework.infra.config.app_config import is_non_chinese_ui_language
from app.framework.ui.widgets.tree import TreeFrame_person, TreeFrame_weapon
from app.framework.ui.views.periodic_base import ModulePageBase


class ShopPage(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__("page_shop", parent=parent, host_context="periodic", use_default_layout=True)

        self.ScrollArea = ScrollArea(self)
        self.ScrollArea.setObjectName("ScrollArea")
        self.ScrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.StrongBodyLabel = StrongBodyLabel(self.scrollAreaWidgetContents)
        self.StrongBodyLabel.setObjectName("StrongBodyLabel")
        self.gridLayout.addWidget(self.StrongBodyLabel, 0, 0, 1, 1)

        is_non_chinese_ui = is_non_chinese_ui_language()
        self.select_person = TreeFrame_person(
            parent=self.scrollAreaWidgetContents,
            enableCheck=True,
            is_non_chinese_ui=is_non_chinese_ui,
        )
        self.select_weapon = TreeFrame_weapon(
            parent=self.scrollAreaWidgetContents,
            enableCheck=True,
            is_non_chinese_ui=is_non_chinese_ui,
        )
        self.gridLayout.addWidget(self.select_person, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.select_weapon, 2, 0, 1, 1)

        buy_names = [
            "CheckBox_buy_3", "CheckBox_buy_4", "CheckBox_buy_5",
            "CheckBox_buy_6", "CheckBox_buy_7", "CheckBox_buy_8",
            "CheckBox_buy_9", "CheckBox_buy_10", "CheckBox_buy_11",
            "CheckBox_buy_12", "CheckBox_buy_13", "CheckBox_buy_14", "CheckBox_buy_15",
        ]

        row = 4
        for name in buy_names:
            checkbox = CheckBox(self.scrollAreaWidgetContents)
            checkbox.setObjectName(name)
            checkbox.setMinimumSize(QSize(29, 22))
            setattr(self, name, checkbox)
            self.gridLayout.addWidget(checkbox, row, 0, 1, 1)
            row += 1

        self.ScrollArea.setWidget(self.scrollAreaWidgetContents)
        self.main_layout.addWidget(self.ScrollArea)
        self.finalize()
