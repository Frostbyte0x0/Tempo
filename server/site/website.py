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
    else:
        project_data = project_data[project]

    language = get_project_language(project_list[project], repo)
    description = get_project_description(project_list[project], repo)

    time_frames = {
        "day":{
            "labels": [(datetime.now() - timedelta(hours=i*2)).strftime("%A %Hh") for i in range(11, 1, -1)] + ["2h ago", "Now"],
            "data_sets": get_time_in_day_per_branch(project_data, [(datetime.now() - timedelta(hours=i*2)).strftime("%D %Hh") for i in range(11, -1, -1)], 2),
        },
        "week":{
            "labels": [(date.today() - timedelta(days=i)).strftime("%A %d") for i in range(6, 1, -1)] + ["Yesterday", "Today"],
            "data_sets": get_time_in_week_per_branch(project_data, [(date.today() - timedelta(days=i)).strftime("%D") for i in range(6, -1, -1)]),
        },
        "month":{
            "labels": [(date.today() - timedelta(days=i*3) + timedelta(days=1)).strftime("%d/%b/%y") for i in range(9, 1, -1)] + ["3d ago", "Today"],
            "data_sets": get_time_in_month_per_branch(project_data, [(date.today() - timedelta(days=i*3) + timedelta(days=1)).strftime("%D") for i in range(9, -1, -1)], 3),
        },
        # "3 months":{
        #     "labels": [(date.today() - timedelta(days=i*9) + timedelta(days=1)).strftime("%d/%b/%y") for i in range(9, 1, -1)] + ["9d ago", "Today"],
        #     "data_sets": get_time_in_month_per_branch(project_data, [(date.today() - timedelta(days=i*9) + timedelta(days=1)).strftime("%D") for i in range(9, -1, -1)], 9),
        # },
        # "6 months":{
        #     "labels": [(date.today() - timedelta(days=i*18) + timedelta(days=1)).strftime("%d/%b/%y") for i in range(9, 1, -1)] + ["18d ago", "Today"],
        #     "data_sets": get_time_in_month_per_branch(project_data, [(date.today() - timedelta(days=i*18) + timedelta(days=1)).strftime("%D") for i in range(9, -1, -1)], 18),
        # },
        "year":{
            "labels": [(date.today() - timedelta(days=i*30)).strftime("%B %y") for i in range(11, -1, -1)],
            "data_sets": get_time_in_year_per_branch(project_data, [(date.today() - timedelta(days=i*30)).strftime("%m %y") for i in range(11, -1, -1)]),
        },
    }

    return render_template("project.html", data={
        "project": project,
        "project_data": project_data,
        "frames": list(time_frames.keys()),
        "time_frames": time_frames,
        "commits_per_branch": repo["commits_per_branch"],
        "language": language,
        "description": description,
        "github_link": project_list[project]["remote_url"][:-4],
        "commit_number": repo["commit_number"],
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
