from __future__ import print_function

from itertools import chain

import requests
from bs4 import BeautifulSoup
from collections import Counter
import statistics
import Constants
import numpy as np
import matplotlib.pyplot as plt
import math

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/70.0.3538.110 Safari/537.36 '
}

total_teams = 64
min_matchup_id_round_64 = 0
max_matchup_id_round_64 = 31
min_matchup_id_round_32 = max_matchup_id_round_64 + 1
max_matchup_id_round_32 = max_matchup_id_round_64 + 16
min_matchup_id_sweet_16 = max_matchup_id_round_32 + 1
max_matchup_id_sweet_16 = max_matchup_id_round_32 + 8
min_matchup_id_elite_8 = max_matchup_id_sweet_16 + 1
max_matchup_id_elite_8 = max_matchup_id_sweet_16 + 4
min_matchup_id_final_4 = max_matchup_id_elite_8 + 1
max_matchup_id_final_4 = max_matchup_id_elite_8 + 2
championship_matchup_id = max_matchup_id_final_4 + 1

entries = Constants.ENTRIES[Constants.YEAR]

all_teams = []
all_actual_matchups = []


def set_all_teams():
    if len(all_teams) > 0:
        return all_teams
    content = get_content_for(next(iter(entries)))
    for matchup_div in extract_matchup_divs(content, min_matchup_id_round_64, max_matchup_id_round_64):
        slots = matchup_div.find_all("div", "slot")
        for slot in slots:
            team = slot.find("span", "name").text
            team_id = int(slot["data-teamid"])
            seed = int(slot.find("span", "seed").text)
            all_teams.append(Team(team, seed, team_id))
    # return sorted(all_teams, key=lambda t: t.team_id)


def set_all_actual_matchups():
    if len(all_actual_matchups) > 0:
        return all_actual_matchups
    content = get_content_for(next(iter(entries)))
    for matchup_div in extract_matchup_divs(content, min_matchup_id_round_64, championship_matchup_id):
        matchup_id = int(matchup_div["data-index"])
        actual_matchup = ActualMatchup(matchup_id, matchup_div)
        all_actual_matchups.append(actual_matchup)


def extract_matchup_divs(content, matchup_id_min, matchup_id_max):
    soup = BeautifulSoup(content, "html.parser")
    bracket_wrapper = soup.find("div", {"class": "bracketWrapper"})
    matchup_divs = bracket_wrapper.find_all("div", {"class": "matchup"})
    for matchup_div in matchup_divs:
        matchup_id = int(matchup_div["data-index"])
        # pick the matchups we care about
        if matchup_id_min <= matchup_id <= matchup_id_max:
            yield matchup_div


def calculate_team_region(team_id):
    if 0 < team_id <= 16:
        return "West"
    if team_id <= 32:
        return "East"
    if team_id <= 48:
        return "South"
    if team_id <= 64:
        return "Midwest"
    raise Exception("Error calculating region for team " + str(team_id))


def extract_picks(content, matchup_id_min, matchup_id_max):
    predicted_winners = []
    for matchup in extract_matchup_divs(content, matchup_id_min, matchup_id_max):
        slots = matchup.find_all("div", "slot")
        for slot in slots:
            selected_to_advance = slot.find("span", {"class", "selectedToAdvance"})
            if selected_to_advance is not None:
                predicted_winner_name = selected_to_advance.find("span", "name").text
                predicted_winners.append(predicted_winner_name)
    return predicted_winners


def extract_all_picks_counter(content):
    all_winners = extract_picks(content, min_matchup_id_round_64, championship_matchup_id)
    all_winners_list = list(all_winners)
    return Counter(all_winners_list)


def get_content_for(name):
    url = "http://fantasy.espn.com/tournament-challenge-bracket/" + str(Constants.YEAR) + "/en/entry?entryID=" + str(entries[name])
    page = requests.get(url, headers=headers)
    return page.content


