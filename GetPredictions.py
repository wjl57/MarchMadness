from __future__ import print_function

from itertools import chain

import requests
from bs4 import BeautifulSoup
from collections import Counter
import statistics

from matplotlib.offsetbox import OffsetImage, AnnotationBbox, TextArea

import Constants
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import shutil
from os.path import exists

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/70.0.3538.110 Safari/537.36 '
}

entries = Constants.ENTRIES[Constants.YEAR]

all_teams = []
all_actual_matchups = []


def set_all_teams():
    if len(all_teams) > 0:
        return all_teams
    content = get_content_for(next(iter(entries)))
    for matchup_div in extract_matchup_divs(content, Constants.min_matchup_id_round_64, Constants.max_matchup_id_round_64):
        slot_divs = matchup_div.find_all("div", "slot")
        for slot_div in slot_divs:
            team = calculate_team(slot_div)
            all_teams.append(team)


def save_logo(abbrev, logo_url):
    filename = 'icons/' + abbrev + '.png'
    if exists(filename):
        return filename
    else:
        r = requests.get(logo_url, stream=True)
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            # Open a local file with wb ( write binary ) permission.
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return filename


def set_all_actual_matchups():
    if len(all_actual_matchups) > 0:
        return all_actual_matchups
    content = get_content_for(next(iter(entries)))
    for matchup_div in extract_matchup_divs(content, Constants.min_matchup_id_round_64, Constants.championship_matchup_id):
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
    for matchup_div in extract_matchup_divs(content, matchup_id_min, matchup_id_max):
        slots = matchup_div.find_all("div", "slot")
        for slot in slots:
            selected_to_advance = slot.find("span", {"class", "selectedToAdvance"})
            if selected_to_advance is not None:
                predicted_winner_name = selected_to_advance.find("span", "name").text
                predicted_winners.append(predicted_winner_name)
    return predicted_winners


def extract_all_picks_counter(content):
    all_winners = extract_picks(content, Constants.min_matchup_id_round_64, Constants.championship_matchup_id)
    all_winners_list = list(all_winners)
    return Counter(all_winners_list)


def get_content_for(name):
    url = "http://fantasy.espn.com/tournament-challenge-bracket/" + str(Constants.YEAR) + "/en/entry?entryID=" + str(entries[name])
    page = requests.get(url, headers=headers)
    return page.content


def calculate_team(slot_div):
    team_id = int(slot_div["data-teamid"])
    actual_team_span = slot_div.find("span", {"class": "actual"})
    team_name = actual_team_span.find("span", {"class": "name"}).text
    seed = int(actual_team_span.find("span", {"class": "seed"}).text)
    abbrev = actual_team_span.find("span", "abbrev").text
    logo_tag = actual_team_span.find("img", {"class": "logo"})
    logo_url = logo_tag["src"]
    logo_file = save_logo(abbrev, logo_url)
    return Team(team_name, seed, team_id, abbrev, logo_file)


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
            slot_1_div = self.matchup_div.select("div.slot.s_1")[0]
            slot_2_div = self.matchup_div.select("div.slot.s_2")[0]
            self.team_1 = calculate_team(slot_1_div)
            self.team_2 = calculate_team(slot_2_div)
            self.winner = self.team_1 if slot_1_div.select("span.actual.winner") else self.team_2
        else:
            self.score_away = None
            self.score_home = None
            self.team_1 = None
            self.team_2 = None
            self.winner = None

    def calculate_round_number(self):
        if Constants.min_matchup_id_round_64 <= self.matchup_id <= Constants.max_matchup_id_round_64:
            return 1
        if Constants.min_matchup_id_round_32 <= self.matchup_id <= Constants.max_matchup_id_round_32:
            return 2
        if Constants.min_matchup_id_sweet_16 <= self.matchup_id <= Constants.max_matchup_id_sweet_16:
            return 3
        if Constants.min_matchup_id_elite_8 <= self.matchup_id <= Constants.max_matchup_id_elite_8:
            return 4
        if Constants.min_matchup_id_final_4 <= self.matchup_id <= Constants.max_matchup_id_final_4:
            return 5
        if Constants.championship_matchup_id == self.matchup_id:
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
        s = "Matchup ID: " + str(self.matchup_id) + " (" + self.region + " Round " + str(self.round_number) + ")\n"
        if self.team_1 is not None and self.team_2 is not None:
            s += str(self.team_1) + " vs " + str(self.team_2) + "\n"
        if self.game_complete:
            s += "Final Score: " + str(self.score_away) + " to " + str(self.score_home) + "\n"
            s += "Won by " + str(self.winner) + "\n"
        else:
            s += "Game not started yet\n"
        # s += "Team ID: " + str(self.team_id) + ", "
        # s += "Region: " + self.region + "\n"
        return s


class Team:
    def __init__(self, team_name, seed, team_id, abbrev, logo_file):
        self.name = team_name
        self.seed = seed
        self.team_id = team_id
        self.region = calculate_team_region(team_id)
        self.abbrev = abbrev
        self.logo_file = logo_file
        self.adjusted_seed = self.seed + int((team_id - 1) / 16) / 4 + 0.125

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
    s = title + ": " + str(scores) + " Total: " + str(sum(scores)) + ", Average: " + str(sum(scores) / len(scores))
    return s


