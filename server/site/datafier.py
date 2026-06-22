import json
import math
from datetime import date, timedelta, datetime, time
from pathlib import Path

from github import Github
from github.Repository import Repository

try:
    with open(Path(__file__).resolve().parent.parent / "key.txt", "r") as f:
        key = f.readlines()[0].strip()
    if key != "":
        g = Github(key)
    else:
        g = Github()
except Exception as e:
    print(e)


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
    file_path = Path(__file__).resolve().parent.parent / "project_list.json"
    with open(file_path, "r") as f:
        return json.load(f)


def read_data() -> dict:
    file_path = Path(__file__).resolve().parent.parent / "data.json"
    with open(file_path, "r") as f:
        return json.load(f)


def read_key() -> str:
    with open(Path(__file__).resolve().parent.parent / "key.txt", "r") as f:
        return f.readlines()[0].strip()

def read_user() -> str:
    with open(Path(__file__).resolve().parent.parent / "key.txt", "r") as f:
        return f.readlines()[1].strip()

def write_key(key: str):
    with open(Path(__file__).resolve().parent.parent / "key.txt", "r") as f:
        user = f.readlines()[1].strip()
    with open(Path(__file__).resolve().parent.parent / "key.txt", "w") as f:
        f.write(key.strip() + "\n" + user.strip())

def write_user(user: str):
    with open(Path(__file__).resolve().parent.parent / "key.txt", "r") as f:
        key = f.readlines()[0].strip()
    with open(Path(__file__).resolve().parent.parent / "key.txt", "w") as f:
        f.write(key.strip() + "\n" + user.strip())


def get_data_by_project() -> dict:
    data = read_data()
    result = {}

    for key, value in data.items():
        value.pop("device_name")
        result = combine(result, value)

    return result


def get_time_in_week_combined(project: dict) -> list[float]:
    per_branch = project["per_branch"]
    data = {}

    for key, value in per_branch.items():
        data = combine(data, value)

    result_data = {(date.today() - timedelta(days=i)).strftime("%D"): 0 for i in range(6, -1, -1)}
    for key, value in data.items():
        k = key.split(" ")[0]
        if k in result_data.keys():
            result_data[k] += value

    return list(result_data.values())


def get_time_in_day(projects: dict, labels: list, hours: int) -> dict[str, list[float]]:
    result = {}
    for project_key, project_data in projects.items():
        result_data = {l: 0 for l in labels}

        for date_key, data in project_data.items():
            if date_key == "total": continue
            day = date_key.split(" ")[0]
            hour = str(math.ceil(int(date_key.split(" ")[1][:-1]) / hours) * hours)
            if len(hour) == 1: hour = "0" + hour
            extra_day = hour == "24"
            if extra_day: hour = "00"

            key = (datetime.strptime(day + " " + hour, "%m/%d/%y %H") +
                   timedelta(hours=int(datetime.now().strftime("%H")) % 2 + 24 if extra_day else 0)).strftime("%D %Hh")
            if key in result_data.keys():
                result_data[key] += data

        result[project_key] = list(result_data.values())

    return result


def get_time_in_week(projects: dict, labels: list) -> dict[str, list[float]]:
    result = {}
    for project_key, project_data in projects.items():
        result_data = {l: 0 for l in labels}

        for date_key, data in project_data.items():
            if date_key == "total": continue
            day = date_key.split(" ")[0]
            if day in result_data.keys():
                result_data[day] += data

        result[project_key] = list(result_data.values())

    return result


def get_time_in_month(projects: dict, labels: list, days: int) -> dict[str, list[float]]:
    result = {}
    for project_key, project_data in projects.items():
        result_data = {l: 0 for l in labels}

        for date_key, data in project_data.items():
            if date_key == "total": continue
            date_info = date_key.split(" ")[0]
            day = str(math.ceil(int(date_info.split("/")[1]) / days) * days)
            if len(day) == 1: day = "0" + day

            key = (datetime.strptime(date_info.split("/")[0] + "/" + day + "/" + date_info.split("/")[2], "%m/%d/%y") +
                   timedelta(days=int(day) % days) + timedelta(days=int(datetime.now().strftime("%d")) % days)).strftime("%D")
            if key in result_data.keys():
                result_data[key] += data

        result[project_key] = list(result_data.values())

    return result


def get_time_in_year(projects: dict, labels: list) -> dict[str, list[float]]:
    result = {}
    for project_key, project_data in projects.items():
        result_data = {l: 0 for l in labels}

        for date_key, data in project_data.items():
            if date_key == "total": continue
            date = date_key.split(" ")[0]
            month = date.split("/")[0]
            if len(month) == 1: month = "0" + month

            key = month + " " + date.split("/")[2]
            if key in result_data.keys():
                result_data[key] += data

        result[project_key] = list(result_data.values())

    return result


