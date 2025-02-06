import csv
import os
from typing import Optional
from collections import defaultdict

import requests
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

from icons import LANG_LOOKUP

# Load environment variables
load_dotenv()


def get_github_repos(token: str) -> list:
    """
    Fetches the list of GitHub repositories for the authenticated user.

    Args:
        token (str): GitHub personal access token for authentication.

    Returns:
        list: A list of dictionaries representing the user's repositories.
    """
    url = f"https://api.github.com/user/repos"
    headers = {"Authorization": f"token {token}"}
    repos = []
    page = 1

    while True:
        response = requests.get(
            url,
            headers=headers,
            params={"per_page": 100, "page": page, "visibility": "all"},
        )
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return []

        data = response.json()
        if not data:
            break

        repos.extend(data)
        page += 1

    return repos


def get_languages(
    repos: list[str], token: str, filter_repos: Optional[list[str]] = None
) -> defaultdict[str, int]:
    """
    Retrieves the programming languages used in the user's GitHub repositories.

    Args:
        repos (list[str]): List of repository data from GitHub API.
        token (str): GitHub personal access token for authentication.
        filter_repos (Optional[list[str]]): List of repository names to exclude from analysis.

    Returns:
        defaultdict[str, int]: A dictionary mapping programming languages to their byte count.
    """
    language_stats = defaultdict(int)

    for repo in repos:
        repo_name: str = repo["name"]
        if filter_repos and repo_name in filter_repos:
            continue

        languages_url = repo["languages_url"]
        headers = {"Authorization": f"token {token}"}
        response = requests.get(languages_url, headers=headers)
        if response.status_code == 200:
            languages = response.json()
            for lang, bytes_count in languages.items():
                language_stats[lang] += bytes_count

    return language_stats


def generate_bar_chart(
    language_stats: tuple[str, int],
    output_file: str = "docs/language_chart.html",
):
    """
    Generates a horizontal bar chart displaying programming language usage.

    Args:
        language_stats (tuple[str, int]): A sorted list of (language, byte count) tuples.
        output_file (str): The filename to save the chart as an html. Defaults to "language_chart.html".
    """
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("chart.jinja")
    render_data = [(x, int(y), LANG_LOOKUP.get(x)) for x, y in language_stats]

    rendered_html = template.render(data=render_data)

    # Save to an HTML file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"HTML file generated: {output_file}")


def writeCSVData(data: dict[str, int]):
    """
    Writes CSV data to file.

    Args:
        data (dict[str, int]): A dict describing the language and associated bytes of code.
    """
    with open("language_data.csv", "w", newline="") as csvfile:
        csv_data = [{"Language": k, "Bytes": v} for k, v in data.items()]
        writer = csv.DictWriter(csvfile, fieldnames=["Language", "Bytes"])
        writer.writeheader()
        writer.writerows(csv_data)


def main():
    """
    Main function to retrieve GitHub repository data, analyze language usage,
    and generate a bar chart visualization.
    """
    token: str = os.getenv("GH_TOKEN")
    filter_repos: list[str] = os.getenv("REPO_FILTER").split(",")
    hide_languages: list[str] = os.getenv("LANG_FILTER").split(",")

    repos = get_github_repos(token)
    if not repos:
        print("No repositories found.")
        return

    language_stats = get_languages(repos, token, filter_repos)
    writeCSVData(language_stats)

    filtered_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    if hide_languages:
        filtered_langs = [x for x in filtered_langs if x[0] not in hide_languages]

    for lang, count in filtered_langs:
        print(f"{lang}: {count} bytes")

    generate_bar_chart(filtered_langs)


if __name__ == "__main__":
    main()
