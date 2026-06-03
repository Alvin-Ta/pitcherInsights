import requests

from config import BASE


async def fetch_game_playbyplay(game_id):
    response = requests.get(f"{BASE}/game/{game_id}/playByPlay")
    data = response.json()
    return data