def get_commits_data_set(commits_per_branch: dict[str, list[dict[str, str]]], dates: list[datetime]) -> dict[str, dict[float, dict[str, str]]]:
    result = {}
    h_step = (dates[1] - dates[0]).total_seconds() / 3600

    for branch, commits in commits_per_branch.items():
        result_data = {}

        for commit in commits:
            commit_date = datetime.strptime(commit["date"], "%Y-%m-%d %H:%M:%S")
            step = (commit_date - dates[0]).total_seconds() / 3600

            if step < 0 or step > (dates[-1] - dates[0]).total_seconds() / 3600:
                continue

            index = step / h_step
            result_data[index] = commit

        result[branch] = result_data

    return result


def get_project_data_set(project_data: dict, commits_per_branch: dict) -> dict[str, dict]:
    return {
        "day": {
            "labels": [(datetime.now() - timedelta(hours=i*2)).strftime("%A %Hh") for i in range(11, 1, -1)] + ["2h ago", "Now"],
            "data_sets": get_time_in_day(project_data["per_branch"], [(datetime.now() - timedelta(hours=i*2)).strftime("%D %Hh") for i in range(11, -1, -1)], 2),
            "commits": get_commits_data_set(commits_per_branch, [datetime.combine(date.today() - timedelta(hours=i*2), time(0, 0)) for i in range(11, -1, -1)]),
        },
        "week": {
            "labels": [(date.today() - timedelta(days=i)).strftime("%A %d") for i in range(6, 1, -1)] + ["Yesterday", "Today"],
            "data_sets": get_time_in_week(project_data["per_branch"], [(date.today() - timedelta(days=i)).strftime("%D") for i in range(6, -1, -1)]),
            "commits": get_commits_data_set(commits_per_branch, [datetime.combine(date.today() - timedelta(days=i), time(0, 0)) for i in range(6, -1, -1)]),
        },
        "month": {
            "labels": [(date.today() - timedelta(days=i*3)).strftime("%d/%b/%y") for i in range(9, 1, -1)] + ["3d ago", "Today"],
            "data_sets": get_time_in_month(project_data["per_branch"], [(date.today() - timedelta(days=i*3)).strftime("%D") for i in range(9, -1, -1)], 3),
            "commits": get_commits_data_set(commits_per_branch, [datetime.combine(date.today() - timedelta(days=i*3), time(0, 0)) for i in range(9, -1, -1)]),
        },
        "year": {
            "labels": [(date.today() - timedelta(days=i*30)).strftime("%B %y") for i in range(11, -1, -1)],
            "data_sets": get_time_in_year(project_data["per_branch"], [(date.today() - timedelta(days=i*30)).strftime("%m %y") for i in range(11, -1, -1)]),
            "commits": get_commits_data_set(commits_per_branch, [datetime.combine(date.today() - timedelta(days=i*30), time(0, 0)) for i in range(11, -1, -1)]),
        },
    }


def get_time_per_language(project_data: dict, repos: dict) -> dict[str, list[dict]]:
    result = {}
    for project, data in project_data.items():
        language = get_project_language(read_project_list()[project], repos[project])
        combined_branches = {}
        for branch in data["per_branch"].values():
            combined_branches = combine(combined_branches, branch)
        if language not in result.keys():
            result[language] = {}
        result[language] = combine(combined_branches, result[language])

    return result


def get_overview_data_set(project_data: dict) -> dict[str, dict]:
    return {
        "day": {
            "labels": [(datetime.now() - timedelta(hours=i*2)).strftime("%A %Hh") for i in range(11, 1, -1)] + ["2h ago", "Now"],
            "data_sets": get_time_in_day(project_data, [(datetime.now() - timedelta(hours=i*2)).strftime("%D %Hh") for i in range(11, -1, -1)], 2),
        },
        "week": {
            "labels": [(date.today() - timedelta(days=i)).strftime("%A %d") for i in range(6, 1, -1)] + ["Yesterday", "Today"],
            "data_sets": get_time_in_week(project_data, [(date.today() - timedelta(days=i)).strftime("%D") for i in range(6, -1, -1)]),
        },
        "month": {
            "labels": [(date.today() - timedelta(days=i*3)).strftime("%d/%b/%y") for i in range(9, 1, -1)] + ["3d ago", "Today"],
            "data_sets": get_time_in_month(project_data, [(date.today() - timedelta(days=i*3)).strftime("%D") for i in range(9, -1, -1)], 3),
        },
        "year": {
            "labels": [(date.today() - timedelta(days=i*30)).strftime("%B %y") for i in range(11, -1, -1)],
            "data_sets": get_time_in_year(project_data, [(date.today() - timedelta(days=i*30)).strftime("%m %y") for i in range(11, -1, -1)]),
        },
    }


def get_commit_number(repos, projects_and_languages: dict[str, str], begin: datetime) -> dict[str, int]:
    result = {}

    for project, language in projects_and_languages.items():
        if project not in repos.keys(): continue

        for branch, commits in repos[project]["commits_per_branch"].items():

            for commit in commits:
                commit_date = datetime.strptime(commit["date"], "%Y-%m-%d %H:%M:%S")
                step = (commit_date - begin).total_seconds()

                if language not in result.keys():
                    result[language] = 0

                if step >= 0:
                    result[language] += 1

    return result


