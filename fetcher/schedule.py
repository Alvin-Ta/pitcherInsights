import requests

from config import BASE

async def fetch_todays_schedule():
    data = requests.get(f"{BASE}/schedule?sportId=1&date=2026-05-13").json()
    all_games = []

    for games in data["dates"][0]["games"]:
       all_games.append({
            "game_id": games["gamePk"],
            # "game_date": games["gameDate"],
            # "season": games["season"],
            "home_team": games["teams"]["home"]["team"]["name"],
            "away_team": games["teams"]["away"]["team"]["name"],
            # "home_team_id": games["teams"]["home"]["team"]["id"],
            # "away_team_id": games["teams"]["away"]["team"]["id"],
            # "game_status": games["status"]["detailedState"],
            # "venue": games["venue"]["name"]
        })


    return all_games
async def extract_probable_pitchers(date):
    data = requests.get(f"{BASE}/schedule?sportId=1&date={date}&hydrate=probablePitcher").json()
    probable_pitchers = []

    for games in data["dates"][0]["games"]:
        if "probablePitcher" in games["teams"]["home"] and "probablePitcher" in games["teams"]["away"]:
            probable_pitchers.append({
                "game_id": games["gamePk"],
                "home_team": games["teams"]["home"]["team"]["name"],
                "away_team": games["teams"]["away"]["team"]["name"],
                "home_probable_pitcher": games["teams"]["home"]["probablePitcher"]["fullName"] if "probablePitcher" in games["teams"]["home"] else None,
                "away_probable_pitcher": games["teams"]["away"]["probablePitcher"]["fullName"] if "probablePitcher" in games["teams"]["away"] else None
            })
    return probable_pitchers
