from __future__ import annotations

import logging
from dataclasses import dataclass

import pytest

from app.framework.application.periodic.periodic_page_actions import PeriodicRuntimeActions
from app.framework.i18n import _ as _i18n_bootstrap  # noqa: F401
from app.framework.i18n import runtime


class _CaptureLogger:
    def __init__(self) -> None:
        self.info_messages: list[object] = []
        self.warning_messages: list[object] = []

    def info(self, msg, *args, **kwargs):  # noqa: ANN001
        self.info_messages.append(msg)

    def warning(self, msg, *args, **kwargs):  # noqa: ANN001
        self.warning_messages.append(msg)


@dataclass
class _Plan:
    final_tasks: list[str]
    should_launch_game: bool
    should_warn_game_not_open: bool


class _PeriodicController:
    def build_run_plan(self, *, task_ids, game_opened, auto_open_game_enabled):  # noqa: ANN001
        return _Plan(
            final_tasks=list(task_ids),
            should_launch_game=False,
            should_warn_game_not_open=False,
        )


class _SettingsUseCase:
    def is_auto_open_game_enabled(self) -> bool:
        return False


class _Host:
    def __init__(self):
        self.logger = _CaptureLogger()
        self.task_registry = {
            "task_get_reward": {"name": "Get Reward"},
        }
        self.periodic_controller = _PeriodicController()
        self.settings_usecase = _SettingsUseCase()
        self.tasks_to_run: list[str] = []
        self.primary_task_id = None
        self.after_start_calls: list[list[str]] = []

    @staticmethod
    def _task_display_name(meta, task_id):  # noqa: ANN001
        return str(meta.get("name") or task_id)

    @staticmethod
    def _is_game_window_open():
        return True

    def open_game_directly(self):
        raise AssertionError("open_game_directly should not be called in this test.")

    def after_start_button_click(self, tasks):
        self.after_start_calls.append(list(tasks))


@pytest.fixture(autouse=True)
def _isolated_runtime(monkeypatch):
    catalogs = {"en": {}, "zh_CN": {}, "zh_HK": {}}
    monkeypatch.setattr(runtime, "_CATALOGS", catalogs)
    monkeypatch.setattr(runtime, "_LOADED", True)
    monkeypatch.setattr(runtime, "_TELEMETRY_SEEN", set())
    monkeypatch.setattr(runtime, "_SOURCE_TEXT_KEY_BY_OWNER_CONTEXT", {})
    monkeypatch.setattr(runtime, "_SOURCE_TEXT_KEY_GLOBAL", {})
    monkeypatch.setattr(runtime, "_SOURCE_TEXT_INDEX_READY", False)
    monkeypatch.setattr(runtime, "_resolve_lang", lambda: "zh_CN")
    yield


def test_initiate_task_run_translates_requested_tasks_and_final_queue_without_msgid():
    runtime._CATALOGS["en"]["framework.ui.requested_tasks_task_names"] = "Requested tasks: {task_names}"
    runtime._CATALOGS["zh_CN"]["framework.ui.requested_tasks_task_names"] = "请求的任务：{task_names}"
    runtime._CATALOGS["en"]["framework.ui.final_queued_tasks_var_0"] = "Final queued tasks: {var_0}"
    runtime._CATALOGS["zh_CN"]["framework.ui.final_queued_tasks_var_0"] = "最终排队任务：{var_0}"

    host = _Host()
    PeriodicRuntimeActions.initiate_task_run(host, ["task_get_reward"])

    assert host.after_start_calls == [["task_get_reward"]]
    assert len(host.logger.info_messages) >= 2

    rendered = [
        runtime.render_message(msg, context="log", levelno=logging.INFO)
        for msg in host.logger.info_messages
    ]
    assert "请求的任务：Get Reward" in rendered
    assert "最终排队任务：Get Reward" in rendered
