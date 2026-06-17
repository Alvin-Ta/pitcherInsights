from db.pregame import build_pregame_expectations
from fetcher.playbyplay import fetch_game_playbyplay


SWING_CODES = {"S", "W", "T", "F", "L", "X", "D", "E"}
WHIFF_CODES = {"S", "W"}


def _round(value, digits):
    if value is None:
        return None
    return round(value, digits)


def _diff(current_value, expected_value, digits=2):
    if current_value is None or expected_value is None:
        return None
    return round(current_value - expected_value, digits)


def _weighted_expected_velocity(expectations):
    season_velocity = expectations.get("season_avg_velocity")
    last_5_velocity = expectations.get("last_5_avg_velocity")

    if season_velocity is None:
        return last_5_velocity
    if last_5_velocity is None:
        return season_velocity

    return (season_velocity * 0.7) + (last_5_velocity * 0.3)


def _empty_pitcher_state(pitcher_id, pitcher_name):
    return {
        "pitcher_id": pitcher_id,
        "pitcher_name": pitcher_name,
        "pitch_count": 0,
        "speeds": [],
        "strikes": 0,
        "swings": 0,
        "whiffs": 0,
        "last_pitch": None,
    }


def compute_live_pitcher_stats(playbyplay):
    pitchers = {}

    for play in playbyplay.get("allPlays", []):
        matchup = play.get("matchup", {})
        pitcher = matchup.get("pitcher", {})
        pitcher_id = pitcher.get("id")

        if pitcher_id is None:
            continue

        pitcher_name = pitcher.get("fullName")
        pitcher_state = pitchers.setdefault(
            pitcher_id,
            _empty_pitcher_state(pitcher_id, pitcher_name),
        )

        for event in play.get("playEvents", []):
            if not event.get("isPitch"):
                continue

            details = event.get("details", {})
            pitch_data = event.get("pitchData", {})
            call_code = details.get("call", {}).get("code") or details.get("code")
            start_speed = pitch_data.get("startSpeed")

            pitcher_state["pitch_count"] += 1

            if start_speed is not None:
                pitcher_state["speeds"].append(start_speed)

            if details.get("isStrike") is True or details.get("isInPlay") is True:
                pitcher_state["strikes"] += 1

            if call_code in SWING_CODES or details.get("isInPlay") is True:
                pitcher_state["swings"] += 1

            if call_code in WHIFF_CODES:
                pitcher_state["whiffs"] += 1

            pitcher_state["last_pitch"] = {
                "inning": play.get("about", {}).get("inning"),
                "half_inning": play.get("about", {}).get("halfInning"),
                "at_bat_index": play.get("about", {}).get("atBatIndex", play.get("atBatIndex")),
                "pitch_number": event.get("pitchNumber"),
                "pitch_type_code": details.get("type", {}).get("code"),
                "pitch_type_name": details.get("type", {}).get("description"),
                "call_code": call_code,
                "call_description": details.get("call", {}).get("description"),
                "start_speed": start_speed,
            }

    live_stats = []

    for pitcher_state in pitchers.values():
        pitch_count = pitcher_state["pitch_count"]
        speeds = pitcher_state["speeds"]
        swings = pitcher_state["swings"]

        current_velocity = sum(speeds) / len(speeds) if speeds else None
        current_strike_pct = pitcher_state["strikes"] / pitch_count if pitch_count else None
        current_whiff_pct = pitcher_state["whiffs"] / swings if swings else None

        live_stats.append({
            "pitcher_id": pitcher_state["pitcher_id"],
            "pitcher_name": pitcher_state["pitcher_name"],
            "pitch_count": pitch_count,
            "current_velocity": _round(current_velocity, 1),
            "current_strike_pct": _round(current_strike_pct, 2),
            "current_whiff_pct": _round(current_whiff_pct, 2),
            "last_pitch": pitcher_state["last_pitch"],
        })

    return live_stats


def build_live_pitcher_expectation_view(playbyplay, season, pitcher_id=None):
    live_pitchers = compute_live_pitcher_stats(playbyplay)

    if pitcher_id is not None:
        live_pitchers = [
            pitcher for pitcher in live_pitchers
            if pitcher["pitcher_id"] == pitcher_id
        ]

    pitcher_views = []

    for live_pitcher in live_pitchers:
        expectations = build_pregame_expectations(live_pitcher["pitcher_id"], season)
        expected_velocity = _weighted_expected_velocity(expectations)
        expected_strike_pct = expectations.get("expected_strike_pct")
        expected_whiff_pct = expectations.get("expected_whiff_pct")

        pitcher_views.append({
            "pitcher_id": live_pitcher["pitcher_id"],
            "pitcher_name": live_pitcher["pitcher_name"] or expectations.get("pitcher_name"),
            "pitch_count": live_pitcher["pitch_count"],
            "current_velocity": live_pitcher["current_velocity"],
            "expected_velocity": _round(expected_velocity, 1),
            "velocity_diff": _diff(live_pitcher["current_velocity"], expected_velocity, 1),
            "current_strike_pct": live_pitcher["current_strike_pct"],
            "expected_strike_pct": expected_strike_pct,
            "strike_pct_diff": _diff(live_pitcher["current_strike_pct"], expected_strike_pct, 2),
            "current_whiff_pct": live_pitcher["current_whiff_pct"],
            "expected_whiff_pct": expected_whiff_pct,
            "whiff_pct_diff": _diff(live_pitcher["current_whiff_pct"], expected_whiff_pct, 2),
            "last_pitch": live_pitcher["last_pitch"],
            "pregame_expectations": expectations,
        })

    return pitcher_views


async def ingest_live_game_for_frontend(game_id, season, pitcher_id=None):
    playbyplay = await fetch_game_playbyplay(game_id)
    pitcher_views = build_live_pitcher_expectation_view(
        playbyplay,
        season,
        pitcher_id=pitcher_id,
    )

    return {
        "game_id": game_id,
        "season": season,
        "pitchers": pitcher_views,
    }
