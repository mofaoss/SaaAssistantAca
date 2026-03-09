from __future__ import annotations

from app.framework.infra.system.windows import get_hwnd


def is_snowbreak_running(server_interface: int | None = None):
    if server_interface is None:
        try:
            from app.framework.infra.config.app_config import config

            server_interface = int(config.server_interface.value)
        except Exception:
            server_interface = 0

    if server_interface != 2:
        game_name = "尘白禁区"
        game_class = "UnrealWindow"
    else:
        game_name = "Snowbreak: Containment Zone"
        game_class = "UnrealWindow"

    return get_hwnd(game_name, game_class)

