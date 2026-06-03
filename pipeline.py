import asyncio

from fetcher import fetch_pitcher_game_log, fetch_game_playbyplay
from normalizers.pitches import normalize_pitch_events
from db.pitches import insert_pitches, pitches_already_stored, save_pitcher
from db.profiles import compute_averages, save_pitcher_profile


async def run_pipeline(pitcher_id, seasons):
    game_records = await fetch_pitcher_game_log(pitcher_id, seasons)
    print(game_records)

    for game in game_records:
        if not pitches_already_stored(game["game_id"], pitcher_id):
            playbyplay = await fetch_game_playbyplay(game["game_id"])
            pitches = normalize_pitch_events([game], playbyplay, pitcher_id)
            insert_pitches(pitches)

    averages = compute_averages(pitcher_id)
    save_pitcher_profile(pitcher_id, averages)


if __name__ == "__main__":
    asyncio.run(run_pipeline(592332, [2025, 2026]))
