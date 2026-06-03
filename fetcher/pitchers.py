import requests

from config import BASE

async def fetch_pitcher_game_log(pitcher_id, seasons):
    game_records = []
    
    for season in seasons:
        response = requests.get(f"{BASE}/people/{pitcher_id}/stats?stats=gameLog&group=pitching&season={season}")
        data = response.json()

        splits = data["stats"][0]["splits"]
        
        for split in splits:
            game_records.append({
                "game_id":   split["game"]["gamePk"],
                "game_date": split["date"],
                "season":    int(split["season"])
            })

    return game_records
