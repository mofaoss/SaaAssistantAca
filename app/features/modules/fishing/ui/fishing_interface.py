import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (BodyLabel, CheckBox, ComboBox, LineEdit, PixmapLabel, 
                            PrimaryPushButton, PushButton, SimpleCardWidget, SpinBox, 
                            StrongBodyLabel, TitleLabel)
from app.framework.infra.config.app_config import config
from app.framework.infra.events.signal_bus import signalBus
from app.framework.ui.views.periodic_base import ModulePageBase
from app.features.modules.fishing.ui.subtask import AdjustColor

class FishingInterface(ModulePageBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page_fishing")
        self.adjust_color_thread = None

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(8)
        self.right_layout = QVBoxLayout()
        self.right_layout.setSpacing(8)

        self.main_layout.addLayout(self.left_layout, 2)
        self.main_layout.addLayout(self.right_layout, 1)

        self._init_ui()
        self.apply_i18n()

    def _init_ui(self):
        # UI from FishingPage
        self.SimpleCardWidget_fish = SimpleCardWidget(self)
        fish_layout = QVBoxLayout(self.SimpleCardWidget_fish)

        self.BodyLabel_2 = BodyLabel(self.SimpleCardWidget_fish)
        self.ComboBox_fishing_mode = ComboBox(self.SimpleCardWidget_fish)
        self.ComboBox_fishing_mode.setObjectName("ComboBox_fishing_mode")
        fish_layout.addLayout(self._row(self.BodyLabel_2, self.ComboBox_fishing_mode))

        self.BodyLabel_21 = BodyLabel(self.SimpleCardWidget_fish)
        self.LineEdit_fish_key = LineEdit(self.SimpleCardWidget_fish)
        self.LineEdit_fish_key.setObjectName("LineEdit_fish_key")
        fish_layout.addLayout(self._row(self.BodyLabel_21, self.LineEdit_fish_key))

        self.CheckBox_is_save_fish = CheckBox(self.SimpleCardWidget_fish)
        self.CheckBox_is_save_fish.setObjectName("CheckBox_is_save_fish")
        self.CheckBox_is_limit_time = CheckBox(self.SimpleCardWidget_fish)
        self.CheckBox_is_limit_time.setObjectName("CheckBox_is_limit_time")
        fish_layout.addWidget(self.CheckBox_is_save_fish)
        fish_layout.addWidget(self.CheckBox_is_limit_time)

        self.BodyLabel = BodyLabel(self.SimpleCardWidget_fish)
        self.SpinBox_fish_times = SpinBox(self.SimpleCardWidget_fish)
        self.SpinBox_fish_times.setObjectName("SpinBox_fish_times")
        self.SpinBox_fish_times.setMinimum(1)
        self.SpinBox_fish_times.setMaximum(99999)
        fish_layout.addLayout(self._row(self.BodyLabel, self.SpinBox_fish_times))

        self.BodyLabel_23 = BodyLabel(self.SimpleCardWidget_fish)
        self.ComboBox_lure_type = ComboBox(self.SimpleCardWidget_fish)
        self.ComboBox_lure_type.setObjectName("ComboBox_lure_type")
        fish_layout.addLayout(self._row(self.BodyLabel_23, self.ComboBox_lure_type))

        self.StrongBodyLabel = StrongBodyLabel(self.SimpleCardWidget_fish)
        fish_layout.addWidget(self.StrongBodyLabel)

        self.BodyLabel_5 = BodyLabel(self.SimpleCardWidget_fish)
        self.LineEdit_fish_base = LineEdit(self.SimpleCardWidget_fish)
        self.LineEdit_fish_base.setObjectName("LineEdit_fish_base")
        self.LineEdit_fish_base.setEnabled(False)
        fish_layout.addLayout(self._row(self.BodyLabel_5, self.LineEdit_fish_base))

        self.BodyLabel_6 = BodyLabel(self.SimpleCardWidget_fish)
        self.LineEdit_fish_upper = LineEdit(self.SimpleCardWidget_fish)
        self.LineEdit_fish_upper.setObjectName("LineEdit_fish_upper")
        fish_layout.addLayout(self._row(self.BodyLabel_6, self.LineEdit_fish_upper))

        self.BodyLabel_7 = BodyLabel(self.SimpleCardWidget_fish)
        self.LineEdit_fish_lower = LineEdit(self.SimpleCardWidget_fish)
        self.LineEdit_fish_lower.setObjectName("LineEdit_fish_lower")
        fish_layout.addLayout(self._row(self.BodyLabel_7, self.LineEdit_fish_lower))

        btn_row = QHBoxLayout()
        self.PushButton_reset = PushButton(self.SimpleCardWidget_fish)
        self.PrimaryPushButton_get_color = PrimaryPushButton(self.SimpleCardWidget_fish)
        btn_row.addWidget(self.PushButton_reset)
        btn_row.addWidget(self.PrimaryPushButton_get_color)
        fish_layout.addLayout(btn_row)

        self.PixmapLabel = PixmapLabel(self.SimpleCardWidget_fish)
        self.PixmapLabel.setScaledContents(True)
        self.PixmapLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fish_layout.addWidget(self.PixmapLabel)

        self.BodyLabel_tip_fish = BodyLabel(self.SimpleCardWidget_fish)
        self.BodyLabel_tip_fish.setTextFormat(Qt.TextFormat.MarkdownText)
        self.BodyLabel_tip_fish.setWordWrap(True)
        fish_layout.addWidget(self.BodyLabel_tip_fish)
        fish_layout.addStretch(1)

        self.PushButton_start_fishing = PushButton(self)
        self.PushButton_start_fishing.setObjectName("PushButton_start_fishing")

        self.left_layout.addWidget(self.SimpleCardWidget_fish)
        self.left_layout.addWidget(self.PushButton_start_fishing)
        self.left_layout.addStretch(1)

        # Log card
        self.SimpleCardWidget_log = SimpleCardWidget(self)
        log_layout = QVBoxLayout(self.SimpleCardWidget_log)
        self.TitleLabel = TitleLabel(self.SimpleCardWidget_log)
        from PySide6.QtWidgets import QTextBrowser
        self.textBrowser_log_fishing = QTextBrowser(self.SimpleCardWidget_log)
        self.textBrowser_log_fishing.setObjectName("textBrowser_log_fishing")
        self.textBrowser_log_fishing.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        log_layout.addWidget(self.TitleLabel)
        log_layout.addWidget(self.textBrowser_log_fishing)
        self.right_layout.addWidget(self.SimpleCardWidget_log)

        # Connect internal logic
        self.PrimaryPushButton_get_color.clicked.connect(self.adjust_color)
        self.PushButton_reset.clicked.connect(self.reset_color)

    def _row(self, left: QWidget, right: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(left, 1)
        row.addWidget(right, 2)
        return row

    def apply_i18n(self):
        self.ComboBox_fishing_mode.clear()
        self.ComboBox_fishing_mode.addItems([
            self._("High Performance (faster and more accurate, higher CPU usage)", msgid='high_performance_faster_and_more_accurate_higher_cpu_usage'),
            self._("Low Performance (timeout-based auto reel, lower accuracy)", msgid='low_performance_timeout_based_auto_reel_lower_accuracy')
        ])
        self.BodyLabel_tip_fish.setText(
            "### Tips\n* Side mouse buttons are not supported in background mode\n* Use analyst for fishing character, otherwise it may fail\n* Configure cast key, fishing times and lure type in game first\n* Daily limit: rare spot 25, epic spot 50, normal spot unlimited\n* Move to next fishing spot manually after one spot is exhausted\n* If yellow block detection is abnormal, recalibrate HSV color\n"
            if self._is_non_chinese_ui else
            "### 提示\n* 为实现纯后台，现已不支持鼠标侧键\n* 钓鱼角色选择分析员，否则无法正常工作\n* 根据游戏右下角手动设置好抛竿按键、钓鱼次数和鱼饵类型后再点开始\n* 珍奇钓点系统上限25次/天； 稀有钓点上限50次/天； 普通钓点无限制\n* 一个钓点钓完后需手动移动下一个钓鱼点再启动脚本\n* 黄色块异常时请校准HSV，钓鱼出现圆环时点`校准颜色`，再点黄色区域\n"
        )
        lure_type_items = [
            '万能鱼饵', '普通鱼饵', '豪华鱼饵', '至尊鱼饵', '重量级鱼类虫饵', '巨型鱼类虫饵', '重量级鱼类夜钓虫饵',
            '巨型鱼类夜钓虫饵'
        ] if not self._is_non_chinese_ui else [
            'Universal Bait', 'Normal Bait', 'Deluxe Bait', 'Supreme Bait',
            'Heavy Insect Bait', 'Giant Insect Bait', 'Heavy Night Insect Bait', 'Giant Night Insect Bait'
        ]
        self.ComboBox_lure_type.clear()
        self.ComboBox_lure_type.addItems(lure_type_items)

        self.PushButton_start_fishing.setText(self._('Start Fishing', msgid='start_fishing'))
        self.TitleLabel.setText(self._("Log", msgid='log'))
        self.CheckBox_is_save_fish.setText(self._("Pause on new records", msgid='pause_on_new_records'))
        self.BodyLabel_7.setText(self._("Color lower bound", msgid='color_lower_bound'))
        self.PrimaryPushButton_get_color.setText(self._("Calibrate Color", msgid='calibrate_color'))
        self.BodyLabel.setText(self._("Fishing attempts:", msgid='fishing_attempts'))
        self.CheckBox_is_limit_time.setText(self._("Limit max reeling interval per attempt", msgid='limit_max_reeling_interval_per_attempt'))
        self.BodyLabel_21.setText(self._("Custom fishing key", msgid='custom_fishing_key'))
        self.StrongBodyLabel.setText(self._("Calibrate perfect reeling HSV (use when logs report yellow block count > 2)", msgid='calibrate_perfect_reeling_hsv_use_when_logs_report_yellow_block_count_2'))
        self.LineEdit_fish_key.setPlaceholderText(self._("Fishing key is bound to in-game dodge key", msgid='fishing_key_is_bound_to_in_game_dodge_key'))
        self.BodyLabel_6.setText(self._("Color upper bound", msgid='color_upper_bound'))
        self.BodyLabel_5.setText(self._("Base HSV", msgid='base_hsv'))
        self.BodyLabel_2.setText(self._("Fishing mode", msgid='fishing_mode'))
        self.PushButton_reset.setText(self._("Reset", msgid='reset'))
        self.BodyLabel_23.setText(self._("Bait type:", msgid='bait_type'))

    def update_label_color(self):
        hsv_value = [int(value) for value in config.LineEdit_fish_base.value.split(",")]
        hsv_array = np.uint8([[[hsv_value[0], hsv_value[1], hsv_value[2]]]])
        bgr_color = cv2.cvtColor(hsv_array, cv2.COLOR_HSV2BGR)[0][0]
        rgb_color = (bgr_color[2], bgr_color[1], bgr_color[0])
        rgb_color_str = f"#{rgb_color[0]:02X}{rgb_color[1]:02X}{rgb_color[2]:02X}"
        self.PixmapLabel.setStyleSheet(f"background-color: {rgb_color_str};border-radius: 5px;")

    def adjust_color(self):
        self.adjust_color_thread = AdjustColor()
        self.adjust_color_thread.color_changed.connect(self.reload_color_config)
        self.adjust_color_thread.start()

    def reload_color_config(self):
        self.LineEdit_fish_base.setText(config.LineEdit_fish_base.value)
        self.LineEdit_fish_upper.setText(config.LineEdit_fish_upper.value)
        self.LineEdit_fish_lower.setText(config.LineEdit_fish_lower.value)
        self.update_label_color()

    def reset_color(self):
        config.set(config.LineEdit_fish_base, config.LineEdit_fish_base.defaultValue)
        config.set(config.LineEdit_fish_upper, config.LineEdit_fish_upper.defaultValue)
        config.set(config.LineEdit_fish_lower, config.LineEdit_fish_lower.defaultValue)
        self.LineEdit_fish_base.setText(config.LineEdit_fish_base.value)
        self.LineEdit_fish_upper.setText(config.LineEdit_fish_upper.value)
        self.LineEdit_fish_lower.setText(config.LineEdit_fish_lower.value)
        self.update_label_color()

    def load_config(self):
        # Specific load logic for fishing if needed, 
        # but the host can also do generic loading by object name
        self.update_label_color()


