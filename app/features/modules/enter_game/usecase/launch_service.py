from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from app.framework.ui.shared.text import ui_text

from .game_window_probe import is_snowbreak_running


_launch_lock = threading.Lock()
_last_game_process = None
_last_launch_ts = 0.0


def has_folder_in_path(path, dir_name):
    try:
        path = Path(path)
        for item in path.iterdir():
            if item.is_dir() and item.name == dir_name:
                return True
        return False
    except Exception:
        return False


def resolve_game_exe(start_path: str) -> str:
    start_path = os.path.normpath(start_path)
    if not os.path.exists(start_path):
        return ""

    parts = start_path.split(os.sep)
    anchor_path = None

    for i, part in enumerate(parts):
        if "snowbreak" in part.lower():
            anchor_path = os.sep.join(parts[: i + 1])
            break

    if not anchor_path:
        max_dir_depth = 3
        start_level = start_path.count(os.sep)

        for root, dirs, _ in os.walk(start_path):
            current_level = root.count(os.sep)
            if current_level - start_level >= max_dir_depth:
                dirs.clear()
                continue

            for d in dirs:
                if "snowbreak" in d.lower():
                    anchor_path = os.path.join(root, d)
                    break

            if anchor_path:
                break

    if not anchor_path:
        return ""

    max_exe_depth = 6
    anchor_level = anchor_path.count(os.sep)

    for root, _, files in os.walk(anchor_path):
        current_level = root.count(os.sep)
        if current_level - anchor_level > max_exe_depth:
            continue

        for file in files:
            if file.lower() == "game.exe":
                full_path = os.path.normpath(os.path.join(root, file))
                if re.search(r"binaries[\\/]win64", full_path.lower()):
                    return full_path

    return ""


def resolve_userdir(start_path: str, exe_path: str) -> str:
    start_path = os.path.normpath(start_path)
    exe_path = os.path.normpath(exe_path)

    game_folder = os.path.normpath(os.path.join(os.path.dirname(exe_path), r"..\..\.."))
    root = os.path.normpath(os.path.join(game_folder, r".."))

    cand1 = os.path.join(root, "game")
    if os.path.isdir(cand1):
        return cand1.replace("\\", "/")

    if os.path.isdir(start_path) and os.path.isdir(os.path.join(start_path, "Game")):
        return start_path.replace("\\", "/")

    return root.replace("\\", "/")


def get_start_arguments(start_path, start_model, exe_path: str = None):
    start_path = os.path.normpath(start_path)

    if exe_path and os.path.exists(exe_path):
        user_dir = resolve_userdir(start_path, exe_path)
    else:
        user_dir = os.path.join(start_path, "game").replace("\\", "/")

    if start_model == 0:
        if has_folder_in_path(start_path, "Temp"):
            return [
                "-FeatureLevelES31",
                "-ChannelID=jinshan",
                f"-userdir={user_dir}",
                '--launcher-language="en"',
                '--launcher-channel="CBJQos"',
                '--launcher-gamecode="cbjq"',
            ]
        return [
            "-FeatureLevelES31",
            "-ChannelID=jinshan",
            f"-userdir={user_dir}",
        ]

    if start_model == 1:
        return [
            "-FeatureLevelES31",
            "-ChannelID=bilibili",
            f"-userdir={user_dir}",
        ]

    if start_model == 2:
        return [
            "-FeatureLevelES31",
            "-channelid=seasun",
            "steamapps",
        ]

    return None


def launch_game_with_guard(
    start_path: str = None,
    game_channel: int = None,
    is_game_running: callable = None,
    logger=None,
    cooldown_seconds: int = 15,
) -> dict[str, Any]:
    global _last_game_process
    global _last_launch_ts

    if start_path is None or game_channel is None:
        try:
            from app.framework.infra.config.app_config import config

            if start_path is None:
                start_path = config.LineEdit_game_directory.value
            if game_channel is None:
                game_channel = int(config.server_interface.value)
        except Exception:
            pass

    if is_game_running is None:
        is_game_running = lambda: is_snowbreak_running(game_channel)

    start_path = os.path.normpath(str(start_path or ""))
    if not start_path or start_path == "./":
        return {"ok": False, "error": "game directory is empty"}

    with _launch_lock:
        if _last_game_process is not None and _last_game_process.poll() is None:
            if logger:
                logger.info(
                    ui_text(
                        "检测到已由程序启动的游戏进程仍在运行，跳过重复启动",
                        "Detected that the game process started by the program is still running, skipping duplicate startup",
                    )
                )
            return {
                "ok": True,
                "already_running": True,
                "message": "game process already running",
                "pid": _last_game_process.pid,
                "process": _last_game_process,
            }

        now = time.time()
        if cooldown_seconds > 0 and now - _last_launch_ts < cooldown_seconds:
            remain = round(cooldown_seconds - (now - _last_launch_ts), 1)
            return {
                "ok": False,
                "error": f"launch cooldown in effect, retry after {remain}s",
            }

        if is_game_running():
            if logger:
                logger.info(ui_text("游戏窗口已存在", "Game window already exists"))
            return {
                "ok": True,
                "already_running": True,
                "message": "game window already exists",
                "process": None,
            }

        exe_path = resolve_game_exe(start_path)
        if not exe_path or not os.path.exists(exe_path):
            if logger:
                logger.error(
                    ui_text(
                        f"未找到游戏主程序 Game.exe，请检查路径: {start_path}",
                        f"Game.exe not found, please check the path: {start_path}",
                    )
                )
            return {
                "ok": False,
                "error": ui_text(
                    f"game exe not found under: {start_path}",
                    f"Game executable not found under: {start_path}",
                ),
            }

        launch_args = get_start_arguments(start_path, game_channel, exe_path=exe_path)
        if launch_args is None:
            if logger:
                logger.error(
                    ui_text(
                        f"游戏启动失败未找到对应参数，start_path：{start_path}，game_channel:{game_channel}",
                        f"Failed to resolve launch arguments, start_path: {start_path}, game_channel: {game_channel}",
                    )
                )
            return {
                "ok": False,
                "error": ui_text(
                    "failed to resolve launch arguments",
                    "Failed to resolve launch arguments",
                ),
            }

        if logger:
            logger.debug(ui_text(f"正在启动 {exe_path} {launch_args}", f"Starting {exe_path} {launch_args}"))

        try:
            process = subprocess.Popen([exe_path] + launch_args)
        except Exception as e:
            if logger:
                logger.error(ui_text(f"启动进程失败: {e}", f"Failed to spawn process: {e}"))
            return {"ok": False, "error": ui_text(f"failed to spawn process: {e}", f"Failed to spawn process: {e}")}

        _last_game_process = process
        _last_launch_ts = time.time()
        return {
            "ok": True,
            "already_running": False,
            "pid": process.pid,
            "exe_path": exe_path,
            "args": launch_args,
            "process": process,
        }

