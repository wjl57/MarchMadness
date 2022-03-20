import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from collections import Counter

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/70.0.3538.110 Safari/537.36 '
}

entries = {
    "Will": 53914595,
    # "Harry": 61337382,
    # "Cathy": 66791702,
    # "Breton": 64261292,
    # "Louis": 65511775,
    # "Vitaliy": 65326118,
    # "JinWang": 63398705,
    # "Ted": 63894438,
    # "Jared": 69932613,
    # "Thomas": 57461192,
    # "Andrew": 54503876,
    # "Andy": 64811291,
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
            all_teams.add(slot.find("span", "name").text)
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


class User:
    def __init__(self, name, bracket_id):
        self.name = name
        self.bracket_id = bracket_id
        content = get_content_for(name)
        self.content = content
        self.picks_counter = extract_all_picks_counter(content)


set_all_teams()
print(all_teams)

for name, bracket_id in entries.items():
    # picks = extract_all_picks_counter(page.content)
    user = User(name, bracket_id)
    # page = requests.get("http://fantasy.espn.com/tournament-challenge-bracket/2022/en/entry?entryID=" + str(entry_id), headers=headers)
    print("------------------------------------------------------")
    print(user.name)
    print("------------------------------------------------------")
    print(user.picks_counter)
    # teams[name] = list(extract_predictions(page.content))
