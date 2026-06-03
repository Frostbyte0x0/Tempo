import json
import socket
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
        logging.FileHandler("client.log", mode="w"),
        logging.StreamHandler(sys.stdout)
    ],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

t = 5  # Time interval in seconds for tracking

# TODO:
# - When connected to server, send data and sync


def read_data() -> dict:
    with open("data.json", "r") as f:
        return json.load(f)

def write_data(data: dict):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)


def increase_time(data: dict, project: str, branch: str):
    if not project:
        return

    hour = time.strftime("%D %Hh")

    if project in data:
        data[project]["total"] += t

        if branch in data[project]["per_branch"]:
            data[project]["per_branch"][branch]["total"] += t

            if hour in data[project]["per_branch"][branch]:
                data[project]["per_branch"][branch][hour] += t
            else:
                data[project]["per_branch"][branch][hour] = t

        else:
            data[project]["per_branch"][branch] = {
                "total": t
            }

    else:
        data[project] = {
            "total": t,
            "per_branch": {
                branch: {
                    "total": t,
                    hour: t
                }
            }
        }


def detect() -> dict[str, dict[str, str]] | None:
    # Execute combined diagnostic tool
    project_reports = get_active_projects_with_git()

    if project_reports:
        with open("project_list.json", "w") as f:
            json.dump(project_reports, f, indent=2)
            f.write("\n")

        for idx, report in enumerate(project_reports.values(), 1):
            logging.info(f"--- [Active Project #{idx}] ---")
            logging.info(f"Target IDE:    {report['ide']}")
            logging.info(f"Project Name:  {report['project_name']}")
            logging.info(f"Local Path:    {report['local_path']}")
            logging.info(f"Git Status:    {report['status']}")
            if report['branch']:
                logging.info(f"Active Branch: {report['branch']}")
            if report['remote_url']:
                logging.info(f"Remote URL:    {report['remote_url']}")
            logging.info("----------------------------")

        return project_reports
    else:
        logging.info("Could not find any active projects tracked in JetBrains configs.")
    return None


def sync(client_data):
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.connect(("localhost", 8080))

    try:
        message = json.dumps(client_data)
        c.sendall(message.encode('utf-8'))
    finally:
        c.close()


def track(project_reports: dict[str, dict[str, str]]):
    # Continuous tracking loop
    data = read_data()
    data["device_name"] = socket.gethostname()

    last_state = None
    while True:
        state, project = get_active_jetbrains_project()
        current_state = f"{state} | Active Project: {project}" if project else state

        if current_state != last_state:
            logging.debug(f"{current_state}")
            last_state = current_state

        if project:
            increase_time(data, project, project_reports[project]["branch"])
            write_data(data)

        sync(data)

        time.sleep(t)


if __name__ == "__main__":
    project_reports = detect()
    if project_reports:
        track(project_reports)
    else:
        logging.info("Could not find any active projects tracked in JetBrains configs.")
