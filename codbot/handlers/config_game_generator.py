import shutil
from .game import Game, MAPS, GAMEMODES
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server/main/")

TDM_MAPROTATION = [
    'gametype war map mp_backlot',
    'gametype war map mp_citystreets',
    'gametype war map mp_crash',
    'gametype war map mp_crossfire',
    'gametype war map mp_strike',
    'gametype war map mp_killhouse',
]

FFA_MAPROTATION = [
    'gametype war map mp_backlot',
    'gametype war map mp_citystreets',
    'gametype war map mp_crash',
    'gametype war map mp_strike',
    'gametype war map mp_killhouse',
    'gametype war map mp_shipment',
    'gametype war map mp_crossfire',
]

SND_MAPROTATION = [
    'gametype war map mp_backlot',
    'gametype war map mp_citystreets',
    'gametype war map mp_crash',
    'gametype war map mp_crossfire',
    'gametype war map mp_strike',
]

PROMOD_TDM_SETTINGS = [
    'set class_sniper_limit 99',
    'set class_specops_limit 99',
    'set class_demolitions_limit 99',
    'set class_assault_limit 99',
    'set weap_allow_flash_gerande 0',
    'set weap_allow_smoke_grenade 0',
    'set weap_allow_frag_grenade 0',
]

PROMOD_SNIPER_SETTINGS = [
    'set class_sniper_limit 99',
    'set class_specops_limit 0',
    'set class_demolitions_limit 0',
    'set class_assault_limit 0',
    'set weap_allow_flash_gerande 0',
    'set weap_allow_smoke_grenade 0',
    'set weap_allow_frag_grenade 0',
    'set weap_allow_beretta 0',
    'set weap_allow_colt45 0',
    'set weap_allow_deserteagle 0',
    'set weap_allow_deserteaglegold 0',
    'set class_sniper_primary "m40a3"',
    'set class_sniper_secondary "remington700"',
]

PROMOD_SND_SETTINGS = [
    'set class_sniper_limit 2',
    'set class_specops_limit 4',
    'set class_demolitions_limit 2',
    'set class_assault_limit 99',
    'set weap_allow_flash_gerande 1',
    'set weap_allow_smoke_grenade 1',
    'set weap_allow_frag_grenade 1',
]

# No error handling has been done here
def parse_map_rotation(file, game:Game) -> None:
    if game.gamemode == 'TDM':
        rot = TDM_MAPROTATION
    elif game.gamemode == 'FFA':
        rot = FFA_MAPROTATION
    elif game.gamemode == 'SnD':
        rot = SND_MAPROTATION

    start = f'gametype {GAMEMODES[game.gamemode]} map {MAPS[game.loc]}'
    if start in rot:
        rot.remove(start)
    rot.insert(0, start)
    rot = ' '.join(rot)
    file.write(f'set sv_maprotation "{rot}"\n')
    file.write('set sv_randomMapRotation "0"\n')
    file.write('map_rotate\n')
    

def parse_promod_settings(file, game:Game, snipers_only = False) -> None:
    if snipers_only:
        file.write('\n'.join(PROMOD_SNIPER_SETTINGS))
    elif game.gamemode in ['TDM', 'FFA']:
        file.write('\n'.join(PROMOD_TDM_SETTINGS))
    elif game.gamemode == 'SnD':
        file.write('\n'.join(PROMOD_SND_SETTINGS))
    else:
        # This should never happen. Require error handling
        return

def generate_config(game:Game, snipers_only = False) -> str:
    shutil.copyfile(PATH + "server_template.cfg", PATH + f"server_{game.port}.cfg")
    template_file = open(PATH + f"server_{game.port}.cfg", "a")
    if snipers_only:
        template_file.write(f'set sv_hostname "CodBotZA - {game.gamemode} SNIPERS" \n')
    else:
        template_file.write(f'set sv_hostname "CodBotZA #{game.port%28960} - {game.gamemode}"\n')
    template_file.write(f'set fs_game "mods/pml220"\n')
    template_file.write(f'set g_password ""\n')
    template_file.write(f'set g_gametype "{GAMEMODES[game.gamemode]}"\n')
    template_file.write(f'map "{MAPS[game.loc]}"\n')
    template_file.write(f'set sv_maxclients "{game.capacity}"\n')

    parse_promod_settings(template_file, game, snipers_only)
    parse_map_rotation(template_file, game)
    return f'server_{game.port}.cfg'

    


