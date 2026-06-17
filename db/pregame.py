from decimal import Decimal

from psycopg2.extras import RealDictCursor

from db.connections import get_connection


SEASON_WEIGHT = 0.7
RECENT_WEIGHT = 0.3


def _to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _round(value, digits):
    if value is None:
        return None
    return round(_to_float(value), digits)


def _weighted(season_value, recent_value):
    if season_value is None:
        return _to_float(recent_value)
    if recent_value is None:
        return _to_float(season_value)
    return (_to_float(season_value) * SEASON_WEIGHT) + (_to_float(recent_value) * RECENT_WEIGHT)


def build_pregame_expectations(pitcher_id, season):
    sql = """
        WITH pitch_window AS (
            SELECT *
            FROM pitches
            WHERE pitcher_id = %s
              AND season = %s
        ),
        last_5_games AS (
            SELECT game_id
            FROM pitch_window
            GROUP BY game_id
            ORDER BY MAX(game_date) DESC
            LIMIT 5
        ),
        scoped_pitches AS (
            SELECT 'season'::text AS scope, *
            FROM pitch_window

            UNION ALL

            SELECT 'last_5'::text AS scope, pw.*
            FROM pitch_window pw
            JOIN last_5_games l5
                ON pw.game_id = l5.game_id
        ),
        pitch_stats AS (
            SELECT
                scope,
                MAX(pitcher_name) AS pitcher_name,
                COUNT(*) FILTER (
                    WHERE is_strike = true OR is_in_play = true
                )::float / NULLIF(COUNT(*), 0) AS strike_pct,
                COUNT(*) FILTER (
                    WHERE pitch_code IN ('S', 'W')
                )::float / NULLIF(
                    COUNT(*) FILTER (
                        WHERE pitch_code IN ('S', 'W', 'T', 'F', 'L', 'X', 'D', 'E')
                    ),
                    0
                ) AS whiff_pct,
                AVG(start_speed) AS avg_velocity
            FROM scoped_pitches
            GROUP BY scope
        ),
        game_pitch_counts AS (
            SELECT
                scope,
                game_id,
                COUNT(*) AS pitch_count
            FROM scoped_pitches
            GROUP BY scope, game_id
        ),
        plate_appearances AS (
            SELECT
                scope,
                game_id,
                at_bat_index,
                MAX(at_bat_result) AS at_bat_result
            FROM scoped_pitches
            GROUP BY scope, game_id, at_bat_index
        ),
        game_pa_counts AS (
            SELECT
                scope,
                game_id,
                COUNT(*) FILTER (
                    WHERE LOWER(at_bat_result) = 'strikeout'
                ) AS strikeouts,
                COUNT(*) FILTER (
                    WHERE LOWER(at_bat_result) IN ('walk', 'intent walk', 'intent_walk')
                ) AS walks
            FROM plate_appearances
            GROUP BY scope, game_id
        ),
        game_stats AS (
            SELECT
                gpc.scope,
                AVG(gpc.pitch_count) AS avg_pitch_count,
                AVG(COALESCE(gpac.strikeouts, 0)) AS avg_strikeouts,
                AVG(COALESCE(gpac.walks, 0)) AS avg_walks
            FROM game_pitch_counts gpc
            LEFT JOIN game_pa_counts gpac
                ON gpc.scope = gpac.scope
               AND gpc.game_id = gpac.game_id
            GROUP BY gpc.scope
        )
        SELECT
            ps.scope,
            ps.pitcher_name,
            ps.strike_pct,
            ps.whiff_pct,
            ps.avg_velocity,
            gs.avg_pitch_count,
            gs.avg_strikeouts,
            gs.avg_walks
        FROM pitch_stats ps
        JOIN game_stats gs
            ON ps.scope = gs.scope;
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (pitcher_id, season))
            rows = {row["scope"]: row for row in cur.fetchall()}

    season_stats = rows.get("season", {})
    last_5_stats = rows.get("last_5", {})

    expected_strike_pct = _weighted(
        season_stats.get("strike_pct"),
        last_5_stats.get("strike_pct"),
    )
    expected_whiff_pct = _weighted(
        season_stats.get("whiff_pct"),
        last_5_stats.get("whiff_pct"),
    )
    expected_velocity = _weighted(
        season_stats.get("avg_velocity"),
        last_5_stats.get("avg_velocity"),
    )
    expected_pitch_count = _weighted(
        season_stats.get("avg_pitch_count"),
        last_5_stats.get("avg_pitch_count"),
    )
    expected_strikeouts = _weighted(
        season_stats.get("avg_strikeouts"),
        last_5_stats.get("avg_strikeouts"),
    )
    expected_walks = _weighted(
        season_stats.get("avg_walks"),
        last_5_stats.get("avg_walks"),
    )

    return {
        "pitcher_id": pitcher_id,
        "pitcher_name": season_stats.get("pitcher_name") or last_5_stats.get("pitcher_name"),
        "season_strike_pct": _round(season_stats.get("strike_pct"), 2),
        "season_whiff_pct": _round(season_stats.get("whiff_pct"), 2),
        "season_avg_velocity": _round(season_stats.get("avg_velocity"), 1),
        "last_5_strike_pct": _round(last_5_stats.get("strike_pct"), 2),
        "last_5_whiff_pct": _round(last_5_stats.get("whiff_pct"), 2),
        "last_5_avg_velocity": _round(last_5_stats.get("avg_velocity"), 1),
        "expected_velocity": _round(expected_velocity, 1),
        "expected_strike_pct": _round(expected_strike_pct, 2),
        "expected_whiff_pct": _round(expected_whiff_pct, 2),
        "expected_pitch_count": round(expected_pitch_count) if expected_pitch_count is not None else None,
        "expected_strikeouts": _round(expected_strikeouts, 1),
        "expected_walks": _round(expected_walks, 1),
    }


if __name__ == "__main__":
    print(build_pregame_expectations(656302, 2026))
