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


def search_imdb(title: str, start_year=0, end_year=0):
    """
    get soup from imdb search page
    """
    title = title.replace(" ", "%20")
    url = f"https://www.imdb.com/search/title/?title={title}&title_type=tv_series,tv_miniseries"
    if start_year:
        url += f"&release_date={start_year}-01-01,"
    if not start_year and end_year:
        url += "&release_date=,"
    if end_year:
        url += f"{end_year}-12-31"
    response = requests.get(
        url=url,
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


def get_episode_ratings(title: str, start_year=0, end_year=0):
    '''
    pull per-episode IMDB ratings
    '''
    imdb_id = search_imdb(title, start_year, end_year)
    response = requests.get(
        url=f"https://www.imdb.com/title/{imdb_id}/episodes/",
        headers=header,
        timeout=20,
    )

    soup = BeautifulSoup(response.content, features="html.parser")
    imdb_title = soup.find_all("h2", {"data-testid": "subtitle"})[0].text
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
    return imdb_title, episode_ratings


def gen_heatmap(title: str, start_year=0, end_year=0):
    """
    Generate heatmap for imdb show episode ratings
    """
    imdb_title, episode_dict = get_episode_ratings(title, start_year, end_year)
    episode_df = pd.DataFrame(data=episode_dict, dtype=np.float32).replace(
        to_replace=pd.NA, value=np.nan
    )
    episode_df.loc['AVG'] = episode_df.mean(axis=0)
    cmap = LinearSegmentedColormap.from_list(
        "RedOrangeYellowGreen", ["#d62727", "#f5b402", "#f5e505", "#15f505"]
    )
    num_seasons = len(episode_df.columns)
    multiplier = 1
    if num_seasons > 16:
        multiplier = 2
    fig, ax = plt.subplots(figsize=(8*multiplier, 8))
    ax.xaxis.tick_top()
    ax.set_title(imdb_title, fontsize=20)
    average_rating = str(round(np.mean(episode_df), 1))
    sns.heatmap(
        episode_df,
        cmap=cmap,
        vmin=7.0,
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
    fig.savefig(f"{imdb_title.replace(' ', '_')}_Heatmap.png", dpi=200)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--title',
                        type=str,
                        dest='title',
                        help="Provide the title of the IMDB TV show to retreive episode ratings.")
    parser.add_argument('-s', '--start_year',
                        type=int,
                        dest='start_year',
                        help="Provide the start year of the IMDB TV show to retreive episode ratings.")
    parser.add_argument('-e', '--end_year',
                        type=int,
                        dest='end_year',
                        help="Provide the end year of the IMDB TV show to retreive episode ratings.")
    args = parser.parse_args()
    gen_heatmap(args.title, args.start_year, args.end_year)
