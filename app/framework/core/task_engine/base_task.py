import logging
from typing import Callable, Optional

import win32gui

from app.framework.infra.events.signal_bus import signalBus
from app.features.utils.ui import ui_text


logger = logging.getLogger(__name__)


class BaseTask:
    def __init__(self):
        self.logger = logger
        self.auto = None

    def run(self):
        pass

    def stop(self):
        if self.auto is not None:
            self.auto.stop()

    def determine_screen_ratio(self, hwnd):
        client_rect = win32gui.GetClientRect(hwnd)
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]

        if client_height == 0:
            self.logger.warning(ui_text("窗口高度为0，无法计算比例", "Window height is 0, cannot calculate ratio"))
            return False

        actual_ratio = client_width / client_height
        target_ratio = 16 / 9

        tolerance = 0.05
        is_16_9 = abs(actual_ratio - target_ratio) <= (target_ratio * tolerance)

        status = ui_text("符合", "Meets") if is_16_9 else ui_text("不符合", "Does not meet")
        self.logger.warning(
            ui_text(
                f"窗口客户区尺寸: {client_width}x{client_height} "
                f"({actual_ratio:.3f}:1), {status}16:9标准比例",
                f"Client area size: {client_width}x{client_height} "
                f"({actual_ratio:.3f}:1), {status}16:9 standard ratio",
            )
        )
        if is_16_9:
            self.auto.scale_x = 1920 / client_width
            self.auto.scale_y = 1080 / client_height
        else:
            self.logger.warning(ui_text("游戏窗口不符合16:9比例，请手动调整", "Game window does not meet 16:9 ratio, please adjust manually."))

        return is_16_9

    def init_auto(
        self,
        name: Optional[str] = None,
        *,
        automation=None,
        automation_factory: Optional[Callable[[], object]] = None,
    ):
        if self.auto is not None:
            self.logger.debug(ui_text(f"延用auto：{self.auto.hwnd}", f"Using existing auto: {self.auto.hwnd}"))
            return True

        try:
            if automation is not None:
                self.auto = automation
            elif callable(automation_factory):
                self.auto = automation_factory()
            else:
                raise ValueError("automation_factory is required when automation is not provided")

            if self.determine_screen_ratio(self.auto.hwnd):
                signalBus.sendHwnd.emit(self.auto.hwnd)
                return True

            self.logger.error(ui_text("游戏窗口比例不是16:9", "Game window ratio is not 16:9"))
            return False
        except Exception as e:
            self.logger.error(ui_text(f"初始化auto失败：{e}", f"Failed to initialize auto: {e}"))
            return False
