from PySide6.QtWidgets import QHBoxLayout
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, StrongBodyLabel

from app.framework.ui.views.periodic_base import ModulePageBase


class UsePowerPage(ModulePageBase):
    def __init_self._(self, parent=None):
        super().__init_self._("page_2", parent=parent, host_context="periodic", use_default_layout=True)

        first_line = QHBoxLayout()
        self.CheckBox_is_use_power = CheckBox(self)
        self.CheckBox_is_use_power.setObjectName("CheckBox_is_use_power")
        self.ComboBox_power_day = ComboBox(self)
        self.ComboBox_power_day.setObjectName("ComboBox_power_day")
        self.BodyLabel_6 = BodyLabel(self)
        self.BodyLabel_6.setObjectName("BodyLabel_6")
        first_line.addWidget(self.CheckBox_is_use_power)
        first_line.addWidget(self.ComboBox_power_day)
        first_line.addWidget(self.BodyLabel_6)

        self.StrongBodyLabel_2 = StrongBodyLabel(self)
        self.StrongBodyLabel_2.setObjectName("StrongBodyLabel_2")
        self.ComboBox_power_usage = ComboBox(self)
        self.ComboBox_power_usage.setObjectName("ComboBox_power_usage")

        self.main_layout.addLayout(first_line)
        self.main_layout.addWidget(self.StrongBodyLabel_2)
        self.main_layout.addWidget(self.ComboBox_power_usage)
        self._apply_i18n()
        self.finalize()

    def _apply_i18n(self):
        self.ComboBox_power_day.addItems(["1", "2", "3", "4", "5", "6"])
        self.ComboBox_power_usage.addItems(
            [
                self._("Event Stages", msgid='event_stages'),
                self._("Operation Logistics", msgid='operation_logistics'),
            ]
        )
        self.StrongBodyLabel_2.setText(self._("Stamina usage mode", msgid='stamina_usage_mode'))
        self.CheckBox_is_use_power.setText(self._("Auto use expiring", msgid='auto_use_expiring'))
        self.BodyLabel_6.setText(self._("day potion", msgid='day_potion'))

