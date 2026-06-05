import asyncio
import psycopg2.extras

from constants.teams import MLB_TEAMS
from db.connections import get_connection
from fetcher.schedule import fetch_team_schedule
from fetcher.playbyplay import fetch_game_playbyplay
from fetcher.batters import extract_batter_events


SEASONS = [2025, 2026]


def insert_batter_pitches(batter_pitches):
    if not batter_pitches:
        return

    sql = """
        INSERT INTO batter_pitches (
            game_id, date, season,
            at_bat_id, at_bat_index, pitch_resulted_in_pa,
            batter_id, batter_name, bat_side,
            pitcher_id, pitcher_name,
            inning, half_inning,
            result_event, result_event_type, is_out, rbi,
            is_swing, is_whiff, is_hit, bases_earned,
            pitch_number,
            pitch_type_code, pitch_type_name,
            call_code, call_description,
            is_ball, is_strike, is_in_play,
            start_speed, zone,
            spin_rate, break_vertical, break_horizontal,
            plate_x, plate_z,
            launch_speed, launch_angle, total_distance, trajectory, hard_hit
        ) VALUES (
            %(game_id)s, %(date)s, %(season)s,
            %(at_bat_id)s, %(at_bat_index)s, %(pitch_resulted_in_pa)s,
            %(batter_id)s, %(batter_name)s, %(bat_side)s,
            %(pitcher_id)s, %(pitcher_name)s,
            %(inning)s, %(half_inning)s,
            %(result_event)s, %(result_event_type)s, %(is_out)s, %(rbi)s,
            %(is_swing)s, %(is_whiff)s, %(is_hit)s, %(bases_earned)s,
            %(pitch_number)s,
            %(pitch_type_code)s, %(pitch_type_name)s,
            %(call_code)s, %(call_description)s,
            %(is_ball)s, %(is_strike)s, %(is_in_play)s,
            %(start_speed)s, %(zone)s,
            %(spin_rate)s, %(break_vertical)s, %(break_horizontal)s,
            %(plate_x)s, %(plate_z)s,
            %(launch_speed)s, %(launch_angle)s, %(total_distance)s, %(trajectory)s, %(hard_hit)s
        )
        ON CONFLICT (game_id, at_bat_index, pitch_number) DO NOTHING;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, sql, batter_pitches, page_size=500)


async def ingest_batter_pitches_for_all_teams():
    seen_game_ids = set()

    for season in SEASONS:
        for team in MLB_TEAMS:
            team_id = team["id"]
            team_name = team["name"]

            print(f"Fetching {season} schedule for {team_name}...")

            schedule = await fetch_team_schedule(team_id, season)

            for game in schedule:
                game_id = game["game_id"]

                if game_id in seen_game_ids:
                    continue

                seen_game_ids.add(game_id)

                game_date = game["game_date"]
                game_season = game.get("season", season)

                print(f"Processing game {game_id} on {game_date}...")

                playbyplay = await fetch_game_playbyplay(game_id)

                batter_pitches = await extract_batter_events(
                    game_date,
                    game_season,
                    game_id,
                    playbyplay,
                )

                insert_batter_pitches(batter_pitches)

                print(f"Inserted {len(batter_pitches)} batter pitch rows")


if __name__ == "__main__":
    asyncio.run(ingest_batter_pitches_for_all_teams())
