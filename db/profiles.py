from psycopg2.extras import RealDictCursor

from db.connections import get_connection


def compute_averages(pitcher_id, seasons):
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
    AND season = ANY(%s)
    AND start_speed IS NOT NULL
    AND spin_rate IS NOT NULL

    GROUP BY pitch_type_name
    ORDER BY usage_pct DESC;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (pitcher_id, seasons))
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
            cur.execute(sql, (pitcher_id, pitcher_id))
            return cur.fetchall()

def compute_baseline_stats(pitcher_id):
    sql = """
        SELECT pitcher_id, pitcher_name, COUNT(*) FILTER 
        (WHERE is_strike = true OR is_in_play = true)::float / COUNT(*) AS strike_pct, 
        COUNT(*) FILTER (WHERE pitch_code IN ('S','W','T'))::float / COUNT(*) AS swstr_pct, 
        COUNT(*) FILTER (WHERE pitch_code IN ('S','W','T'))::float / NULLIF(COUNT(*) 
        FILTER (WHERE pitch_code IN ('S','W','T','F','D','E','X')), 0) AS whiff_pct, 
        AVG(start_speed) FILTER (WHERE pitch_type_code = 'FF') AS avg_ff_velocity, 
        AVG(pitch_totals.total) AS avg_pitch_count_per_game 
        FROM pitches CROSS JOIN ( SELECT MAX(total_pitch_count) 
        AS total FROM pitches WHERE pitcher_id = %s GROUP BY game_id ) 
        pitch_totals WHERE pitcher_id = %s GROUP BY pitcher_id, pitcher_name;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (pitcher_id, pitcher_id))
            return cur.fetchone()

def compute_fatigue_profile(pitcher_id):
    sql = """
        WITH bucketed_pitches AS (
            SELECT
                *,
                CASE
                    WHEN total_pitch_count BETWEEN 1 AND 25 THEN '1-25'
                    WHEN total_pitch_count BETWEEN 26 AND 50 THEN '26-50'
                    WHEN total_pitch_count BETWEEN 51 AND 75 THEN '51-75'
                    WHEN total_pitch_count BETWEEN 76 AND 100 THEN '76-100'
                    ELSE '100+'
                END AS pitch_count_bucket,
                CASE
                    WHEN total_pitch_count BETWEEN 1 AND 25 THEN 1
                    WHEN total_pitch_count BETWEEN 26 AND 50 THEN 2
                    WHEN total_pitch_count BETWEEN 51 AND 75 THEN 3
                    WHEN total_pitch_count BETWEEN 76 AND 100 THEN 4
                    ELSE 5
                END AS bucket_order
            FROM pitches
            WHERE pitcher_id = %s
              AND total_pitch_count IS NOT NULL
        ),
        pitch_stats AS (
            SELECT
                pitch_count_bucket,
                bucket_order,
                ROUND(AVG(start_speed), 2) AS avg_velocity,
                ROUND(
                    COUNT(*) FILTER (
                        WHERE is_strike = true OR is_in_play = true
                    ) * 1.0 / NULLIF(COUNT(*), 0),
                    3
                ) AS strike_pct,
                ROUND(
                    COUNT(*) FILTER (
                        WHERE pitch_code IN ('S', 'W')
                    ) * 1.0 / NULLIF(
                        COUNT(*) FILTER (
                            WHERE pitch_code IN ('S', 'W', 'T', 'F', 'L', 'X', 'D', 'E')
                        ),
                        0
                    ),
                    3
                ) AS whiff_pct
            FROM bucketed_pitches
            GROUP BY pitch_count_bucket, bucket_order
        ),
        final_pa_pitches AS (
            SELECT DISTINCT ON (game_id, at_bat_index)
                game_id,
                at_bat_index,
                pitch_count_bucket,
                bucket_order,
                at_bat_result
            FROM bucketed_pitches
            ORDER BY game_id, at_bat_index, pitch_number DESC
        ),
        walk_stats AS (
            SELECT
                pitch_count_bucket,
                bucket_order,
                ROUND(
                    COUNT(*) FILTER (
                        WHERE LOWER(at_bat_result) IN ('walk', 'intent walk', 'intent_walk')
                    ) * 1.0 / NULLIF(COUNT(*), 0),
                    3
                ) AS walk_pct
            FROM final_pa_pitches
            GROUP BY pitch_count_bucket, bucket_order
        )
        SELECT
            ps.pitch_count_bucket,
            ps.avg_velocity,
            ps.strike_pct,
            ps.whiff_pct,
            ws.walk_pct
        FROM pitch_stats ps
        LEFT JOIN walk_stats ws
            ON ps.pitch_count_bucket = ws.pitch_count_bucket
           AND ps.bucket_order = ws.bucket_order
        ORDER BY ps.bucket_order;
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (pitcher_id,))
            return cur.fetchall()

if __name__ == "__main__":
    # print(compute_baseline_stats(656302))
    # print(compute_last_5_pitches(656302))
    print(compute_fatigue_profile(656302))
