# import requests
# import psycopg2
# import psycopg2.extras
# import os
# from psycopg2.extras import RealDictCursor

# from contextlib import contextmanager




# CORE FUNCTIONS TO IMPLEMENT:
    # game_records = asyncio.run(fetch_pitcher_game_log(656302, [2025, 2026]))
    # for game in game_records:
    #     if not pitches_already_stored(game["game_id"], 656302):
    #         playbyplay = asyncio.run(fetch_game_playbyplay(game["game_id"]))
    #         pitches = normalize_pitch_events([game], playbyplay, 656302)
    #         insert_pitches(pitches)


#psql mlb_pipeline -c "\x" -c "SELECT round(avg(start_speed), 2) as avg_velocity, round(avg(spin_rate), 2) as avg_spin_rate, round(avg(break_vertical), 2) as avg_break_vertical, round(avg(break_horizontal), 2) as avg_break_horizontal, (count(*)/total_pitch_count) as usg_pct FROM pitches WHERE game_id = 776959 AND inning = 1;"


# mlb_app psql mlb_pipeline -c "\x" -c "
# SELECT 
#     inning,
#     pitch_type_name,
#     round(avg(start_speed), 2) as avg_velocity,
#     round(avg(spin_rate), 2) as avg_spin_rate,
#     round(avg(break_vertical), 2) as avg_break_vertical,
#     round(avg(break_horizontal), 2) as avg_break_horizontal,
#     round(count(*) * 100.0 / sum(count(*)) OVER (PARTITION BY inning), 1) as usage_pct
# FROM pitches 
# WHERE game_id = 776959
# GROUP BY inning, pitch_type_name
# ORDER BY inning, usage_pct DESC;
# """


# pitcher_id = 656302
# averages = compute_averages(pitcher_id)
# save_pitcher_profile(pitcher_id, averages)