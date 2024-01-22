import json
import time
from selenium.webdriver import Firefox
from bs4 import BeautifulSoup
from icecream import ic


def get_page_source(driver: Firefox, player_ids: list[int]) -> dict:
    stats = {}

    for player_id in player_ids:
        driver.get(f'https://csstats.gg/player/{player_id}?date=7d#/')
        time.sleep(3)
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
