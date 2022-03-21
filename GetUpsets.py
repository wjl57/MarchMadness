import numpy as np

import Constants
from GetPredictions import extract_matchup_divs, get_content_for
import matplotlib.pyplot as plt


class Upset:
    def __init__(self, name, num_games_correct, num_upsets_predicted, num_upsets_correct, upset_score, potential_upset_score):
        self.name = name
        self.num_games_correct = num_games_correct
        self.num_upsets_predicted = num_upsets_predicted
        self.num_upsets_correct = num_upsets_correct
        self.upset_score = upset_score
        self.potential_upset_score = potential_upset_score
        self.average_upset_score_correct = self.upset_score / self.num_upsets_correct
        self.average_upset_score = self.potential_upset_score / self.num_upsets_predicted


def extract_upsets(content, matchup_id_min, matchup_id_max):
    num_games_correct = 0
    num_upsets_predicted = 0
    num_upsets_correct = 0
    potential_upset_score = 0
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
            num_games_correct += 1
        if predicted_upset:
            num_upsets_predicted += 1
            upset_score_delta = abs(team_2_seed - team_1_seed)
            potential_upset_score += upset_score_delta
            print("Predicted upset: " + team_1_name + " (" + str(team_1_seed) + ") vs " + team_2_name + " (" + str(team_2_seed) + ")")
            if game_predicted_correctly:
                num_upsets_correct += 1
                upset_score += upset_score_delta
                print("Prediction correct! Worth " + str(upset_score_delta))
    return num_games_correct, num_upsets_predicted, num_upsets_correct, upset_score, potential_upset_score


def extract_optimal_upsets(content, matchup_id_min, matchup_id_max):
    num_games_correct = 0
    num_upsets_predicted = 0
    num_upsets_correct = 0
    potential_upset_score = 0
    upset_score = 0
    for matchup_div in extract_matchup_divs(content, matchup_id_min, matchup_id_max):
        slot_1_div = matchup_div.select("div.slot.s_1")[0]
        team_1_won = slot_1_div.select("span.actual.winner")
        team_1_seed = int(slot_1_div.find("span", {"class": "seed"}).text)
        team_1_name = slot_1_div.find("span", {"class": "name"}).text
        slot_2_div = matchup_div.select("div.slot.s_2")[0]
        team_2_won = slot_2_div.select("span.actual.winner")
        team_2_seed = int(slot_2_div.find("span", {"class": "seed"}).text)
        team_2_name = slot_2_div.find("span", {"class": "name"}).text
        was_upset = team_1_seed > team_2_seed if team_1_won else team_2_seed > team_1_seed
        num_games_correct += 1
        if was_upset:
            print("Predicted upset: " + team_1_name + " (" + str(team_1_seed) + ") vs " + team_2_name + " (" + str(team_2_seed) + ")")
            num_upsets_predicted += 1
            num_upsets_correct += 1
            upset_score_delta = abs(team_2_seed - team_1_seed)
            potential_upset_score += upset_score_delta
            upset_score += upset_score_delta
            print("Prediction correct! Worth " + str(upset_score_delta))
    return num_games_correct, num_upsets_predicted, num_upsets_correct, upset_score, potential_upset_score


def show_upset_score_plot(upsets):
    labels = [upset.name for upset in upsets]
    potential_upset_scores = [upset.potential_upset_score for upset in upsets]
    upset_scores = [upset.upset_score for upset in upsets]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width / 2, potential_upset_scores, width, label='Potential Upset Score')
    rects2 = ax.bar(x + width / 2, upset_scores, width, label='Actual Upset Score')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Scores')
    ax.set_title('Upset Score')
    ax.set_xticks(x, labels)
    ax.legend()

    ax.bar_label(rects1, padding=3)
    ax.bar_label(rects2, padding=3)

    fig.tight_layout()

    plt.show()


def show_upset_count_plot(upsets):
    labels = [upset.name for upset in upsets]
    num_upsets_predicted = [upset.num_upsets_predicted for upset in upsets]
    num_upsets_correct = [upset.num_upsets_correct for upset in upsets]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width / 2, num_upsets_predicted, width, label='Num Upsets Predicted')
    rects2 = ax.bar(x + width / 2, num_upsets_correct, width, label='Num Upsets Correct')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Count')
    ax.set_title('Upset Count')
    ax.set_xticks(x, labels)
    ax.legend()

    ax.bar_label(rects1, padding=3)
    ax.bar_label(rects2, padding=3)

    fig.tight_layout()

    plt.show()


def show_average_upset_score_plot(upsets):
    labels = [upset.name for upset in upsets]
    average_upset_score = [round(upset.average_upset_score, 1) for upset in upsets]
    average_upset_score_correct = [round(upset.average_upset_score_correct, 1) for upset in upsets]

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width / 2, average_upset_score, width, label='Avg Predicted Upset Score')
    rects2 = ax.bar(x + width / 2, average_upset_score_correct, width, label='Avg Correct Upset Score')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Score')
    ax.set_title('Average Upset Scores')
    ax.set_xticks(x, labels)
    ax.legend()

    ax.bar_label(rects1, padding=3)
    ax.bar_label(rects2, padding=3)

    fig.tight_layout()

    plt.show()


if __name__ == "__main__":

    entries = Constants.ENTRIES[Constants.YEAR]
    upsets = []
    for name, bracket_id in entries.items():
        content = get_content_for(name)
        games_predicted_correctly, upset_predicted, num_upsets_correct, upset_score, potential_upset_score = extract_upsets(content,
                                                                                                                                   Constants.min_matchup_id_round_64,
                                                                                                                                   Constants.max_matchup_id_round_64)
        upset = Upset(name, games_predicted_correctly, upset_predicted, num_upsets_correct, upset_score, potential_upset_score)
        print("------------------------------------------------------")
        print(upset.name)
        print("------------------------------------------------------")
        print("Games predicted correctly: " + str(upset.num_games_correct))
        print("Upsets predicted: " + str(upset.num_upsets_predicted))
        print("Upsets predicted correctly: " + str(upset.num_upsets_correct))
        print("Upset score: " + str(upset.upset_score))
        print("Average predicted upset score: " + str(upset.average_upset_score))
        print("Average correct upset score: " + str(upset.average_upset_score_correct))
        upsets.append(upset)
        upsets = sorted(upsets, key=lambda u: u.potential_upset_score, reverse=True)

    content = get_content_for(next(iter(entries)))
    games_predicted_correctly, upset_predicted, num_upsets_correct, upset_score, potential_upset_score = extract_optimal_upsets(content, Constants.min_matchup_id_round_64, Constants.max_matchup_id_round_64)
    optimal_upset = Upset('Optimal', games_predicted_correctly, upset_predicted, num_upsets_correct, upset_score, potential_upset_score)
    upsets.append(optimal_upset)
    # show_upset_score_plot(upsets)
    # show_upset_count_plot(upsets)
    show_average_upset_score_plot(upsets)

