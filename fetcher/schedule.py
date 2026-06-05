import requests

from config import BASE

async def fetch_todays_schedule():
    data = requests.get(f"{BASE}/schedule?sportId=1&date=2026-05-13").json() #UPDATE WHEN AVAILABLE
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

async def fetch_team_schedule(team_id, season):
    data = requests.get(f"{BASE}/schedule?sportId=1&season={season}&teamId={team_id}&gameType=R").json()
    team_schedule = []
    for date in data["dates"]:
        for game in date["games"]: 
            team_schedule.append({
                "game_id": game["gamePk"],
                "game_date": date["date"],
                "season": game["season"],
                # "home_team": game["teams"]["home"]["team"]["name"],
                # "away_team": game["teams"]["away"]["team"]["name"],
                # "home_team_id": game["teams"]["home"]["team"]["id"],
                # "away_team_id": game["teams"]["away"]["team"]["id"],
                # "game_status": game["status"]["detailedState"],
                # "venue": game["venue"]["name"]
            })
    return team_schedule

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

# if __name__ == "__main__":
#     import asyncio
#     print(asyncio.run(fetch_team_schedule(147, 2026)))
    # print(asyncio.run(fetch_todays_schedule()))