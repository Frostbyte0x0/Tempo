import json
from datetime import date, timedelta
from pathlib import Path
from github import Github

from flask import Flask, render_template

app = Flask(__name__)
g = Github()


def combine(d1:dict, d2:dict) -> dict:
    for key, value in d2.items():
        if type(value) == dict:
            if key in d1.keys():
                d1[key] = combine(d1[key], value)
            else:
                d1[key] = value
        else:
            if key in d1.keys():
                d1[key] += value
            else:
                d1[key] = value
    return d1

def read_project_list() -> dict:
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    file_path = parent_dir / "project_list.json"
    with open(file_path, "r") as f:
        return json.load(f)

def read_data() -> dict:
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    file_path = parent_dir / "data.json"
    with open(file_path, "r") as f:
        return json.load(f)

def get_data_by_project() -> dict:
    data = read_data()
    result = {}

    for key, value in data.items():
        value.pop("device_name")
        result = combine(result, value)

    return result

def get_time_in_week(project: dict) -> list[float]:
    per_branch = project["per_branch"]
    data = {}

    for key, value in per_branch.items():
        data = combine(data, value)

    result_data = {(date.today() - timedelta(days=i)).strftime("%D"): 0 for i in range(6, -1, -1)}
    print(result_data)
    for key, value in data.items():
        k = key.split(" ")[0]
        if k in result_data.keys():
            result_data[k] += value

    return list(result_data.values())

def get_project_language(project: dict) -> str:
    if project["remote_url"].endswith(".git"):
        info = project["remote_url"][:-4].split("/")
        repo = g.get_repo(f"{info[-2]}/{info[-1]}")
        return repo.language

    language_by_ide = {
        "ideaic": "Java",
        "intellij": "Java",
        "pycharm": "Python",
        "rider": "C#",
        "webstorm": "JavaScript",
        "goland": "Go",
        "clion": "C++",
        "ruby": "Ruby",
        "php": "PHP"
    }

    for key, value in language_by_ide.items():
        if key in project["ide"]:
            return value

    return "Language Unknown"

def get_project_description(project: dict, cutoff: int = 0) -> str:
    if project["remote_url"].endswith(".git"):
        info = project["remote_url"][:-4].split("/")
        repo = g.get_repo(f"{info[-2]}/{info[-1]}")
        d = repo.description
        if 0 < cutoff < len(d): d = d[:cutoff] + "..."
        return d

    return "Description Unknown"


@app.route("/")
def main():
    project_list = read_project_list()
    project_data = get_data_by_project()
    data_sets = {project: get_time_in_week(project_data[project]) for project in project_data.keys()}
    languages = {project: get_project_language(project_list[project]) for project in project_data.keys()}
    descriptions = {project: get_project_description(project_list[project], 45) for project in project_data.keys()}

    return render_template('overview.html', data={
        "project_list": project_list,
        "project_data": project_data,
        "labels": [(date.today() - timedelta(days=i)).strftime('%D') for i in range(6, 1, -1)] + ["Yesterday", "Today"],
        "data_sets": data_sets,
        "languages": languages,
        "descriptions": descriptions,
    })


@app.route('/project/<project>')
def show_user_profile(project):
    project_list = read_project_list()

    return render_template('project.html', project_list=project_list)