def get_project_number(project_data: dict, days: int) -> int:
    total = 0
    for project, data in project_data.items():
        for branch, times in data["per_branch"].items():
            if branch == "total": continue
            latest_update = datetime.strptime(list(times.keys())[-1], "%m/%d/%y %Hh")
            delta = (datetime.now() - latest_update).total_seconds() / (60 * 60 * 24)
            if delta < days:
                total += 1
                break
    return total


def get_most_used_language(project_data: dict, repos: dict, days: int) -> str:
    language_time = {}
    for project, data in project_data.items():
        for branch, times in data["per_branch"].items():
            if branch == "total": continue
            latest_update = datetime.strptime(list(times.keys())[-1], "%m/%d/%y %Hh")
            delta = (datetime.now() - latest_update).total_seconds() / (60 * 60 * 24)
            if delta < days:
                language = get_project_language(read_project_list()[project], repos[project])
                total_time = sum(times.values())
                if language not in language_time.keys():
                    language_time[language] = 0
                language_time[language] += total_time

    most_used_language = "Unknown"
    max_time = 0
    for language, time in language_time.items():
        if time > max_time:
            most_used_language = language
            max_time = time

    return most_used_language


def get_project_with_most_time(project_data: dict, days: int) -> str:
    project_time = {}
    for project, data in project_data.items():
        for branch, times in data["per_branch"].items():
            if branch == "total": continue
            latest_update = datetime.strptime(list(times.keys())[-1], "%m/%d/%y %Hh")
            delta = (datetime.now() - latest_update).total_seconds() / (60 * 60 * 24)
            if delta < days:
                total_time = sum(times.values())
                project_time[project] = total_time

    most_used_project = "Unknown"
    max_time = 0
    for project, time in project_time.items():
        if time > max_time:
            most_used_project = project
            max_time = time

    return most_used_project


def get_info_per_time_frame(data_by_project: dict, overview_data_sets: dict, repos: dict, projects_and_languages: dict[str, str]) -> dict:
    return {
        time: {
            "total_time": sum(sum(times) for times in overview_data_sets[time]["data_sets"].values()),
            "average_per_day": round(sum(sum(times) for times in overview_data_sets[time]["data_sets"].values()) / days),
            "project_nb": get_project_number(data_by_project, days),
            "commit_nb": get_commit_number(repos, projects_and_languages, datetime.now() - timedelta(days=days)),
            "total_commit_nb": sum([t for time, t in get_commit_number(repos, projects_and_languages, datetime.now() - timedelta(days=days)).items()]),
            "most_used_language": get_most_used_language(data_by_project, repos, days),
            "project_with_most_time": get_project_with_most_time(data_by_project, days),
        } for time, days in {"day": 1, "week": 7, "month": 30, "year": 365}.items()
    }


def get_repo(user: str, name: str) -> tuple[Repository | None, bool]:
    try:
        return g.get_repo(f"{user}/{name}"), False
    except Exception as e: # If the rate limit for unauthenticated requests (60) is reached
        print(e, user, name)
        return None, "404" not in str(e) # Error can also be 404 not found


def get_repo_info(remote_url: str) -> tuple[dict, bool]:
    file_path = Path(__file__).resolve().parent.parent / "repo_info.json"
    with open(file_path, "r") as f:
        d = json.load(f)

    info = remote_url[:-4].split("/")

    if info[-1] in d.keys():
        if datetime.now() - datetime.strptime(d[info[-1]]["last_updated"], "%Y-%m-%d %H:%M:%S") < timedelta(days=1):
            return d[info[-1]], False

    repo, rate_limit_reached = get_repo(info[-2], info[-1])
    if repo:
        repo_info = {
            "found": True,
            "language": repo.language,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": repo.description,
            "commit_number": sum([repo.get_commits(sha=branch.name).totalCount for branch in repo.get_branches()]),
            "commits_per_branch": {branch.name: [{
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.strftime("%Y-%m-%d %H:%M:%S"),
                "message": commit.commit.message.splitlines()[0],
            } for commit in repo.get_commits(sha=branch.name)[:100]]
            for branch in repo.get_branches()},
        }
    else:
        repo_info = {
            "found": False,
            "language": None,
            "description": None,
            "commit_number": 0,
            "commits_per_branch": {},
        }

    d[info[-1]] = repo_info
    with open(file_path, "w") as f:
        json.dump(d, f, indent=2)

    return repo_info, rate_limit_reached


def read_and_update_repo_info(project_urls: dict) -> tuple[dict, bool]:
    d = {}

    rate_limit_reached = False
    for project, url in project_urls.items():
        repo_info, rate_limit_reached = get_repo_info(url)
        d[project] = repo_info
        if rate_limit_reached:
            break

    return d, rate_limit_reached


def get_project_language(project: dict, repo: dict) -> str:
    if project["remote_url"].endswith(".git") and repo["found"]:
        return repo["language"]

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
        if key in project["ide"].lower():
            return value

    return "Language Unknown"


def get_project_description(project: dict, repo: dict, cutoff: int = 0) -> str:
    if project["remote_url"].endswith(".git") and repo["found"]:
        d = repo["description"]
        if 0 < cutoff < len(d): d = d[:cutoff] + "..."
        return d

    return "Description Unknown"