def generate_team_plot(all_predicted_results, all_actual_matchups):
    adjusted_seeds = np.array([pr.team.adjusted_seed for pr in all_predicted_results])
    columns = [pr.predicted_wins for pr in all_predicted_results]
    fig, ax = plt.subplots()

    # Include team logos
    for idx, pr in enumerate(all_predicted_results):
        arr_team = mpimg.imread(pr.team.logo_file)
        imagebox_team = OffsetImage(arr_team, zoom=0.5)
        ab = AnnotationBbox(imagebox_team, (adjusted_seeds[idx], -0.2), bboxprops=dict(edgecolor='white'))
        ax.add_artist(ab)

    # Include predictions as a boxplot
    medianprops = dict(linestyle='None', linewidth=2.5, color='firebrick')
    meanlineprops = dict(linestyle='-', linewidth=2.5, color='C3')
    bplot = ax.boxplot(columns, whis=(0, 100), widths=0.25 / 5, meanline=True, showmeans=True, medianprops=medianprops, meanprops=meanlineprops,
                       positions=adjusted_seeds, patch_artist=True, zorder=2)
    for patch in bplot['boxes']:
        patch.set(color='C0', linewidth=2)

    # Include horizontal dotted lines for historical wins by seed
    historical_wins_by_seed = [3.361, 2.354, 1.847, 1.514, 1.119, 1.07, 0.902, 0.709, 0.591, 0.619, 0.64, 0.521, 0.257, 0.167, 0.077, 0.007]
    plt.hlines(historical_wins_by_seed, np.arange(1, 17, 1), np.arange(2, 18, 1), colors='C1', linestyles='dotted', zorder=1, label='Historical wins per seed')

    # Include actual wins by team so far
    actual_winners = [am.winner.name for am in all_actual_matchups if am.winner is not None]
    actual_team_wins_counter = Counter(actual_winners)
    actual_wins_by_team = [actual_team_wins_counter[pr.team.name] for pr in all_predicted_results]
    max_wins_so_far = 2
    # plt.scatter(adjusted_seeds, actual_wins_by_team, c=['C3' if w < max_wins_so_far else 'C2' for w in actual_wins_by_team], marker='X', zorder=4, label='Actual Wins (so far)')
    plt.scatter(adjusted_seeds, actual_wins_by_team, c='C2', marker='D', s=25, zorder=3, label='Actual Wins (so far)')

    # Include flavor text
    stpeters = next(pr for pr in all_predicted_results if pr.team.abbrev == 'SPU')
    stpeters_wins = actual_team_wins_counter[stpeters.team.name]
    plt.annotate('Sponsored by\nNBC Peacock!',
                 xy=(stpeters.team.adjusted_seed, stpeters_wins),
                 xytext=(0.5, 20),
                 textcoords='offset points',
                 weight='bold',
                 ha='center',
                 va="center"
                 )

    # Set axis
    ax.set_title('Predicted Wins by Team')
    ax.set_xlabel("Seed", labelpad=10)
    ax.set_ylabel("Predicted Wins", labelpad=10)
    ax.set_ylim(-1, 7)
    ax.set_xticks(range(1, 17))
    ax.set_xticklabels(range(1, 17))
    leg = ax.legend()
    plt.show()


if __name__ == "__main__":
    set_all_teams()
    set_all_actual_matchups()

    print("------------------------------------------------------")
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

    # west_scores = get_scores('West', 1, 1)
    # print(display_scores('West', west_scores))
    # east_scores = get_scores('East', 1, 1)
    # print(display_scores('East', east_scores))
    # south_scores = get_scores('South', 1, 1)
    # print(display_scores('South', south_scores))
    # midwest_scores = get_scores('Midwest', 1, 1)
    # print(display_scores('Midwest', midwest_scores))

    all_entries = []
    for name, bracket_id in entries.items():
        print("------------------------------------------------------")
        print(name)
        print("------------------------------------------------------")
        entry = Entry(name, bracket_id)
        all_entries.append(entry)
        print(entry.picks_counter)

    all_predicted_results = []
    for team in all_teams:
        predicted_wins_dict = {entry.name: entry.picks_counter[team.name] for entry in all_entries}
        # predicted_wins = [entry.picks_counter[team.name] for entry in all_entries]
        predicted_result = PredictedResults(team, predicted_wins_dict)
        all_predicted_results.append(predicted_result)
    # Order predictions by seed number
    all_predicted_results = sorted(all_predicted_results, key=lambda pr: pr.team.seed)
    #
    # for predicted_result in all_predicted_results:
    #     print(predicted_result)
    #
    # predicted_result_average_wins = sorted(all_predicted_results, key=lambda pr: pr.average_wins, reverse=True)
    # predicted_result_std_dev = sorted(all_predicted_results, key=lambda pr: pr.std_dev, reverse=True)
    #
    # print("HIGHEST AVERAGE")
    # for pr in predicted_result_average_wins[0:5]:
    #     print(pr)
    #
    # print("HIGHEST STD DEV")
    # for pr in predicted_result_std_dev[0:5]:
    #     print(pr)
    #
    # print("LOWEST STD DEV")
    # for pr in predicted_result_std_dev[-13:-8]:
    #     print(pr)
    #
    # no_wins_predicted = filter(lambda pr: pr.max == 0, all_predicted_results)
    #
    # print("NO WINS")
    # for pr in no_wins_predicted:
    #     print(pr.team)
    #

    generate_team_plot(all_predicted_results, all_actual_matchups)