class ActualMatchup:
    def __init__(self, matchup_id, matchup_div):
        self.matchup_id = matchup_id
        self.round_number = self.calculate_round_number()
        self.matchup_div = matchup_div
        game_progress = self.matchup_div.find("a", {"class": "gameProgress final"})
        self.game_complete = game_progress is not None
        self.region = self.calculate_region()
        if self.game_complete:
            score_away_span = game_progress.select("span.score.away")[0]
            score_home_span = game_progress.select("span.score.home")[0]
            self.score_away = int(score_away_span.text)
            self.score_home = int(score_home_span.text)
            self.team_1 = ActualMatchup.calculate_team(self.matchup_div.select("div.slot.s_1")[0])
            self.team_2 = ActualMatchup.calculate_team(self.matchup_div.select("div.slot.s_2")[0])
        else:
            self.score_away = None
            self.score_home = None
            self.team_1 = None
            self.team_2 = None

    @staticmethod
    def calculate_team(slot_div):
        print(slot_div)
        team_id_str = slot_div["data-teamid"]
        print(team_id_str)
        team_id = int(team_id_str)
        actual_team_span = slot_div.find("span", {"class": "actual"})
        # print(actual_team_span)
        team_name = actual_team_span.find("span", {"class": "name"}).text
        seed_span = actual_team_span.find("span", {"class": "seed"})
        seed = int(seed_span.text)
        return Team(team_name, seed, team_id)

        # self.team_1 = team_1,
        # self.team_2 = team_2,
        # self.game_complete = game_complete
        # self.team_1_score = team_1_score
        # self.team_2_score = team_2_score
        # self.region = team_1.region if team_1.region == team_2.region else "No region"

    def calculate_round_number(self):
        if min_matchup_id_round_64 <= self.matchup_id <= max_matchup_id_round_64:
            return 1
        if min_matchup_id_round_32 <= self.matchup_id <= max_matchup_id_round_32:
            return 2
        if min_matchup_id_sweet_16 <= self.matchup_id <= max_matchup_id_sweet_16:
            return 3
        if min_matchup_id_elite_8 <= self.matchup_id <= max_matchup_id_elite_8:
            return 4
        if min_matchup_id_final_4 <= self.matchup_id <= max_matchup_id_final_4:
            return 5
        if championship_matchup_id == self.matchup_id:
            return 6

    def calculate_region(self):
        if self.matchup_id < 8:
            return "West"
        if self.matchup_id < 16:
            return "East"
        if self.matchup_id < 24:
            return "South"
        if self.matchup_id < 32:
            return "Midwest"
        if self.matchup_id < 36:
            return "West"
        if self.matchup_id < 40:
            return "East"
        if self.matchup_id < 44:
            return "South"
        if self.matchup_id < 48:
            return "Midwest"
        if self.matchup_id < 50:
            return "West"
        if self.matchup_id < 52:
            return "East"
        if self.matchup_id < 54:
            return "South"
        if self.matchup_id < 56:
            return "Midwest"
        if self.matchup_id < 57:
            return "West"
        if self.matchup_id < 58:
            return "East"
        if self.matchup_id < 59:
            return "South"
        if self.matchup_id < 60:
            return "Midwest"
        return "No region"

    def __repr__(self):
        # s = self.matchup_id
        s = "Matchup ID: " + str(self.matchup_id) + " (" + self.region + " Round " + str(self.round_number) + ")\n"
        if self.team_1 is not None and self.team_2 is not None:
            s += str(self.team_1) + " vs " + str(self.team_2) + "\n"
        if self.game_complete:
            s += "Final Score: " + str(self.score_away) + " to " + str(self.score_home) + "\n"
        else:
            s += "Game not started yet\n"
        # s += "Team ID: " + str(self.team_id) + ", "
        # s += "Region: " + self.region + "\n"
        return s


class Team:
    def __init__(self, name, seed, team_id):
        self.name = name
        self.seed = seed
        self.team_id = team_id
        self.region = calculate_team_region(team_id)

    def __repr__(self):
        s = self.name + " (" + str(self.seed) + ")\n"
        s += "Team ID: " + str(self.team_id) + ", "
        s += "Region: " + self.region + "\n"
        return s

    def __str__(self):
        s = self.name + " (" + str(self.seed) + ")"
        return s


class Entry:
    def __init__(self, name, bracket_id):
        self.name = name
        self.bracket_id = bracket_id
        content = get_content_for(name)
        self.content = content
        self.picks_counter = extract_all_picks_counter(content)


