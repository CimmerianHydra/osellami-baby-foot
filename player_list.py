from OFB import *
import pickle as pk

class PlayerList:
    
    PLAYER_LIST_PATH = r'player_list.bin'
    DATA:list[Player] = []
    
    def __init__(self) -> None:
        self.load_file()

    def load_file(self):
        with open(self.PLAYER_LIST_PATH, 'rb') as f:
            self.DATA = pk.load(f)

    def save_file(self):
        with open(self.PLAYER_LIST_PATH, 'wb') as f:
            pk.dump(self.DATA, f)
    
    def erase_list(self):
        self.DATA = []
    
    def search_by_name(self, name:str):
        found = None
        for p in self.DATA:
            if p.name == name:
                found = p
        return found

    def add_new_player(self, name:str):
        new_player = Player(name)    
        if not self.search_by_name(name):
            self.DATA.append(new_player)
    
    def resolve_match(self, team_1, team_2, score_1, score_2):
        new_match = Match(team_1, team_2)
        new_match.resolve_match(score_1, score_2)
    
    def leaderboard(self, role:Role):
        sorted_list = sorted(self.DATA.copy(), key=lambda x: -1*x.elo(role))
        return sorted_list