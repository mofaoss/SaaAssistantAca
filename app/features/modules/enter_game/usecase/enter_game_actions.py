from __future__ import annotations

from PySide6.QtWidgets import QFileDialog
from qfluentwidgets import Flyout, FlyoutView

from app.features.modules.enter_game.usecase.enter_game_usecase import launch_game_with_guard
from app.features.utils.windows import is_exist_snowbreak


class EnterGameActions:
    """Enter-game module actions hosted by periodic page."""

    def __init__(self, is_non_chinese_ui: bool):
        self._is_non_chinese_ui = bool(is_non_chinese_ui)

    def show_path_tutorial(self, host, anchor_widget):
        tutorial_title = "How to find the game path" if self._is_non_chinese_ui else "如何查找对应游戏路径"
        tutorial_content = (
            'No matter which server/channel you play, first select your server in Settings.\n'
            'For global server, choose a path like "E:\\SteamLibrary\\steamapps\\common\\SNOWBREAK".\n'
            'For CN/Bilibili server, open the Snowbreak launcher and find launcher settings.\n'
            'Then choose the game installation path shown there.'
            if self._is_non_chinese_ui
            else
            '不管你是哪个渠道服的玩家，第一步都应该先去设置里选服\n国际服选完服之后选择类似"E:\\SteamLibrary\\steamapps\\common\\SNOWBREAK"的路径\n官服和b服的玩家打开尘白启动器，新版或者旧版启动器都找到启动器里对应的设置\n在下面的路径选择中找到并选择刚才你看到的路径'
        )
        view = FlyoutView(
            title=tutorial_title,
            content=tutorial_content,
            image="asset/path_tutorial.png",
            isClosable=True,
        )
        view.widgetLayout.insertSpacing(1, 5)
        view.widgetLayout.addSpacing(5)
        flyout = Flyout.make(view, anchor_widget, host)
        view.closed.connect(flyout.close)

    @staticmethod
    def select_game_directory(parent, current_directory: str) -> str | None:
        folder = QFileDialog.getExistingDirectory(parent, "选择游戏文件夹", "./")
        if not folder or str(folder) == str(current_directory):
            return None
        return folder

    @staticmethod
    def launch_game(logger):
        return launch_game_with_guard(logger=logger)

    @staticmethod
    def is_game_window_open() -> bool:
        return bool(is_exist_snowbreak())