class PredictedResults:
    def __init__(self, team, predicted_wins_dict):
        self.predicted_wins_dict = predicted_wins_dict
        predicted_wins = sorted(predicted_wins_dict.values(), reverse=True)
        self.predicted_wins = predicted_wins
        self.team = team
        self.average_wins = sum(predicted_wins) / len(predicted_wins)
        self.std_dev = statistics.stdev(predicted_wins)
        self.min = min(predicted_wins)
        self.max = max(predicted_wins)
        self.std_dev_min = 0 if self.std_dev == 0 else (self.min - self.average_wins) / self.std_dev
        self.std_dev_max = 0 if self.std_dev == 0 else (self.max - self.average_wins) / self.std_dev

    def __repr__(self):
        s = "------------------------------------------------------\n"
        s += "Team: " + repr(self.team) + "\n"
        s += "------------------------------------------------------\n"
        s += "Predicted Wins: " + str(self.predicted_wins) + "\n"
        s += "Predicted Win Dict: " + str(self.predicted_wins_dict) + "\n"
        s += "Average Wins: " + str(self.average_wins) + "\n"
        s += "Std Dev: " + str(self.std_dev) + "\n"
        s += "Range: " + str(self.min) + " to " + str(self.max) + "\n"
        s += "Std Dev Range: " + str(self.std_dev_min) + " to " + str(self.std_dev_max) + "\n"
        return s


def get_scores(region, min_round, max_round):
    non_flattened_scores = [[m.score_away, m.score_home] for m in all_actual_matchups if m.region == region and min_round <= m.round_number <= max_round]
    return list(chain.from_iterable(non_flattened_scores))


def display_scores(title, scores):
    s = title + ": " + str(scores) + " Total: " + str(sum(scores)) + ", Average: " + str(sum(scores)/len(scores))
    return s


set_all_teams()
set_all_actual_matchups()

print("TEAMS")
print("------------------------------------------------------")
for team in all_teams:
    print(team)
print("------------------------------------------------------")
print()
print()
print("------------------------------------------------------")
print("MATCHUPS")
print("------------------------------------------------------")
for actual_matchup in all_actual_matchups:
    print(actual_matchup)

print("------------------------------------------------------")
print()
print()

west_scores = get_scores('West', 1, 1)
print(display_scores('West', west_scores))
east_scores = get_scores('East', 1, 1)
print(display_scores('East', east_scores))
south_scores = get_scores('South', 1, 1)
print(display_scores('South', south_scores))
midwest_scores = get_scores('Midwest', 1, 1)
print(display_scores('Midwest', midwest_scores))

all_entries = []
for name, bracket_id in entries.items():
    entry = Entry(name, bracket_id)
    all_entries.append(entry)
    print("------------------------------------------------------")
    print(entry.name)
    print("------------------------------------------------------")
    print(entry.picks_counter)

all_predicted_results = []
for team in all_teams:
    predicted_wins_dict = {entry.name: entry.picks_counter[team.name] for entry in all_entries}
    # predicted_wins = [entry.picks_counter[team.name] for entry in all_entries]
    predicted_result = PredictedResults(team, predicted_wins_dict)
    all_predicted_results.append(predicted_result)
# Order predictions by seed number
all_predicted_results = sorted(all_predicted_results, key=lambda pr: pr.team.seed)

for predicted_result in all_predicted_results:
    print(predicted_result)


predicted_result_average_wins = sorted(all_predicted_results, key=lambda pr: pr.average_wins, reverse=True)
predicted_result_std_dev = sorted(all_predicted_results, key=lambda pr: pr.std_dev, reverse=True)

print("HIGHEST AVERAGE")
for pr in predicted_result_average_wins[0:5]:
    print(pr)

print("HIGHEST STD DEV")
for pr in predicted_result_std_dev[0:5]:
    print(pr)

print("LOWEST STD DEV")
for pr in predicted_result_std_dev[-13:-8]:
    print(pr)

no_wins_predicted = filter(lambda pr: pr.max == 0, all_predicted_results)

print("NO WINS")
for pr in no_wins_predicted:
    print(pr.team)


x = [pr.team.seed for pr in all_predicted_results]
y = [pr.average_wins for pr in all_predicted_results]
colors = 'black'#np.random.rand(4)
area = 10
plt.scatter(x, y, s=area, c=colors, alpha=0.5)
plt.show()
