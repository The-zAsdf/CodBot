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
import socket
import time
import asyncio_dgram
import re
from pandas import DataFrame
from .config_game_generator import generate_config

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

def get_ip(remote_server="google.com"):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((remote_server, 80))
        return s.getsockname()[0]

# def get_ip():
    # return 'zoosd.asuscomm.com'
    # return '192.168.50.130'


class Host:
    cod_token = Config().cod_token
    rcon_token = Config().rcon_token
    process = None
    busy = False
    output_queue = asyncio.Queue()
    input_queue = asyncio.Queue()

    def __init__(self, game:Game, print_output = False, status = False, ROQ = False, cfg = 'server_tdm.cfg'):
        self.game = game
        self.game.busy = True
        self.print_output = print_output
        self.status = status
        self.ROQ = ROQ
        self.ip = get_ip()
        self.cfg = generate_config(game)
        print(self.cfg)

    def parse_game(self):
        args = {
            '+set sv_authtoken': self.cod_token,
            '+set rcon_password': self.rcon_token,
            '+set sv_maxclients': self.game.capacity,
            '+set net_port': self.game.port,
            '+set net_ip': self.ip,
            '+exec': self.cfg,
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
        
        if True:
            await asyncio.sleep(1) # Wait for server to start
            self.stream = await asyncio_dgram.connect((self.ip, self.game.port))


        runs = []
        if self.print_output:
            runs.append(self.read_stdout)
        if self.status:
            runs.append(self.ping_status)
            runs.append(self.perma_parse_status)
            if self.ROQ:
                runs.append(self.read_output_queue)
        


        await asyncio.gather(*[f() for f in runs])


    async def restart_server(self):
        await asyncio.sleep(5)
        await self.pass_command('restart')

    async def sandbox(self):
        command = 'systeminfo'
        rcon_password = self.rcon_token.encode("utf-8")
        packet = b'\xFF\xFF\xFF\xFFrcon ' + rcon_password + b' ' + command.encode("utf-8")
        try:
            await self.stream.send(packet)
            data, _ = await self.stream.recv()
            response = data.decode("utf-8", errors="ignore")
            print()
            print()
            print(response)
            print()
            print()
            return response
        
        except InterruptedError as e:
            print(e)
            print('Failed to send command.')
            return None

    # Parse the status response from server
    def parse_status(self, response):
        serverinfo = {}
        playerinfo = []
        serverinfo['time'] = time.time()
        response_lines = response.split('\n')
        for line in response_lines[1:7]:
            subline = line.split(':')
            subline = [x.strip() for x in subline]
            serverinfo[subline[0]] = subline[1]

        header = re.split(r'\s+',response_lines[8].strip())[:6]
        
        for line in response_lines[10:]:
            line = re.split(r'\s+',line[:86].strip())
            if len(line) == 6:
                playerinfo.append(line)

        df = DataFrame(playerinfo, columns=header)
        return DataFrame(serverinfo, index = [0]), df # serverinfo, playerinfo
    
    # Constantly waits for response from server, parses it and puts it in output queue
    async def perma_parse_status(self):
        while True:
            data, _ = await self.stream.recv()
            response = data.decode("utf-8", errors="ignore")
            serverinfo, playerinfo = await asyncio.to_thread(self.parse_status, response)
            await self.output_queue.put((serverinfo, playerinfo))
    
    # Printing output queue
    async def read_output_queue(self):
        while True:
            line = await self.output_queue.get()
            print(line)
            print()

    # Constantly pings server via UDP for status
    async def ping_status(self, interval = 5):
        rcon_password = self.rcon_token.encode("utf-8")
        rcon_command = 'status'.encode("utf-8")
        packet = b'\xFF\xFF\xFF\xFFrcon ' + rcon_password + b' ' + rcon_command
        while True:
            try:
                await asyncio.sleep(interval)
                await self.stream.send(packet)

            except InterruptedError as e:
                print(e)
                print('status fetching failed.')
        


    def exit(self):
        self.busy = False
        
    async def pass_command(self, command:str):
        rcon_password = self.rcon_token.encode("utf-8")
        packet = b'\xFF\xFF\xFF\xFFrcon ' + rcon_password + b' ' + command.encode("utf-8")
        try:
            await self.stream.send(packet)
            data, _ = await self.stream.recv()
            response = data.decode("utf-8", errors="ignore")
            return response
        
        except InterruptedError as e:
            print(e)
            print('Failed to send command.')
            return None

    # Function to asynchronously read stdout of the process
    async def read_stdout(self) -> None:
        while True:
            line = await self.process.stdout.readline()
            if line:
                print(line.decode().strip())
                # await self.output_queue.put(line.decode().strip()) # output queue can be used to parse cod4 server
        
    


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
    

    