'''
Python module to generate a heatmap of episode ratings for a TV Show
based on IMDB ratings.
'''
import requests
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from matplotlib.colors import LinearSegmentedColormap


header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "\
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
    }


def search_imdb(title: str):
    """
    get soup from imdb search page
    """
    title = title.replace(" ", "%20")
    response = requests.get(
        url=f"https://www.imdb.com/search/title/?title={title}&title_type=tv_series",
        headers=header,
        timeout=20,
    )
    soup = BeautifulSoup(response.content, features="html.parser")
    search_results = soup.find_all("a", attrs={"class": "ipc-title-link-wrapper"})
    first_result = search_results[0]
    start = first_result["href"].find("tt")
    end = first_result["href"].find("/?ref")
    imdb_id = first_result["href"][start:end]
    return imdb_id


def get_episode_ratings(title: str):
    '''
    pull per-episode IMDB ratings
    '''
    imdb_id = search_imdb(title)
    response = requests.get(
        url=f"https://www.imdb.com/title/{imdb_id}/episodes/",
        headers=header,
        timeout=20,
    )

    soup = BeautifulSoup(response.content, features="html.parser")
    seasons = soup.find_all("a", attrs={"data-testid": "tab-season-entry"})
    season_numbers = [season.text for season in seasons]

    episode_ratings = {k: {} for k in season_numbers}
    for season_number in season_numbers:
        response = requests.get(
            url=f"https://www.imdb.com/title/{imdb_id}/episodes/?season={season_number}",
            headers=header,
            timeout=20,
        )

        soup = BeautifulSoup(response.content, features="html.parser")
        ratings = soup.find_all(
            "span",
            attrs={
                "class": "ipc-rating-star ipc-rating-star--base "\
                    "ipc-rating-star--imdb ratingGroup--imdb-rating"
            },
        )
        episode_count = 1
        for rating in ratings:
            end = rating.text.find("/")
            episode_ratings[season_number][episode_count] = rating.text[:end]
            episode_count += 1
    return episode_ratings


def gen_heatmap(title: str):
    """
    Generate heatmap for imdb show episode ratings
    """
    episode_dict = get_episode_ratings(title)
    episode_df = pd.DataFrame(data=episode_dict, dtype=np.float32).replace(
        to_replace=pd.NA, value=np.nan
    )
    cmap = LinearSegmentedColormap.from_list(
        "RedYellowGreen", ["#d62727", "#f5e505", "#15f505"]
    )
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.xaxis.tick_top()
    ax.set_title(title, fontsize=20)
    average_rating = str(round(np.mean(episode_df), 1))
    sns.heatmap(
        episode_df,
        cmap=cmap,
        vmin=episode_df.min().min(),
        vmax=10.0,
        linewidths=1,
        annot=True,
        mask=episode_df.isna(),
    )
    ax.set_xlabel("Season")
    ax.set_ylabel("Episode")
    ax.tick_params(axis="y", labelrotation=-0.1)
    ax.xaxis.set_label_position("top")
    ax.yaxis.set_ticks_position("none")
    ax.xaxis.set_ticks_position("none")
    fig.text(0.50, 0.02, f'Average Rating: {average_rating}',
             horizontalalignment='center',
             wrap=True) 
    fig.savefig(f"{title.replace(' ', '_')}_Heatmap.png", dpi=200)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title',
                        type=str,
                        dest='title',
                        help="Provide the title of the IMDB TV show to retreive episode ratings.")
    args = parser.parse_args()
    gen_heatmap(args.title)
