import os
import time
import win32gui
import win32con

from app.framework.infra.events.signal_bus import signalBus
from app.framework.ui.shared.text import ui_text
from app.features.modules.enter_game.usecase.enter_game_usecase import is_snowbreak_running

from app.framework.core.module_system import module


@module(
    id="task_close_game",
    name="执行退出",
    en_name="Execute Exit",
    host="periodic",
)
class CloseGameModule:
    def __init__(
        self,
        auto,
        logger,
        CheckBox_close_game=False,
        CheckBox_shutdown=False,
        CheckBox_close_proxy=False,
    ):
        self.auto = auto
        self.logger = logger
        self.close_game_enabled = bool(CheckBox_close_game)
        self.shutdown_enabled = bool(CheckBox_shutdown)
        self.close_proxy_enabled = bool(CheckBox_close_proxy)

    def run(self):
        # 1. 退出游戏
        if self.close_game_enabled:
            self.logger.info(ui_text("正在退出游戏...", "Exiting game..."))
            hwnd = is_snowbreak_running()
            if hwnd:
                win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                time.sleep(2)

        # 2. 关机
        if self.shutdown_enabled:
            self.logger.info(ui_text("系统将于60秒后关机...", "System will shut down in 60s..."))
            os.system('shutdown -s -t 60')

        # 3. 退出代理 (发送信号给主窗口处理)
        if self.close_proxy_enabled:
            self.logger.info(ui_text("正在退出程序...", "Exiting Application..."))
            signalBus.requestExitApp.emit()


