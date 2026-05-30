import json
import sys
import time

from project_lister import get_active_projects_with_git
from scanner import get_active_jetbrains_project
import logging

# Configure logging to save to a file
# noinspection PyArgumentList
logging.basicConfig(
    encoding='utf-8',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("app.log", mode="w"),
        logging.StreamHandler(sys.stdout)
    ],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Example log entries
logging.debug("This is a debug message")
logging.info("This is an info message")
logging.warning("This is a warning message")
logging.error("This is an error message")

# TODO:
# - Detect project list
# - Scan for open IDE and project
# - Add time in local data JSON
# - When connected to server, send data and sync


def detect() -> bool:
    # Execute combined diagnostic tool
    project_reports = get_active_projects_with_git()

    if project_reports:
        with open("project_list.json", "w") as f:
            json.dump({"projects": project_reports}, f, indent=2)
            f.write("\n")

        for idx, report in enumerate(project_reports, 1):
            logging.info(f"--- [Active Project #{idx}] ---")
            logging.info(f"Target IDE:    {report['ide']}")
            logging.info(f"Project Name:  {report['project_name']}")
            logging.info(f"Local Path:    {report['local_path']}")
            logging.info(f"Git Status:    {report['status']}")
            if report['branch']:
                logging.info(f"Active Branch: {report['branch']}")
            if report['remote_url']:
                logging.info(f"Remote URL:    {report['remote_url']}")
            logging.info("-----------------------------")

        return True
    else:
        logging.info("Could not find any active projects tracked in JetBrains configs.")
    return False


def track():
    # Continuous tracking loop
    last_state = None
    while True:
        state, project = get_active_jetbrains_project()
        current_state = f"{state} | Active Project: {project}" if project else state

        if current_state != last_state:
            logging.debug(f"{current_state}")
            last_state = current_state

        time.sleep(1)


if __name__ == "__main__":
    detect()
    track()
