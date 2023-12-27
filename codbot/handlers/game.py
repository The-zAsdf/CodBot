from .orderedset import OrderedSet
import random


DEFAULT_LOBBY_SIZE = 10

MAPS = {
    'Strike': 'mp_strike',
    'Crash': 'mp_crash',
    'Backlot': 'mp_backlot',
    'Crossfire': 'mp_crossfire',
    'Vacant': 'mp_vacant',
    'Shipment': 'mp_shipment',
    'Killhouse': 'mp_killhouse',
}

GAMEMODES = {
    'SnD': 'war',
    'TDM': 'dm',
    'FFA': 'dm'
}

class Game:
    def __init__(self, author, loc:str=None, gamemode:str=None, capacity:int=DEFAULT_LOBBY_SIZE):
        self.loc = self.set_loc(loc)
        self.gamemode = self.set_gamemode(gamemode)
        self.author = author
        self.capacity = capacity
        self.lobby = OrderedSet()
        self.busy = False
        self.add_player(author)

    def is_full(self):
        return len(self.lobby) >= self.capacity
    
    def player_in_lobby(self, player):
        return player in self.lobby
    
    def add_player(self, player):
        self.lobby.add(player)

    def remove_player(self, player):
        self.lobby.remove(player)

    def clear_queue(self):
        self.lobby = set()

    def get_players(self):
        return list(self.lobby)

    def __len__(self):
        return len(self.lobby)
    
    def __getitem__(self, player):
        return self.lobby[player]

    def set_loc(self, loc:str):
        if loc == None:
            return random.choice(list(MAPS.keys()))
        elif loc in MAPS:
            return loc
        else:
            logger.info(f'Invalid map: {loc}')
            return

    def set_gamemode(self, gamemode:str):
        if gamemode == None:
            return 'TDM'
        elif gamemode in MAPS:
            return gamemode
        else:
            logger.info(f'Invalid gamemode: {gamemode}')
            return