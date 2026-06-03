# # models/pitcher_profile.py

# import psycopg2
# from psycopg2.extras import RealDictCursor
# from database import get_connection   # the helper we wrote in Step 1
# import sys
# print(sys.path)

# def get_pitch_mix(pitcher_id: int, seasons: tuple[int, ...]) -> list[dict]:
#     """
#     Returns per-pitch-type averages for a pitcher across the given seasons.
#     Each row: pitch_type_name, total, avg_velocity, avg_spin, usage_pct
#     """
#     seasons = tuple(seasons)
#     sql = """
#         SELECT
#             pitch_type_name,
#             COUNT(*) AS total,
#             ROUND(AVG(start_speed), 1)                                  AS avg_velocity,
#             ROUND(AVG(spin_rate), 0)                                     AS avg_spin,
#             ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)          AS usage_pct
#         FROM pitches
#         WHERE pitcher_id = %s
#           AND season IN %s
#         GROUP BY pitch_type_name
#         ORDER BY total DESC
#     """
#     with get_connection() as conn:
#         with conn.cursor(cursor_factory=RealDictCursor) as cur:
#             cur.execute(sql, (pitcher_id, seasons))
#             return cur.fetchall()

# if __name__ == "__main__":
#     import json
#     from pprint import pprint

#     CEASE_ID = 656302

#     print(f"Fetching pitch mix for pitcher_id={CEASE_ID}, season=2025...\n")
#     results = get_pitch_mix(CEASE_ID, (2025,))
#     pprint(results)