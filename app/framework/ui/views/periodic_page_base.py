from PySide6.QtWidgets import QVBoxLayout, QWidget

from .base_interface import BaseInterface


class PeriodicPageBase(QWidget, BaseInterface):
    def __init__(self, object_name: str, parent=None):
        QWidget.__init__(self, parent)
        BaseInterface.__init__(self)
        self.setObjectName(object_name)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

    def finalize(self):
        self.main_layout.addStretch(1)
