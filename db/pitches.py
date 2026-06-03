import psycopg2.extras

from db.connections import get_connection


def insert_pitches(pitches):
    if not pitches:
        return
    sql = """
        INSERT INTO pitches (
            game_id, game_date, season, inning, half_inning, at_bat_index,
            pitch_number, total_pitch_count,
            pitcher_id, pitcher_name, batter_id, batter_name,
            pitch_type_code, pitch_type_name,
            pitch_code, pitch_description,
            is_strike, is_ball, is_in_play,
            start_speed, end_speed, strike_zone_top, strike_zone_bottom, spin_rate, spin_direction,
            zone, px, pz, break_angle, break_vertical, break_length, break_horizontal,
            balls, strikes, outs, at_bat_result, at_bat_description, pitch_start_time, pitch_end_time
        ) VALUES (
            %(game_id)s, %(game_date)s, %(season)s, %(inning)s, %(half_inning)s, %(at_bat_index)s,
            %(pitch_number)s, %(total_pitch_count)s,
            %(pitcher_id)s, %(pitcher_name)s, %(batter_id)s, %(batter_name)s,
            %(pitch_type_code)s, %(pitch_type_name)s,
            %(pitch_code)s, %(pitch_description)s,
            %(is_strike)s, %(is_ball)s, %(is_in_play)s,
            %(start_speed)s, %(end_speed)s, %(strike_zone_top)s, %(strike_zone_bottom)s, %(spin_rate)s, %(spin_direction)s,
            %(zone)s, %(px)s, %(pz)s, %(break_angle)s, %(break_vertical)s, %(break_length)s, %(break_horizontal)s,
            %(balls)s, %(strikes)s, %(outs)s, %(at_bat_result)s, %(at_bat_description)s, %(pitch_start_time)s, %(pitch_end_time)s
        )
    """
    with get_connection() as conn:
        psycopg2.extras.execute_batch(conn.cursor(), sql, pitches, page_size=500)

def pitches_already_stored(game_id, pitcher_id):
    sql = """
        SELECT 1 FROM pitches
        WHERE game_id = %s AND pitcher_id = %s
        LIMIT 1
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (game_id, pitcher_id))
            return cur.fetchone() is not None

def save_pitcher(pitcher):
    sql = """
    INSERT INTO pitchers (
        pitcher_id,
        full_name,
        team,
        team_id,
        throws
    )
    VALUES (%s, %s, %s, %s, %s)

    ON CONFLICT (pitcher_id)
    DO UPDATE SET
        full_name = EXCLUDED.full_name,
        team = EXCLUDED.team,
        team_id = EXCLUDED.team_id,
        throws = EXCLUDED.throws,
        updated_at = NOW()
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                pitcher["pitcher_id"],
                pitcher["full_name"],
                pitcher["team"],
                pitcher["team_id"],
                pitcher["throws"]
            ))