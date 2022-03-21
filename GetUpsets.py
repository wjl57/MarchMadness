import Constants
from GetPredictions import extract_matchup_divs, get_content_for


def extract_upsets(content, matchup_id_min, matchup_id_max):
    games_predicted_correctly = 0
    upset_predicted = 0
    upset_predicted_correctly = 0
    upset_score = 0
    for matchup_div in extract_matchup_divs(content, matchup_id_min, matchup_id_max):
        slot_1_div = matchup_div.select("div.slot.s_1")[0]
        team_1_selected = slot_1_div.find("span", {"class", "selectedToAdvance"})
        team_1_won = slot_1_div.select("span.actual.winner")
        team_1_seed = int(slot_1_div.find("span", {"class": "seed"}).text)
        team_1_name = slot_1_div.find("span", {"class": "name"}).text
        slot_2_div = matchup_div.select("div.slot.s_2")[0]
        team_2_selected = slot_2_div.find("span", {"class", "selectedToAdvance"})
        team_2_won = slot_2_div.select("span.actual.winner")
        team_2_seed = int(slot_2_div.find("span", {"class": "seed"}).text)
        team_2_name = slot_2_div.find("span", {"class": "name"}).text
        predicted_upset = team_1_seed > team_2_seed if team_1_selected else team_2_seed > team_1_seed
        game_predicted_correctly = (team_1_won and team_1_selected) or (team_2_won and team_2_selected)
        if game_predicted_correctly:
            games_predicted_correctly += 1
        if predicted_upset:
            upset_predicted += 1
            print("Predicted upset: " + team_1_name + " (" + str(team_1_seed) + ") vs " + team_2_name + " (" + str(team_2_seed) + ")")
            if game_predicted_correctly:
                upset_predicted_correctly += 1
                upset_score_delta = abs(team_2_seed - team_1_seed)
                upset_score += upset_score_delta
                print("Prediction correct! Worth " + str(upset_score_delta))
    return games_predicted_correctly, upset_predicted, upset_predicted_correctly, upset_score


if __name__ == "__main__":
    entries = Constants.ENTRIES[Constants.YEAR]
    for name, bracket_id in entries.items():
        print("------------------------------------------------------")
        print(name)
        print("------------------------------------------------------")
        content = get_content_for(name)
        games_predicted_correctly, upset_predicted, upset_predicted_correctly, upset_score = extract_upsets(content, Constants.min_matchup_id_round_64,
                                                                                                            Constants.max_matchup_id_round_64)
        print("Games predicted correctly: " + str(games_predicted_correctly))
        print("Upsets predicted: " + str(upset_predicted))
        print("Upsets predicted correctly: " + str(upset_predicted_correctly))
        print("Upsets score: " + str(upset_score))
