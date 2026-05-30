import psutil
import pygetwindow as gw
import win32gui
import win32process

# Known JetBrains IDE executable names
JETBRAINS_PROCESSES = ["pycharm64.exe", "idea64.exe", "webstorm64.exe", "clion64.exe"]


def get_active_app_name():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = psutil.Process(pid)
    return process.name()


def get_active_jetbrains_project():
    # 1. Check if any JetBrains process is running
    ide_running = any(p.name().lower() in JETBRAINS_PROCESSES for p in psutil.process_iter())
    if not ide_running:
        return "IDE Closed", None

    # 2. Extract project name from the foreground active window title
    try:
        active_win = gw.getActiveWindow()
        if active_win and active_win.title:
            title = active_win.title
            app_name = get_active_app_name()
            # JetBrains windows usually format as: "project_name [path] - File.py" or contain the IDE name
            if app_name in JETBRAINS_PROCESSES:
                # Extract project name (it is typically the first word or string before the path bracket)
                project_name = title.split(" [")[0] if " [" in title else title.split(" – ")[0]
                return "IDE Open (Focused)", project_name.strip()
    except Exception:
        pass

    return "IDE Open (Background)", None
