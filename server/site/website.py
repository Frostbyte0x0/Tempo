import logging
import sys

from flask import Flask, render_template, request

from datafier import *

app = Flask(__name__)

# noinspection PyArgumentList
logging.basicConfig(
    encoding='utf-8',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("website.log", mode="w"),
        logging.StreamHandler(sys.stdout)
    ],
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# TODO:
# - Overview tab, show total with list of languages
# - Finish project view
#   - Branches
#   - Time frame selection
#   - Time frame info
#   - Commit placement
# - Check PAT key github
# - Sorting on list page
# - Link with github info and sync


@app.route("/")
def main():
    user_input = request.args.get('text_data', '')
    if user_input != "":
        write_key(user_input)

    project_list = read_project_list()
    project_data = get_data_by_project()
    repos, needs_key = read_and_update_repo_info({project: project_list[project]["remote_url"] for project in project_data.keys()})
    data_sets = {project: get_time_in_week(project_data[project]) for project in project_data.keys()}
    languages = {project: get_project_language(project_list[project], repos[project]) for project in project_data.keys()}
    descriptions = {project: get_project_description(project_list[project], repos[project], 45) for project in project_data.keys()}

    return render_template("list.html",
        data={
            "project_list": project_list,
            "project_data": project_data,
            "labels": [(date.today() - timedelta(days=i)).strftime("%D") for i in range(6, 1, -1)] + ["Yesterday", "Today"],
            "data_sets": data_sets,
            "languages": languages,
            "descriptions": descriptions,
            "needs_key": needs_key,
        },
        user_input=user_input
    )


@app.route("/project/<project>")
def project(project):
    project_list = read_project_list()
    repo, needs_key = get_repo_info(project_list[project]["remote_url"])

    project_data = get_data_by_project()
    if project not in project_data:
        project_data = {"total": 0}
        data_set = [0, 0, 0, 0, 0, 0, 0]
    else:
        project_data = project_data[project]
        data_set = get_time_in_week(project_data)

    language = get_project_language(project_list[project], repo)
    description = get_project_description(project_list[project], repo)

    return render_template("project.html", data={
        "project": project,
        "project_data": project_data,
        "labels": [(date.today() - timedelta(days=i)).strftime("%D") for i in range(6, 1, -1)] + ["Yesterday", "Today"],
        "data_set": data_set,
        "branches": data_set, #
        "commits_per_branch": data_set, #
        "language": language,
        "description": description,
        "github_link": project_list[project]["remote_url"],
        "nb_commits": description, #
        "needs_key": needs_key,
    })


@app.route("/overview")
def overview():
    project_list = read_project_list()
    project_data = get_data_by_project()["Tempo"]

    repos, needs_key = read_and_update_repo_info({project: project_list[project]["remote_url"] for project in project_data.keys()})

    data_set = get_time_in_week(project_data)

    return render_template("overview.html", data={
        "project_data": project_data,
        "labels": [(date.today() - timedelta(days=i)).strftime("%D") for i in range(6, 1, -1)] + ["Yesterday", "Today"],
        "data_set": data_set,
        "needs_key": needs_key,
    })

if __name__ == "__main__":
    try:
        app.run(debug=True)
    except Exception as e:
        logging.exception(e)
