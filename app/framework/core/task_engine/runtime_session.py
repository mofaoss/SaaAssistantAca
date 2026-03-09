# coding:utf-8
from app.framework.infra.automation.automation import Automation
from app.framework.infra.config.app_config import config
from app.framework.core.task_engine.base_task import BaseTask


class RuntimeAutomationSession:
    """Shared runtime session for task execution threads."""

    def __init__(self, logger_instance):
        self.logger = logger_instance
        self._task_context = BaseTask()
        self._task_context.logger = self.logger
        self._ocr = None

    @property
    def auto(self):
        return self._task_context.auto

    def prepare(self):
        ok = self._task_context.init_auto(automation_factory=self._build_default_automation)
        if not ok:
            return False
        if self.auto is not None:
            self.auto.reset()
        return True

    def _build_default_automation(self):
        if config.server_interface.value != 2:
            game_name = "尘白禁区"
        else:
            game_name = "Snowbreak: Containment Zone"
        return Automation(game_name, "UnrealWindow", self.logger)

    def stop_ocr(self):
        try:
            if self._ocr is not None:
                self._ocr.stop_ocr()
        except Exception:
            pass

    def stop(self):
        if self.auto is None:
            return
        self.auto.stop()

