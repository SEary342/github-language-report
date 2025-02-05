from typing import Optional
import requests
import matplotlib.pyplot as plt
from collections import defaultdict
import os
from dotenv import load_dotenv

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
    output_file: str = "language_chart.png",
    transparent: bool = True,
):
    """
    Generates a horizontal bar chart displaying programming language usage.
    
    Args:
        language_stats (tuple[str, int]): A sorted list of (language, byte count) tuples.
        output_file (str): The filename to save the chart as an image. Defaults to "language_chart.png".
        transparent (bool): Whether the background of the chart should be transparent. Defaults to True.
    """
    languages = [x[0] for x in language_stats]
    usage = [x[1] for x in language_stats]

    plt.figure(figsize=(10, 5))
    plt.barh(languages, usage, color="skyblue")
    plt.xlabel("Bytes of Code", color="#aaaaaa")
    plt.ylabel("Programming Languages", color="#aaaaaa")
    plt.title("Language Usage in GitHub Repositories", color="#aaaaaa")
    plt.gca().invert_yaxis()
    plt.gca().set_facecolor("none")
    plt.gcf().set_facecolor("none")
    plt.xticks(color="#aaaaaa")
    plt.yticks(color="#aaaaaa")
    plt.savefig(output_file, bbox_inches="tight", transparent=transparent)
    print(f"Chart saved to {output_file}")

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
    filtered_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    if hide_languages:
        filtered_langs = [x for x in filtered_langs if x[0] not in hide_languages]

    for lang, count in filtered_langs:
        print(f"{lang}: {count} bytes")

    generate_bar_chart(filtered_langs)

if __name__ == "__main__":
    main()
