import json
import re
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
    rating_regex = re.compile('cs2rating.*')

    for rs in raw_stats.values():
        player_stats = {
            'Name': '',
            'Rank': 0,
            'Rating': 0,
            'KpD': 0,
            'ADR': 0,
            'Games': 0,
            'Win_Rate': 0,
            'Entry_Attempts': 0,
            'Worst_Match': 0.0,
            'Best_Match': 0.0,
            'Kills': 0,
            'Deaths': 0,
            'Assists': 0,
            'Kill_Shot_Ratio': 0.0,
            'Avatar': ''
        }

        soup = BeautifulSoup(rs, 'html.parser')

        player_stats['Name'] = soup.find('div', id='player-name').text.strip()
        ic(player_stats['Name'])

        avatar = soup.find('div', id='player-avatar').find_next('img')
        player_stats['Avatar'] = avatar['src']
        ic(player_stats['Avatar'])

        try:
            player_stats['Rank'] = int(soup.find('div', {'class': rating_regex}).find_next('span').text.strip().replace(',', ''))
        except (AttributeError, ValueError):
            pass
        ic(player_stats['Rank'])

        try:
            player_stats['Rating'] = float(soup.find('div', id='rating').text.strip())
        except AttributeError:
            pass
        ic(player_stats['Rating'])

        try:
            played = soup.find('img', src='https://static.csstats.gg/images/winrate-icon.png').find_next('span', class_='total-label')
            player_stats['Games'] = int(played.find_next('span', class_='total-value').text.strip()) if played.text.lower() == 'played' else 0
        except AttributeError:
            stats.append(player_stats)
            continue
        ic(player_stats['Games'])

        try:
            player_stats['KpD'] = float(soup.find('div', id='kpd').text.strip())
        except AttributeError:
            pass
        ic(player_stats['KpD'])

        try:
            player_stats['ADR'] = int(soup.find('img', src='https://static.csstats.gg/images/damage-icon.png').find_next().text.strip().split(' ')[0].strip())
        except AttributeError:
            pass
        ic(player_stats['ADR'])

        try:
            player_stats['Win_Rate'] = int(soup.find('img', src='https://static.csstats.gg/images/winrate-icon.png').find_next().text.split('%')[0])
        except AttributeError:
            pass
        ic(player_stats['Win_Rate'])

        try:
            player_stats['Entry_Attempts'] = int(soup.find('canvas', id='1-fk-both').find_previous('div').find_previous('div').text.split('%')[0].strip())
        except AttributeError:
            pass
        ic(player_stats['Entry_Attempts'])

        try:
            match_table = soup.find('div', id='match-list-outer').find_next('table')
        except AttributeError:
            match_table = None

        if match_table is not None:
            match_frame = pd.read_html(str(match_table))[0]
            player_stats['Worst_Match'] = float(match_frame.nsmallest(1, 'Rating')['Rating'].to_string(index=False))
            player_stats['Best_Match'] = float(match_frame.nlargest(1, 'Rating')['Rating'].to_string(index=False))
            player_stats['Kills'] = int(match_frame['K'].sum())
            player_stats['Deaths'] = int(match_frame['D'].sum())
            player_stats['Assists'] = int(match_frame['A'].sum())
            ic(player_stats['Worst_Match'])
            ic(player_stats['Best_Match'])
            ic(player_stats['Kills'])
            ic(player_stats['Deaths'])
            ic(player_stats['Assists'])

        try:
            weapon_table = soup.find('div', id='player-weapons').find_next('table')
        except AttributeError:
            weapon_table = None

        if weapon_table is not None:
            weapon_frame = pd.read_html(str(weapon_table))[0]
            total_shots = int(weapon_frame['Shots'].sum())
            total_kills = int(weapon_frame['Kills'].sum())
            ksr = (total_kills / total_shots) * 100
            player_stats['Kill_Shot_Ratio'] = round(ksr, 2)

        stats.append(player_stats)

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
