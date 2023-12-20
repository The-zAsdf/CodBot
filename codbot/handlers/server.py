# This script will handle both the creation of the cod4 server
# and the cog that will handle the server commands which will be
# referred to as the 'host' and 'cog' respectively.

# The host will serve as the interaction from cod4 dedicated server
# to the cog. The cog is used by the discord userst to interact with the server
# In conjunction, RCON must also be setup appropriately.

# This comment is a reminder on a tutorial how to install the dedicated server
# for anyone using CodBot.

# Github copilot autocompleted this link: https://www.youtube.com/watch?v=8Q0zNpZlXj8
# It does nothing and I found that hilarious. Who reads comments anyway?

import discord
from subprocess import Popen, PIPE, STDOUT
import os
import asyncio

# TODO:
# - Figure out how to handle multiple servers (async start,stop,IO)

#### Host ####
EXECUTABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server/cod4x18_dedrun")
LOCAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server/")

# TODO:
# - Mods
# - Configure default server config
# - Flesh out startup commands for host

class Host:
    process = None
    busy = False

    def __init__(self, **kwargs):
        self.busy = True
        self.start()

    def start(self):
        self.process = Popen(
            [EXECUTABLE],
            stdout=PIPE,
            stdin = PIPE,
            stderr= STDOUT, 
            # If stderr is PIPE then it breaks. I don't know why.
            # Errors are now thrown into stdout with weird formatting. 
            # Would be nice to fix this some time
            universal_newlines=True,
            text = True,
            cwd = LOCAL_DIR,
        )

    def exit(self):
        self.process.terminate()
        self.busy = False
        
    def pass_command(self,command:str):
        stdout, stderr = self.process.communicate(input=command) # maybe +"\n"?
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

    async def read_output(self):
        while True:
            if self.process.poll() is not None:
                break
            line = self.process.stdout.readline()
            if line:
                print(line.strip())
        
    


#### Cog ####
                
# TODO:
# - Lay out the foundation on how the cog will interact with the host
        

#### main (testing/sandbox) ####
if __name__ == "__main__":
    host = Host()
    try:
        asyncio.run(host.read_output())
    finally:
        host.exit()

    