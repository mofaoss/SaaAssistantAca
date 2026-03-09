import win32api
import win32con
import win32gui


def is_fullscreen(hwnd):
    window_rect = win32gui.GetWindowRect(hwnd)
    window_width = window_rect[2] - window_rect[0]
    window_height = window_rect[3] - window_rect[1]

    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    return window_width == screen_width and window_height == screen_height


def enumerate_child_windows(parent_hwnd):
    def callback(handle, windows):
        windows.append(handle)
        return True

    child_windows = []
    win32gui.EnumChildWindows(parent_hwnd, callback, child_windows)
    return child_windows


def get_hwnd(window_title, window_class):
    hwnd = win32gui.FindWindow(None, window_title)
    handle_list = []
    if hwnd:
        handle_list.append(hwnd)
        handle_list.extend(enumerate_child_windows(hwnd))
        for handle in handle_list:
            class_name = win32gui.GetClassName(handle)
            if class_name == window_class:
                return handle
    return None

