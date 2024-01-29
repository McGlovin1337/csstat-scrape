import json
import time
import pandas as pd
from selenium.webdriver import Firefox
from bs4 import BeautifulSoup
from icecream import ic


def get_page_source(driver: Firefox, player_ids: list[int]) -> dict:
    stats = {}

    for player_id in player_ids:
        ic(player_id)
        driver.get(f'https://csstats.gg/player/{player_id}?date=7d#/')
        time.sleep(10)
        stats.update({player_id: driver.page_source})

    return stats


def parse_html(raw_stats: dict) -> list[dict]:
    stats = []

    for rs in raw_stats.values():
        soup = BeautifulSoup(rs, 'html.parser')

        name = soup.find('div', id='player-name').text.strip()
        ic(name)

        try:
            rank = int(soup.find('div', class_='rank').find_next('span').text.strip().replace(',', ''))
        except (AttributeError, ValueError):
            rank = 0
        ic(rank)

        try:
            rating = float(soup.find('div', id='rating').text.strip())
        except AttributeError:
            rating = 0
        ic(rating)

        try:
            kpd = float(soup.find('div', id='kpd').text.strip())
        except AttributeError:
            kpd = 0
        ic(kpd)

        try:
            adr = int(soup.find('img', src='https://static.csstats.gg/images/damage-icon.png').find_next().text.strip().split(' ')[0].strip())
        except AttributeError:
            adr = 0
        ic(adr)

        try:
            win_rate = int(soup.find('img', src='https://static.csstats.gg/images/winrate-icon.png').find_next().text.split('%')[0])
        except AttributeError:
            win_rate = 0
        ic(win_rate)

        try:
            played = soup.find('img', src='https://static.csstats.gg/images/winrate-icon.png').find_next('span', class_='total-label')
            games = int(played.find_next('span', class_='total-value').text.strip()) if played.text.lower() == 'played' else 0
        except AttributeError:
            games = 0
        ic(games)

        try:
            entry_attempts = int(soup.find('canvas', id='1-fk-both').find_previous('div').find_previous('div').text.split('%')[0].strip())
        except AttributeError:
            entry_attempts = 0
        ic(entry_attempts)

        try:
            match_table = soup.find('div', id='match-list-outer').find_next('table')
        except AttributeError:
            match_table = None
            worst_match = 0.0
            best_match = 0.0

        if match_table is not None:
            match_frame = pd.read_html(str(match_table))[0]
            worst_match = float(match_frame.nsmallest(1, 'Rating')['Rating'].to_string(index=False))
            best_match = float(match_frame.nlargest(1, 'Rating')['Rating'].to_string(index=False))
            ic(worst_match)
            ic(best_match)

        try:
            weapon_table = soup.find('div', id='player-weapons').find_next('table')
        except AttributeError:
            weapon_table = None
            total_shots = 0
            total_kills = 0
            kill_shot_ratio = 0

        if weapon_table is not None:
            weapon_frame = pd.read_html(str(weapon_table))[0]
            total_shots = int(weapon_frame['Shots'].sum())
            total_kills = int(weapon_frame['Kills'].sum())
            kill_shot_ratio = (total_kills / total_shots) * 100

        avatar = soup.find('div', id='player-avatar').find_next('img')
        avatar_src = avatar['src']
        ic(avatar_src)

        stats.append({
            'Name': name,
            'Rank': rank,
            'Rating': rating,
            'KpD': kpd,
            'ADR': adr,
            'Games': games,
            'Win_Rate': win_rate,
            'Entry_Attempts': entry_attempts,
            'Worst_Match': worst_match,
            'Best_Match': best_match,
            'Kill_Shot_Ratio': round(kill_shot_ratio, 2),
            'Avatar': avatar_src
        })

    return stats


def main():
    with open('player_list.json', 'r', encoding='utf-8') as pl:
        players = json.load(pl)

    driver = Firefox()

    player_ids = list(players.values())
    player_raw_stats = get_page_source(driver, player_ids)

    ic(player_raw_stats.keys())

    driver.quit()

    stats = parse_html(player_raw_stats)
    ic(stats)

    json_stats = json.dumps(stats)

    with open('player_stats.json', 'w', encoding='utf-8') as ps:
        ps.write(json_stats)


if __name__ == '__main__':
    main()
