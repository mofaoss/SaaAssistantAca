from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from app.framework.i18n import tr
from app.framework.ui.auto_page.base import AutoPageBase


class OnDemandAutoPage(AutoPageBase):
    """Auto-generated module page for on-demand host.

    Owns local run button + local log panel because on-demand tasks are
    independently started/stopped from this page.
    """

    def _is_background_execution(self) -> bool:
        return str(getattr(self.module_meta, "on_demand_execution", "exclusive") or "exclusive").strip().lower() == "background"

    def _should_show_start_button(self) -> bool:
        return not self._is_background_execution()

    def _should_show_log_panel(self) -> bool:
        return True

    def _mount_split_layout(self) -> None:
        log_card = getattr(self, "SimpleCardWidget_log", None)
        if log_card is None:
            return

        for widget in (self.scroll_area, self.actions_bar, self.PushButton_start, log_card):
            if widget is not None:
                self.main_layout.removeWidget(widget)

        split_host = QWidget(self)
        split_layout = QHBoxLayout(split_host)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(16)

        left_panel = QWidget(split_host)
        left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.scroll_area.setParent(left_panel)
        left_layout.addWidget(self.scroll_area, 1)

        self.actions_bar.setParent(left_panel)
        left_layout.addWidget(self.actions_bar)

        if self.PushButton_start is not None:
            self.PushButton_start.setParent(left_panel)
            left_layout.addWidget(self.PushButton_start)

        log_card.setParent(split_host)
        log_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        split_layout.addWidget(left_panel, 2)
        split_layout.addWidget(log_card, 1)

        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(split_host, 1)

        # Compatibility aliases expected by existing host glue code.
        self.left_panel = left_panel
        self.left_panel_layout = left_layout

    def __init__(self, parent=None, *, module_meta=None, host_context=None):
        super().__init__(parent, module_meta=module_meta, host_context=host_context)
        self._mount_split_layout()

    def _update_button_state(self, is_running: bool):
        button = getattr(self, "PushButton_start", None)
        if button is None:
            return

        stop_candidates: list[str] = []
        start_candidates: list[str] = []
        for module_id in self._module_i18n_ids():
            stop_candidates.extend([
                f"module.{module_id}.ui.stop_{module_id}",
                f"module.{module_id}.ui.stop",
            ])
            start_candidates.extend([
                f"module.{module_id}.ui.start_{module_id}",
                f"module.{module_id}.ui.start",
            ])

        if is_running:
            translated = self._first_translated(stop_candidates)
            button.setText(translated or tr("framework.ui.stop", fallback="Stop"))
            return

        translated = self._first_translated(start_candidates)
        button.setText(translated or tr("framework.ui.run", fallback="Run"))
