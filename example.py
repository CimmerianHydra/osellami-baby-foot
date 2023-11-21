from player_list import PlayerList
from OFB import Team
from OFB import Role
from icecream import ic
import numpy as np

pl = PlayerList()
pl.erase_list()
pl.add_new_player("Niki Di Giano")
pl.add_new_player("Ciro Pentangelo")
pl.add_new_player("Vittorio Grimaldi")
pl.add_new_player("Marco Gardina")

for p in pl.DATA:
    print(f"{p.name} has Elo rating in ATK equal to {p.atk_elo}.")
    
# ADDING A MATCH

team_1 = Team(pl.search_by_name("Niki Di Giano"), pl.search_by_name("Ciro Pentangelo"))
team_2 = Team(pl.search_by_name("Vittorio Grimaldi"), pl.search_by_name("Marco Gardina"))

pl.resolve_match(team_1, team_2, 7, 8)
pl.resolve_match(team_1, team_2, 7, 8)
pl.resolve_match(team_1, team_2, 7, 8)
pl.resolve_match(team_1, team_2, 7, 8)

for p in pl.DATA:
    print(f"{p.name} has Elo rating in ATK equal to {p.atk_elo}.")

for r in Role:
    print([f"{p.name}: {int(p.elo(r))}" for p in pl.leaderboard(r)])