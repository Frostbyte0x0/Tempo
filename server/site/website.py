import json
from pathlib import Path

from flask import Flask, render_template

app = Flask(__name__)


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


@app.route("/")
def main():
    project_list = read_project_list()
    project_data = get_data_by_project()
    print(project_data)
    return render_template('overview.html', project_list=project_list, project_data=project_data)


@app.route('/project/<project>')
def show_user_profile(project):
    project_list = read_project_list()

    return render_template('project.html', project_list=project_list)
