# CodBot
A Discord bot used to create public matches for CoD4 PC

# Requirements
Contact me if these links are outdated.
1. Follow the [guide](https://cod4x.ovh/t/how-to-create-a-server-linux-guide/3116)
2. For the prerequisites, check see [compiling the CoD4 server](https://github.com/callofduty4x/CoD4x_Server?tab=readme-ov-file#compiling-on-linux) for your OS.

# TODO:
- Writeup how to install the cod4 server part correctly.
- Server handler needs to asynchronously deal with multiple servers and their IO.
- Mods, default configs, and connect the discord bot to the server handler.
- Ensure running multiple servers work correctly. Is it even possible to host multiple servers through same IP? Just change socket? Figure it out.
- Read up on hooking an executable to discord for users. Want to 'auto-connect' players to the match.