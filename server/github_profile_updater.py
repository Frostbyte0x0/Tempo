import base64
import math
from datetime import datetime

import requests

from server.site.datafier import (read_project_list, get_data_by_project, read_and_update_repo_info,
                                  get_time_per_language,
                                  get_overview_data_set, get_info_per_time_frame, get_project_language)


def read_key() -> str:
    with open("key.txt", "r") as f:
        return f.readlines()[0].strip()

def read_user() -> str:
    with open("key.txt", "r") as f:
        return f.readlines()[1].strip()


def update_profile() -> tuple[bool, str]:
    project_list = read_project_list()
    project_data = get_data_by_project()
    repos, needs_key = read_and_update_repo_info({project: project_list[project]["remote_url"] for project in project_data.keys()})
    data_sets = get_overview_data_set(get_time_per_language(project_data, repos))

    frame_info = get_info_per_time_frame(project_data, data_sets, repos,
                                         {project: get_project_language(project_list[project], repos[project]) for project in project_data.keys()})


    USERNAME = read_user()
    TOKEN = read_key()

    url = f"https://api.github.com/repos/{USERNAME}/{USERNAME}/contents/README.md"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Python-Requests-Script"
    }

    response = requests.get(url, headers=headers)
    response_data = response.json()

    sha = response_data.get("sha") if response.status_code == 200 else None

    new_content = f"""
# Time stats from Tempo, last updated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} 

# In the past year (or since June 20th 2026 (when the timer started)): 
+ Total time spent coding: {math.floor(frame_info["year"]["total_time"] / 60)}h {frame_info["year"]["total_time"] % 60}m
+ Average per day: {math.floor(frame_info["year"]["average_per_day"] / 60)}h {frame_info["year"]["average_per_day"] % 60}m
+ Nb of commits made: {frame_info["year"]["total_commit_nb"]}
+ Nb of projects worked on: {frame_info["year"]["project_nb"]}
+ Project with most time: {frame_info["year"]["project_with_most_time"]}
+ Most used language: {frame_info["year"]["most_used_language"]}

# In the past month: 
+ Total time spent coding: {math.floor(frame_info["month"]["total_time"] / 60)}h {frame_info["month"]["total_time"] % 60}m
+ Average per day: {math.floor(frame_info["month"]["average_per_day"] / 60)}h {frame_info["month"]["average_per_day"] % 60}m
+ Nb of commits made: {frame_info["month"]["total_commit_nb"]}
+ Nb of projects worked on: {frame_info["month"]["project_nb"]}
+ Project with most time: {frame_info["month"]["project_with_most_time"]}
+ Most used language: {frame_info["month"]["most_used_language"]}
"""

    encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    data = {
        "message": "docs: update profile readme with latest coding stats",
        "content": encoded_content,
    }
    if sha:
        data["sha"] = sha

    put_response = requests.put(url, headers=headers, json=data)

    if put_response.status_code in [200, 201]:
        return True, "Success! Your profile README has been updated and is live."
    else:
        return False, f"Failed to update profile: {put_response.status_code}"


if __name__ == "__main__":
    update_profile()
