async def extract_batter_events(date, season, game_id, playbyplay):
    batter_pitches = []

    hit_events = {
        "single": 1,
        "double": 2,
        "triple": 3,
        "home_run": 4,
    }

    reach_base_events = {
        "walk": 1,
        "intent_walk": 1,
        "hit_by_pitch": 1,
        "field_error": 1,
        "force_out": 1,
        "fielders_choice": 1,
    }

    swing_codes = {
        "S",  # Swinging Strike
        "W",  # Swinging Strike (Blocked)
        "T",  # Foul Tip
        "F",  # Foul
        "L",  # Foul Bunt
        "X",  # In play, out(s)
        "D",  # In play, no out
        "E",  # In play, run(s)
    }

    whiff_codes = {
        "S",  # Swinging Strike
        "W",  # Swinging Strike (Blocked)
    }

    for play in playbyplay["allPlays"]:
        if play["result"]["type"] != "atBat":
            continue

        matchup = play["matchup"]
        result = play["result"]
        about = play["about"]

        at_bat_index = about.get("atBatIndex", play.get("atBatIndex"))
        at_bat_id = f"{game_id}_{at_bat_index}"

        result_event_type = result.get("eventType")
        is_hit = result_event_type in hit_events

        if result_event_type in hit_events:
            bases_earned = hit_events[result_event_type]
        else:
            bases_earned = reach_base_events.get(result_event_type, 0)

        pitch_events = [
            event for event in play["playEvents"]
            if event.get("isPitch")
        ]
        last_pitch_number = (
            pitch_events[-1]["pitchNumber"]
            if pitch_events
            else None
        )

        for pitch in pitch_events:
            details = pitch["details"]
            pitch_data = pitch.get("pitchData", {})
            breaks = pitch_data.get("breaks", {})
            hit_data = pitch.get("hitData", {})

            call_code = details.get("call", {}).get("code") or details.get("code")

            is_swing = call_code in swing_codes or details.get("isInPlay") is True
            is_whiff = call_code in whiff_codes

            batter_pitches.append({
                "game_id": game_id,
                "date": date,
                "season": season,

                "at_bat_id": at_bat_id,
                "at_bat_index": at_bat_index,
                "pitch_resulted_in_pa": pitch["pitchNumber"] == last_pitch_number,

                "batter_id": matchup["batter"]["id"],
                "batter_name": matchup["batter"]["fullName"],
                "bat_side": matchup["batSide"]["code"],

                "pitcher_id": matchup["pitcher"]["id"],
                "pitcher_name": matchup["pitcher"]["fullName"],

                "inning": about["inning"],
                "half_inning": about["halfInning"],

                "result_event": result["event"],
                "result_event_type": result_event_type,
                "is_out": result["isOut"],
                "rbi": result["rbi"],

                "is_swing": is_swing,
                "is_whiff": is_whiff,
                "is_hit": is_hit,
                "bases_earned": bases_earned,

                "pitch_number": pitch["pitchNumber"],

                "pitch_type_code": details.get("type", {}).get("code"),
                "pitch_type_name": details.get("type", {}).get("description"),

                "call_code": call_code,
                "call_description": details.get("call", {}).get("description"),

                "is_ball": details.get("isBall"),
                "is_strike": details.get("isStrike"),
                "is_in_play": details.get("isInPlay"),

                "start_speed": pitch_data.get("startSpeed"),
                "zone": pitch_data.get("zone"),

                "spin_rate": breaks.get("spinRate"),
                "break_vertical": breaks.get("breakVerticalInduced"),
                "break_horizontal": breaks.get("breakHorizontal"),

                "plate_x": pitch_data.get("coordinates", {}).get("pX"),
                "plate_z": pitch_data.get("coordinates", {}).get("pZ"),

                "launch_speed": hit_data.get("launchSpeed"),
                "launch_angle": hit_data.get("launchAngle"),
                "total_distance": hit_data.get("totalDistance"),
                "trajectory": hit_data.get("trajectory"),
                "hard_hit": hit_data.get("hardHit"),
            })

    return batter_pitches




if __name__ == "__main__":
    import asyncio
    from fetcher.playbyplay import fetch_game_playbyplay
    playbyplay = asyncio.run(fetch_game_playbyplay(822839))
    batter_events = asyncio.run(extract_batter_events("2026-03-27", "2026", 822839, playbyplay))
    print(batter_events)