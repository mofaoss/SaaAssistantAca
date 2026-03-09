from __future__ import annotations

from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel, InfoBar, InfoBarPosition, ProgressBar

from app.features.utils.network import calculate_time_difference, get_date_from_api
from app.features.utils.ui import ui_text


class EventTipsUseCase:
    """Event tips business logic extracted from periodic host."""

    def __init__(self, settings_usecase, is_non_chinese_ui: bool, ui_text_fn):
        self.settings_usecase = settings_usecase
        self._is_non_chinese_ui = bool(is_non_chinese_ui)
        self._ui_text = ui_text_fn

    def _load_tip_payload(self, logger, host, url=None):
        if url:
            tips_dic = get_date_from_api(url)
            if "error" in tips_dic.keys():
                logger.error(tips_dic["error"])
                return None
            self.settings_usecase.save_date_tip(tips_dic)
            return tips_dic

        tips_dic = self.settings_usecase.load_date_tip()
        if tips_dic:
            return tips_dic

        InfoBar.error(
            title=ui_text("活动日程更新失败", "Failed to update event schedule"),
            content=ui_text("本地没有存储信息且未获取到url", "No local information stored and no URL fetched"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=host,
        )
        return None

    def refresh_tips_panel(self, ui, logger, host, url=None):
        tips_dic = self._load_tip_payload(logger, host, url=url)
        if not tips_dic:
            return

        if self.settings_usecase.is_log_enabled():
            logger.info(ui_text("获取活动日程成功", "Successfully fetched event schedule"))

        normalized = {key: calculate_time_difference(value) for key, value in tips_dic.items()}
        max_total_days = max(
            (
                total_day
                for _, (days, total_day, status) in normalized.items()
                if status == 0
            ),
            default=1,
        )

        items_list = []
        index = 0
        for key, value in normalized.items():
            body_label = ui.scrollAreaWidgetContents_tips.findChild(BodyLabel, name=f"BodyLabel_tip_{index + 1}")
            if body_label is None:
                body_label = BodyLabel(ui.scrollAreaWidgetContents_tips)
                body_label.setObjectName(f"BodyLabel_tip_{index + 1}")

            progress_bar = ui.scrollAreaWidgetContents_tips.findChild(ProgressBar, name=f"ProgressBar_tip{index + 1}")
            if progress_bar is None:
                progress_bar = ProgressBar(ui.scrollAreaWidgetContents_tips)
                progress_bar.setObjectName(f"ProgressBar_tip{index + 1}")

            days, total_day, status = value
            if status == -1:
                body_label.setText(f"{key} {self._ui_text('已结束', 'finished')}")
                sort_weight = 99999
                progress_bar.setValue(0)
            elif status == 1:
                body_label.setText(self._ui_text(f"{key} 还有 {days} 天开始", f"{key} in {days}d(s)"))
                sort_weight = 10000 + days
                progress_bar.setValue(0)
            else:
                body_label.setText(self._ui_text(f"{key}剩：{days}天", f"{key}: {days}d(s) left"))
                sort_weight = days
                normalized_percent = int((days / max_total_days) * 100)
                progress_bar.setValue(normalized_percent)

            items_list.append([body_label, progress_bar, sort_weight])
            index += 1

        items_list.sort(key=lambda item: item[2])
        for row, (body_label, progress_bar, _) in enumerate(items_list, start=1):
            ui.gridLayout_tips.addWidget(body_label, row, 0, 1, 1)
            ui.gridLayout_tips.addWidget(progress_bar, row, 1, 1, 1)

