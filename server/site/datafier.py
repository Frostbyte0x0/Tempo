import json
from datetime import date, timedelta
from pathlib import Path

from github import Github
from github.Repository import Repository

try:
    with open(Path(__file__).resolve().parent.parent / "key.txt", "r") as f:
        key = f.read().strip()
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


def write_key(key: str):
    with open(Path(__file__).resolve().parent.parent / "key.txt", "w") as f:
        f.write(key.strip())


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
    for key, value in data.items():
        k = key.split(" ")[0]
        if k in result_data.keys():
            result_data[k] += value

    return list(result_data.values())


def get_time_in_week_per_branch(project: dict) -> dict[str, list[float]]:
    per_branch = project["per_branch"]

    result = {}
    for branch, branch_data in per_branch.items():
        result_data = {(date.today() - timedelta(days=i)).strftime("%D"): 0 for i in range(6, -1, -1)}
        for date_key, data in branch_data.items():
            day = date_key.split(" ")[0]
            if day in result_data.keys():
                result_data[day] += data
        result[branch] = list(result_data.values())

    return result


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
        return d[info[-1]], False

    repo, rate_limit_reached = get_repo(info[-2], info[-1])
    if repo:
        repo_info = {
            "found": True,
            "language": repo.language,
            "description": repo.description,
            "commit_number": repo.get_commits().totalCount,
            "commits_per_branch": {branch.name: [{
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.strftime("%Y-%m-%d %H:%M:%S"),
                "message": commit.commit.message.splitlines()[0],
            } for commit in repo.get_commits(sha=branch.name)[:50]]
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