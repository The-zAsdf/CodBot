# This script will handle both the creation of the cod4 server
# and the cog that will handle the server commands which will be
# referred to as the 'host' and 'cog' respectively.

# The host will serve as the interaction from cod4 dedicated server
# to the cog. The cog is used by the discord users to interact with the server

# Github copilot autocompleted this link: https://www.youtube.com/watch?v=8Q0zNpZlXj8
# It does nothing and I found that hilarious. Who reads comments anyway?

from subprocess import PIPE, STDOUT
import os
import asyncio
from .game import Game, MAPS, GAMEMODES
from .config import Config

# TODO:
# - Figure out how to handle multiple servers (async start,stop,IO)
# - RCON must also be setup appropriately.
# - tutorial on how to install the dedicated server for anyone using CodBot
# - What does status do in dedicated server?

#### Host ####
EXECUTABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server/cod4x18_dedrun")
LOCAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server/")

# TODO:
# - Configure default server config (kinda done; need to make more prog on other stuff)
# - Flesh out startup commands for host 

# COMMANDS:
# - map: map
# - gamemode: g_gametype/gametype
# - lobby size: sv_maxclients
# - promod specfic commands based on gamemode
#     - class limits unlocked for tdm, ffa
#     - class limits for snd


class Host:
    cod_token = Config().cod_token
    process = None
    busy = False
    output_queue = asyncio.Queue()
    input_queue = asyncio.Queue()

    def __init__(self, game:Game, print_output = True, command_line_input = True):
        self.game = game
        self.busy = True
        self.print_output = print_output
        self.command_line_input = command_line_input

    def parse_game(self):
        args = {
            '+set sv_authtoken': self.cod_token,
            '+set sv_maxclients': self.game.capacity,
            '+set fs_game': 'mods/pml220', # This should be in config, but it doesn't seem to work. Fix pls.
            '+exec': 'server.cfg',
            '+set g_gametype': GAMEMODES[self.game.gamemode],
            'map': MAPS[self.game.loc],
        }
        temp =  [f"{k} {v}" for k,v in args.items()]
        return [arg for q in temp for arg in q.split(' ')]


    async def start(self):
        self.process = await asyncio.create_subprocess_exec(
            # EXECUTABLE,
            *[EXECUTABLE, *self.parse_game()],
            stdout=PIPE,
            stdin = PIPE,
            stderr= STDOUT, 
            cwd = LOCAL_DIR,
        )

        runs = [self.read_stdout, self.execute_input]
        if self.command_line_input:
            runs.append(self.read_stdin)

        await asyncio.gather(*[f() for f in runs])


    def exit(self):
        self.busy = False
        
    async def write_input(self, command:str):
        print(command.strip())
        await self.input_queue.put(command.strip())

    async def read_stdin(self):
        while True:
            line = await asyncio.to_thread(input)
            await self.input_queue.put(line+"\n")

    async def execute_input(self):
        while True:
            line = await self.input_queue.get()
            line = line.encode()
            self.process.stdin.write(line)
            

    # Function to asynchronously read stdout of the process
    async def read_stdout(self) -> None:
        while True:
            line = await self.process.stdout.readline()
            if line:
                print(line.decode().strip())
                await self.output_queue.put(line.decode().strip()) # output queue can be used to parse cod4 server
        
    


#### Cog ####
                
# TODO:
# - Lay out the foundation on how the cog will interact with the host
        

#### main (testing/sandbox) ####
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    game = Game(None)
    host = Host(game)
    asyncio.run(host.start())
    loop.run_forever()
    loop.close()
    # while True:
    #     time.sleep(3)
    #     host.write_input("status")
    

    