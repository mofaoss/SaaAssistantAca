import time

from app.framework.infra.automation.timer import Timer
from app.framework.infra.config.app_config import config

from app.features.utils.home_navigation import back_to_home


class EnterGameModule:
    def __init__(self, auto, logger):
        self.auto = auto
        self.logger = logger
        self.enter_game_flag = False
        self.is_log = True

    def run(self):
        self.is_log = config.isLog.value
        self.handle_game()
        back_to_home(self.auto, self.logger)

    def handle_starter_new(self):
        """处理官方新启动器窗口。"""
        timeout = Timer(20).start()
        while True:
            self.auto.take_screenshot()

            if self.auto.find_element("游戏运行中", "text", crop=(0.5, 0.5, 1, 1), is_log=self.is_log):
                break
            if self.auto.click_element("开始游戏", "text", crop=(0.5, 0.5, 1, 1), action="move_click", is_log=self.is_log):
                continue
            if self.auto.find_element("正在更新", "text", crop=(0.5, 0.5, 1, 1), is_log=self.is_log):
                time.sleep(5)
                timeout.reset()
                continue
            if self.auto.click_element("继续更新", "text", crop=(0.5, 0.5, 1, 1), action="mouse_click", is_log=self.is_log):
                time.sleep(5)
                timeout.reset()
                continue
            if self.auto.click_element("更新", "text", include=False, crop=(0.5, 0.5, 1, 1), action="mouse_click", is_log=self.is_log):
                time.sleep(2)
                timeout.reset()
                self.logger.info("需要更新")
                continue
            if timeout.reached():
                self.logger.error("启动器开始游戏超时")
                break

    def handle_game(self):
        """处理游戏窗口部分。"""
        timeout = Timer(180).start()
        while True:
            self.auto.take_screenshot()

            if self.auto.click_element("获得道具", "text", crop=(824 / 1920, 0, 1089 / 1920, 129 / 1080), is_log=self.is_log):
                break
            if self.auto.find_element("基地", "text", crop=(1598 / 1920, 678 / 1080, 1661 / 1920, 736 / 1080)) and self.auto.find_element(
                "任务", "text", crop=(1452 / 1920, 327 / 1080, 1529 / 1920, 376 / 1080), is_log=self.is_log
            ):
                self.logger.info("已进入游戏")
                break

            if self.auto.click_element(["游戏", "开始"], "text", crop=(852 / 1920, 920 / 1080, 1046 / 1920, 981 / 1080), is_log=self.is_log):
                time.sleep(2)
                continue
            if self.auto.click_element(["尘白禁区", "尘白", "禁区"], "text", crop=(812 / 1920, 814 / 1080, 1196 / 1920, 923 / 1080), is_log=self.is_log):
                time.sleep(1)
                continue

            if self.auto.click_element(["X", "x"], "text", crop=(1271 / 1920, 88 / 1080, 1890 / 1920, 367 / 1080), is_log=self.is_log):
                continue
            if self.auto.click_element("app/features/assets/start_game/newbird_cancel.png", "image", crop=(0.5, 0, 1, 0.5), is_log=self.is_log):
                continue

            if timeout.reached():
                self.logger.error("进入游戏超时")
                break

