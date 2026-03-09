# coding:utf-8
from __future__ import annotations

from enum import Enum


class HotkeyAction(str, Enum):
    NOOP = "noop"
    REQUEST_STOP = "request_stop"
    START_DAILY = "start_daily"
    START_ON_DEMAND = "start_on_demand"
    # Backward-compatible alias.
    START_ADDITIONAL = "start_on_demand"


def resolve_f8_action(global_is_running: bool, context: str) -> HotkeyAction:
    if global_is_running:
        return HotkeyAction.REQUEST_STOP
    if context == "home":
        return HotkeyAction.START_DAILY
    if context in {"additional", "on_demand"}:
        return HotkeyAction.START_ON_DEMAND
    return HotkeyAction.NOOP

