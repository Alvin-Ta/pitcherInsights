import requests

from config import BASE


def get_pitcher_game_ids(pitcher_id, seasons):
    game_records = []
    
    for season in seasons:
        response = requests.get(f"{BASE}/people/{pitcher_id}/stats?stats=gameLog&group=pitching&season={season}")
        data = response.json()

        splits = data["stats"][0]["splits"]
        
        for split in splits:
            game_records.append({
                "game_id":   split["game"]["gamePk"],
                "game_date": split["date"],
                "season":    int(split["season"])
            })
    # print(game_records)
    return game_records


def parse_pitchers(game_records, pitcher_id):
    all_pitches = []
    for record in game_records:
        total_pitches = 0
        game_id   = record["game_id"]
        game_date = record["game_date"]
        season    = record["season"]

        response = requests.get(f"{BASE}/game/{game_id}/playByPlay")
        data = response.json()
        all_plays = data["allPlays"]

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
                            "spin_rate": event.get("pitchData", {}).get("breaks", {}).get("spinRate"),
                            "zone": event.get("pitchData", {}).get("zone"),
                            "px": round(event.get("pitchData", {}).get("coordinates", {}).get("pX"), 3),
                            "pz": round(event.get("pitchData", {}).get("coordinates", {}).get("pZ"), 3),
                            "break_vertical": event.get("pitchData", {}).get("breaks", {}).get("breakVerticalInduced"),
                            "break_horizontal": event.get("pitchData", {}).get("breaks", {}).get("breakHorizontal"),
                            "balls": event.get("count", {}).get("balls"),
                            "strikes": event.get("count", {}).get("strikes"),
                            "outs": event.get("count", {}).get("outs"),
                            "at_bat_result": play["result"]["event"]
                        })
    return all_pitches




# get_pitcher_game_ids(656302, [2024, 2025])

# parse_pitchers(get_pitcher_game_ids(656302, [2024, 2025]), 656302)

# if __name__ == "__main__":
#     # just grab the first game from 2025 to test
#     game_records = get_pitcher_game_ids(656302, [2025])
#     first_game = [game_records[0]]  # just one game to keep it fast

#     print(f"Testing with game: {first_game[0]['game_id']} on {first_game[0]['game_date']}")
    
#     pitches = parse_pitchers(first_game, 656302)
    
#     print(f"Total pitches parsed: {len(pitches)}")
#     print()
#     print("First pitch:")
#     for key, value in pitches[0].items():
#         print(f"  {key}: {value}")
#     print()
#     print("Last pitch:")
#     for key, value in pitches[-1].items():
#         print(f"  {key}: {value}")


# if __name__ == "__main__":
#     game_records = get_pitcher_game_ids(656302, [2025])
#     first_game = [game_records[0]]

#     pitches = parse_pitchers(first_game, 656302)

#     # filter to inning 1 only
#     inning_1 = [p for p in pitches if p["inning"] == 1]

#     print(f"Game: {first_game[0]['game_id']} on {first_game[0]['game_date']}")
#     print(f"Inning 1 pitches: {len(inning_1)}")
#     print()

#     for pitch in inning_1:
#         print(f"  [{pitch['pitch_result_code']}] {pitch['pitch_type_name']} | {pitch['pitch_result_name']} | {pitch['start_speed']} mph | Spin: {pitch['spin_rate']} | vs {pitch['batter_name']} | Count: {pitch['balls']}-{pitch['strikes']}")