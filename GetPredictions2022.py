from __future__ import print_function
import requests
from bs4 import BeautifulSoup
from collections import Counter
import statistics


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/70.0.3538.110 Safari/537.36 '
}

entries = {
    "Will": 53914595,
    "Harry": 61337382,
    "Cathy": 66791702,
    "Breton": 64261292,
    "Louis": 65511775,
    "Vitaliy": 65326118,
    "JinWang": 63398705,
    "Ted": 63894438,
    "Jared": 69932613,
    "Thomas": 57461192,
    "Andrew": 54503876,
    "Andy": 64811291,
    "Check": 56824064,
    "Caitlin": 66188779
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

all_teams = set()


def set_all_teams():
    if len(all_teams) > 0:
        return all_teams
    content = get_content_for(next(iter(entries)))
    for matchup in extract_matchups(content, min_matchup_id_round_64, max_matchup_id_round_64):
        slots = matchup.find_all("div", "slot")
        for slot in slots:
            team = slot.find("span", "name").text
            seed = slot.find("span", "seed").text
            all_teams.add(Team(team, seed))
    return all_teams


def extract_matchups(content, matchup_id_min, matchup_id_max):
    soup = BeautifulSoup(content, "html.parser")
    bracket_wrapper = soup.find("div", {"class": "bracketWrapper"})
    matchups = bracket_wrapper.find_all("div", {"class": "matchup"})
    for matchup in matchups:
        matchup_id = int(matchup["data-index"])
        # pick the matchups we care about
        if matchup_id_min <= matchup_id <= matchup_id_max:
            yield matchup


def extract_picks(content, matchup_id_min, matchup_id_max):
    predicted_winners = []
    for matchup in extract_matchups(content, matchup_id_min, matchup_id_max):
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
    url = "http://fantasy.espn.com/tournament-challenge-bracket/2022/en/entry?entryID=" + str(entries[name])
    page = requests.get(url, headers=headers)
    return page.content


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed

    def __repr__(self):
        return self.name + " (" + self.seed + ")"


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


set_all_teams()
print(all_teams)

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

no_wins_predicted = filter(lambda pr: pr.max == 0, all_predicted_results)

print("NO WINS")
for pr in no_wins_predicted:
    print(pr.team)
