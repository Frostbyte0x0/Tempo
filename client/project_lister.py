import os
import re
from pathlib import Path

import xmltodict


def get_git_info(project_path):
    """
    Inspects the project folder to extract the current Git branch and remote URL.
    Bypasses external CLI dependencies for optimal performance.
    """
    git_dir = Path(project_path) / ".git"
    if not git_dir.exists():
        return {"status": "Not a Git Repository", "branch": None, "remote_url": None}

    branch = None
    remote_url = None

    try:
        # 1. Extract Current Branch name from .git/HEAD
        head_file = git_dir / "HEAD"
        if head_file.exists():
            head_content = head_file.read_text().strip()
            if head_content.startswith("ref:"):
                branch = head_content.split("refs/heads/")[-1]
            else:
                branch = f"Detached HEAD ({head_content[:7]})"

        # 2. Extract Remote URL from .git/config
        config_file = git_dir / "config"
        if config_file.exists():
            config_content = config_file.read_text()
            # Regex to find the url field underneath the [remote "origin"] block
            remote_match = re.search(r'\[remote\s+"origin"\][^\[]*url\s*=\s*([^\n]+)', config_content)
            if remote_match:
                remote_url = remote_match.group(1).strip()

        return {
            "status": "Git Connected",
            "branch": branch or "Unknown",
            "remote_url": remote_url or "No remote origin configured"
        }
    except Exception:
        return {"status": "Error parsing Git metadata", "branch": None, "remote_url": None}


def get_active_projects_with_git() -> dict[str, dict[str, str]]:
    """Reads JetBrains metadata logs and pairs paths with local Git diagnostics."""
    if os.name == 'nt':
        config_base = Path(os.environ.get('APPDATA', '')) / "JetBrains"
    elif os.name == 'posix':
        if os.uname().sysname == 'Darwin':
            config_base = Path.home() / "Library/Application Support/JetBrains"
        else:
            config_base = Path.home() / ".config/JetBrains"
    else:
        return {}

    if not config_base.exists():
        return {}

    processed_paths = set()
    aggregated_results = {}

    for ide_dir in config_base.iterdir():
        recent_projects_xml = ide_dir / "options" / "recentProjects.xml"
        xml_map = {}

        if not recent_projects_xml.exists():
            recent_projects_xml = ide_dir / "options" / "recentSolutions.xml"
            if not recent_projects_xml.exists():
                continue

        try:
            with open(recent_projects_xml) as xml_file:
                xml_map = xmltodict.parse(xml_file.read())
            entries = xml_map["application"]["component"]["option"][0]["map"]["entry"]

            if type(entries) is not list:
                entries = [entries]

            for entry in entries:
                path_str = entry["@key"].replace("$USER_HOME$", str(Path.home())).replace("/", "\\")
                if path_str.endswith(".sln"):
                    path_str = "\\".join(entry["@key"].replace("$USER_HOME$", str(Path.home())).replace("/", "\\").split("\\")[:-1])
                if path_str in processed_paths or not os.path.exists(path_str): continue

                processed_paths.add(path_str)
                git_data = get_git_info(path_str)

                if git_data["branch"] and git_data["remote_url"]:
                    aggregated_results.update({
                                    os.path.basename(path_str): {
                                    "ide": ide_dir.name,
                                    "project_name": os.path.basename(path_str),
                                    "local_path": path_str.replace("/", "\\"),
                                    **git_data
                                }})
        except Exception:
            continue

    return aggregated_results

if __name__ == "__main__":
    print(get_active_projects_with_git())
