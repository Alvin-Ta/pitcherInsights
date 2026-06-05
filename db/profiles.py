from psycopg2.extras import RealDictCursor

from db.connections import get_connection


def compute_averages(pitcher_id):
    sql = """
    SELECT
        pitch_type_name,

        ROUND(AVG(start_speed), 2) AS avg_velocity,
        ROUND(AVG(spin_rate), 2) AS avg_spin_rate,
        ROUND(AVG(break_vertical), 2) AS avg_break_vertical,
        ROUND(AVG(break_horizontal), 2) AS avg_break_horizontal,

        ROUND(
            COUNT(*) * 100.0 /
            SUM(COUNT(*)) OVER (),
            1
        ) AS usage_pct

    FROM pitches
    WHERE pitcher_id = %s
    AND start_speed IS NOT NULL
    AND spin_rate IS NOT NULL

    GROUP BY pitch_type_name
    ORDER BY usage_pct DESC;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (pitcher_id,))
            return cur.fetchall()

def save_pitcher_profile(pitcher_id, averages):
    sql = """
    INSERT INTO pitcher_profiles (
        pitcher_id, pitch_type_name, avg_velocity, avg_spin_rate, avg_break_vertical, avg_break_horizontal, usage_pct
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (pitcher_id, pitch_type_name) DO UPDATE SET
        avg_velocity = EXCLUDED.avg_velocity,
        avg_spin_rate = EXCLUDED.avg_spin_rate,
        avg_break_vertical = EXCLUDED.avg_break_vertical,
        avg_break_horizontal = EXCLUDED.avg_break_horizontal,
        usage_pct = EXCLUDED.usage_pct,
        updated_at = NOW();
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            for row in averages:
                cur.execute(sql, (
                    pitcher_id,
                    row["pitch_type_name"],
                    row["avg_velocity"],
                    row["avg_spin_rate"],
                    row["avg_break_vertical"],
                    row["avg_break_horizontal"],
                    row["usage_pct"]
                ))
                
def compute_last_5_pitches(pitcher_id):
    sql = """
        WITH last_5_games AS (
            SELECT DISTINCT game_id, game_date
            FROM pitches
            WHERE pitcher_id = %s
            ORDER BY game_date DESC
            LIMIT 5
        )
        SELECT
            p.pitch_type_name,

            ROUND(AVG(p.start_speed), 2) AS avg_velocity,
            ROUND(AVG(p.spin_rate), 2) AS avg_spin_rate,
            ROUND(AVG(p.break_vertical), 2) AS avg_break_vertical,
            ROUND(AVG(p.break_horizontal), 2) AS avg_break_horizontal,

            ROUND(
                COUNT(*) * 100.0 /
                SUM(COUNT(*)) OVER (),
                1
            ) AS usage_pct

        FROM pitches p
        JOIN last_5_games g
            ON p.game_id = g.game_id

        WHERE p.pitcher_id = %s
          AND p.start_speed IS NOT NULL
          AND p.spin_rate IS NOT NULL

        GROUP BY p.pitch_type_name
        ORDER BY usage_pct DESC;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (pitcher_id,))
            return cur.fetchall()
