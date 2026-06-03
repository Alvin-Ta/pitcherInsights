def determine_missing_games(api_games, stored_games):
    api_game_ids = {game["game_id"] for game in api_games}
    stored_game_ids = {game["game_id"] for game in stored_games}

    missing_game_ids = api_game_ids - stored_game_ids
    return [game for game in api_games if game["game_id"] in missing_game_ids]

def normalize_pitch_events(game_records, playbyplay_data, pitcher_id):
    all_pitches = []
    print(game_records)
    for record in game_records:
        total_pitches = 0
        game_id   = record["game_id"]
        game_date = record["game_date"]
        season    = record["season"]

        all_plays = playbyplay_data["allPlays"]

        for play in all_plays:
            if play["matchup"]["pitcher"]["id"] == pitcher_id:
                inning = play["about"]["inning"]
                half_inning = play["about"]["halfInning"]
                at_bat_index = play["about"]["atBatIndex"]
                at_bat_result = play["result"]["event"]
                batter_id = play["matchup"]["batter"]["id"]
                batter_name = play["matchup"]["batter"]["fullName"]
            
                for event in play["playEvents"]:
                    if event["isPitch"] == True:
                        total_pitches += 1
                        pitch_type = event["details"]["type"]["description"]
                        pitch_result = event["details"]["description"]
                        all_pitches.append({
                            "game_id": game_id,
                            "game_date": game_date,
                            "season": season,
                            "inning": inning,
                            "half_inning": half_inning,
                            "at_bat_index": at_bat_index,
                            "pitcher_id": pitcher_id,
                            "pitcher_name": play["matchup"]["pitcher"]["fullName"],
                            "batter_id": batter_id,
                            "batter_name": batter_name,
                            "pitch_number": event["pitchNumber"],
                            "total_pitch_count": total_pitches,
                            "pitch_type_code": event["details"]["type"]["code"],
                            "pitch_type_name": event["details"]["type"]["description"],
                            "pitch_code": event["details"]["code"],
                            "pitch_description": event["details"]["description"],
                            "is_strike": event["details"]["isStrike"],
                            "is_ball": event["details"]["isBall"],
                            "is_in_play": event["details"]["isInPlay"],
                            "start_speed": event.get("pitchData", {}).get("startSpeed"),
                            "end_speed": event.get("pitchData", {}).get("endSpeed"),
                            "strike_zone_top": event.get("pitchData", {}).get("strikeZoneTop"),
                            "strike_zone_bottom": event.get("pitchData", {}).get("strikeZoneBottom"),
                            "spin_rate": event.get("pitchData", {}).get("breaks", {}).get("spinRate"),
                            "spin_direction": event.get("pitchData", {}).get("breaks", {}).get("spinDirection"),
                            "zone": event.get("pitchData", {}).get("zone"),
                            "px": round(event.get("pitchData", {}).get("coordinates", {}).get("pX"), 3),
                            "pz": round(event.get("pitchData", {}).get("coordinates", {}).get("pZ"), 3),

                            "break_angle": event.get("pitchData", {}).get("breaks", {}).get("breakAngle"),
                            "break_length": event.get("pitchData", {}).get("breaks", {}).get("breakLength"),
                            "break_vertical": event.get("pitchData", {}).get("breaks", {}).get("breakVerticalInduced"),
                            "break_horizontal": event.get("pitchData", {}).get("breaks", {}).get("breakHorizontal"),
                            "balls": event.get("count", {}).get("balls"),
                            "strikes": event.get("count", {}).get("strikes"),
                            "outs": event.get("count", {}).get("outs"),
                            "at_bat_result": play["result"]["event"],
                            "at_bat_description": play["result"]["description"],
                            "pitch_start_time": play["about"]["startTime"],
                            "pitch_end_time": play["about"]["endTime"]
                        })
    return all_pitches