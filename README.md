# CodBot
A Discord bot used to create public matches for CoD4 PC

# Requirements:
Contact me if these links are outdated.
1. Follow the [guide](https://cod4x.ovh/t/how-to-create-a-server-linux-guide/3116)
2. For the prerequisites, check see [compiling the CoD4 server](https://github.com/callofduty4x/CoD4x_Server?tab=readme-ov-file#compiling-on-linux) for your OS.

# TODO:
- Write up how to install the cod4 server part correctly.
- Write up on how to setup config.ini correctly.
- ~~Server handler needs to asynchronously deal with multiple servers and their IO.~~
- Mods, default configs, and connect the discord bot to the server handler.
- Ensure running multiple servers work correctly.
- ~~Auto-connect players to the match via discord embedded message~~
- Allow host user to change map of server through discord

# Future implementation:
- Codbot & servers will run independently and interact via sockets. This allows for the codbot to go down and servers to stay up until codbot restarts/reconnects.
- Create private server for 5v5 SnD `competition` setup.

# Current (or untested) problems:
- No handling/reconnection for codbot to public server. Just use UDP and hope for the best
- If codbot errors, then all servers need to go down and restart
- Codbot can error through interactions.
