import numpy as np
from enum import Enum

R_PARAMETER = 500.0
K_MULTIPLIER = 50.0
K_PARAMETER = 300.0
MAX_SCORE = 8

class Role(Enum):
    ATK = 0
    DEF = 1

class Player:

    def __init__(self, name: str, atk_elo: float = 1200.0, def_elo: float = 1200.0) -> None:
        self.name = name
        self.atk_elo = atk_elo
        self.def_elo = def_elo
        self.atk_exp = 0
        self.def_exp = 0
    
    def add_elo(self, role:Role, value: float) -> None:
        match role:
            case Role.ATK: self.atk_elo += value
            case Role.DEF: self.def_elo += value
    
    def elo(self, role:Role) -> float:
        match role:
            case Role.ATK: return self.atk_elo
            case Role.DEF: return self.def_elo

    def K_factor(self, role:Role) -> float:
        match role:
            case Role.ATK: return K_MULTIPLIER * np.reciprocal( 1 + self.atk_exp/K_PARAMETER )
            case Role.DEF: return K_MULTIPLIER * np.reciprocal( 1 + self.def_exp/K_PARAMETER )

class Team:

    def __init__(self, attacker:Player, defender:Player) -> None:
        self.attacker = attacker
        self.defender = defender
    
    def players(self):
        return [self.attacker, self.defender]


class Match:

    def __init__(self, first_team:Team, second_team:Team, date=0) -> None:
        self.team_1 = first_team
        self.team_2 = second_team
    
    def teams(self):
        return [self.team_1, self.team_2]

    def f(self, elo_1, elo_2) -> float:
        return np.reciprocal(1 + 10**((elo_1 - elo_2)/R_PARAMETER))

    def cappotto_factor(self, score_difference) -> float:
        return 2 + (np.log10(np.abs(score_difference)) + 1)**3

    def resolve_match(self, first_team_score, second_team_score):
        assert first_team_score != second_team_score
        assert max(first_team_score, second_team_score) == MAX_SCORE

        team_1_win = int(first_team_score > second_team_score)
        team_2_win = 1 - team_1_win

        for t in self.teams():
            t.attacker.atk_exp += 1
            t.defender.def_exp += 1

        team_1_attacker_ES = 0.5*( self.f(self.team_2.attacker.atk_elo, self.team_1.attacker.atk_elo) +
                                   self.f(self.team_2.defender.def_elo, self.team_1.attacker.atk_elo) )
        team_1_defender_ES = 0.5*( self.f(self.team_2.attacker.atk_elo, self.team_1.defender.def_elo) +
                                   self.f(self.team_2.defender.def_elo, self.team_1.defender.def_elo) )
        team_2_attacker_ES = 0.5*( self.f(self.team_1.attacker.atk_elo, self.team_2.attacker.atk_elo) +
                                   self.f(self.team_1.defender.def_elo, self.team_2.attacker.atk_elo) )
        team_2_defender_ES = 0.5*( self.f(self.team_1.attacker.atk_elo, self.team_2.defender.def_elo) +
                                   self.f(self.team_1.defender.def_elo, self.team_2.defender.def_elo) )

        cappotto = self.cappotto_factor(np.abs(first_team_score - second_team_score))

        self.team_1.attacker.add_elo(Role.ATK, self.team_1.attacker.K_factor(Role.ATK) * cappotto * (team_1_win - team_1_attacker_ES))
        self.team_1.defender.add_elo(Role.DEF, self.team_1.defender.K_factor(Role.DEF) * cappotto * (team_1_win - team_1_defender_ES))
        self.team_2.attacker.add_elo(Role.ATK, self.team_2.attacker.K_factor(Role.ATK) * cappotto * (team_2_win - team_2_attacker_ES))
        self.team_2.defender.add_elo(Role.DEF, self.team_2.defender.K_factor(Role.ATK) * cappotto * (team_2_win - team_2_defender_ES))

if __name__ == 'main':
    from icecream import ic

    player_list = []

    player_list.append(
        Player("Niki Di Giano")
    )
    player_list.append(
        Player("Pasquale Barbato")
    )
    player_list.append(
        Player("Vittorio Grimaldi", atk_elo=1000)
    )
    player_list.append(
        Player("Ciro Pentangelo", def_elo=1000)
    )

    first_team = Team(player_list[0], player_list[1])
    second_team = Team(player_list[2], player_list[3])
    
    sample_match = Match(first_team, second_team)
    sample_match.resolve_match(8, 0)
    for p in player_list:
        ic(p.elo(Role.ATK))
        ic(p.elo(Role.DEF))