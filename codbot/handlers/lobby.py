import discord
from discord import app_commands
from discord.ext import commands, tasks
import collections
import logging
import asyncio
# import random
# from .orderedset import OrderedSet
import os
from .server import Host
from .game import Game, MAPS, GAMEMODES
import time
from datetime import datetime
from .magnet import shorten

# TODO:
# - Set capacity
# - !help in bot.py
# - What happens when game is starting?

logger = logging.getLogger("lobby")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


DEFAULT_COLOR = discord.Colour.from_rgb(79,121,66)
MIN_PORT = 28961
MAX_PORT = 28967

async def setup(bot):
    await bot.add_cog(Master(bot))

class LobbyManager():
    def __init__(self):
        self.instances = set()
    
    def add_instance(self, game):
        self.instances.add(game)

    def remove_instance(self, game):
        self.instances.remove(game)

    def is_player_in_instance(self, player):
        return any(player in game for game in self.instances)
    
    def get_game_from_author(self, user):
        return any(user == game.author for game in self.instances)
    
    def ports_in_use(self):
        return [game.port for game in self.instances]

class Master(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lobbies = LobbyManager()
        self.channel = self.set_channel()
        self.start_public_servers()


    def get_next_open_port(self):
        for port in range(MIN_PORT, MAX_PORT):
            if not self.is_port_in_use(port):
                return port
        return None

    def is_port_in_use(self, port):
        return port in self.lobbies.ports_in_use()
    
    def set_channel(self, id = 1201125288600412181):
        try:
            return self.bot.get_channel(id)
        except Exception as e:
            logger.error(f'Could not set channel: {e}')
            return None
        
    def start_public_servers(self):
        # 1. Find the channel and clear the messages.
        # 2. Create the public servers.
        # 3. If the channel is found, loop the parse_status from public server & send to channel.
        # 4. Loop the output_queue from public server & update message

        pub = Game(None, port = self.get_next_open_port(), gamemode='TDM', capacity=16)
        self.lobbies.add_instance(pub)
        host = Host(pub, print_output= True, status= True, ROQ = False,  cfg = 'server_tdm.cfg')
        view = PublicView(pub, host, self.lobbies, self.channel, timeout = None)
        asyncio.create_task(view.start())

        
    

    # How about creating a default embedded message template?

    # Create a embedded message, buttons to join/leave queue, update dynamically.
    @commands.command(name = 'mixme', aliases = ['mm'], description = 'test mixme')
    async def mixme(self, ctx):
        player = ctx.author
        if self.lobbies.is_player_in_instance(player):
            await ctx.send(f'{player} is already in a queue!')
            return
        port = self.get_next_open_port()
        if port == None:
            await ctx.send(f'No available servers. Try again later.')
            return
        newgame = Game(player,port)
        self.lobbies.add_instance(newgame)
        view = CustomView(newgame, self.lobbies, timeout = None)
        embed = discord.Embed(
            title = f'{newgame.gamemode} on {newgame.loc}',
            description = f'{len(newgame):d}/{newgame.capacity:d}',
            colour = DEFAULT_COLOR,
        )
        # image, name = self.bot.get_image(newgame.loc).values()
        # embed.set_thumbnail(url = f'attachment://{name}')
        # embed.set_footer(text='Made by zAsdf')
        players = newgame.get_players() # This feels pointless. Currently a safety net.
        midpoint = len(players) // 2 + len(players) % 2
        embed.clear_fields()
        embed.add_field(name = 'Players', value = '\n'.join(player.display_name for player in players[:midpoint]), inline = True)
        embed.add_field(name = '\u200b', value = '\n'.join(player.display_name for player in players[midpoint:]), inline = True)
        
        view.message = await ctx.send(embed = embed, view = view)
        # view.message = await ctx.send(file = image, embed = embed, view = view)
        await view.wait()


    @commands.Cog.listener()
    async def on_ready(self):
        print('Lobby cog loaded')
    

class PublicView(discord.ui.View):
    message = None

    def __init__(self, game, host, lobbymanager, channel, timeout:float=None):
        super().__init__(timeout = timeout)
        self.game = game
        self.lobbymanager = lobbymanager
        self.host = host
        self.channel = channel
        self.message = None

    async def start(self):
        if self.channel != None:
            await asyncio.gather(
                self.host.start(),
                self.update_status.start(),
            )
        else:
            await self.host.start()
        
    @tasks.loop(seconds = 5)
    async def update_status(self):
        # print('update_status: ', end = '')
        if self.message == None:
            # print('first message ', end = '')
            await asyncio.wait_for(self.channel.purge(), timeout= None)
            embed = discord.Embed(
                title = f'{self.game.gamemode} on {self.game.loc}',
                description = time.strftime('%b %d, %Y - %H:%M:%S'),
                colour = DEFAULT_COLOR,
            )
            players = []
            midpoint = len(players) // 2 + len(players) % 2
            embed.clear_fields()
            embed.add_field(name = f'Players: {len(self.game):d}/{self.game.capacity:d}', value = '\n'.join(player.display_name for player in players[:midpoint]), inline = True)
            embed.add_field(name = '\u200b', value = '\n'.join(player.display_name for player in players[midpoint:]), inline = True)
            embed.add_field(name = 'Join the game', value = f'[Click me](https://zoosd.asuscomm.com/{self.game.port}-link/)', inline = False)
            self.message = await self.channel.send(embed = embed, view = self)
            # print('(done)')
        else:
            # print('update message ', end = '')
            try:
                # print('(trying... ', end = '')
                serverinfo, playerinfo = await self.host.output_queue.get()
                map_name = serverinfo['map'][0]
                # gamemode does not exist in serverinfo (problem? Eh whatever)
                embed = discord.Embed(
                    title = f'{self.game.gamemode} on {map_name}',
                    description = time.strftime('%b %d, %Y - %H:%M:%S'),
                    colour = DEFAULT_COLOR,
                )
                players = playerinfo['name']
                midpoint = len(players) // 2 + len(players) % 2
                embed.clear_fields()
                embed.add_field(name = f'Players: {len(self.game):d}/{self.game.capacity:d}', value = '\n'.join(player.display_name for player in players[:midpoint]), inline = True)
                embed.add_field(name = '\u200b', value = '\n'.join(player.display_name for player in players[midpoint:]), inline = True)
                embed.add_field(name = 'Join the game!', value = f'[Click me](https://zoosd.asuscomm.com/{self.game.port}-link/)', inline = False)
                self.message = await self.message.edit(embed = embed, view = self)
                # print('done)')
            # except TimeoutError as e:
                # print('error)')
                # logger.error(f'Error in update_from_status: {e}')
                # print('missed)')
            except Exception as e:
                print('error)')
                logger.error(f'Error in update_from_status: {e}')

""" 
    Below lies the custom view for user created lobbies.
"""
class CustomView(discord.ui.View):
    """ The custom view for an embedded message representing a lobby in discord. """
    message = None

    def __init__(self, game, lobbymanager, timeout:float=None):
        super().__init__(timeout = timeout)
        self.game = game
        self.last_removed = None
        self.lobbymanager = lobbymanager
        

    def disable_all_items(self):
        for child in self.children:
            child.disabled = True

    def clear_all_items(self):
        for child in self.children:
            self.remove_item(child)

    def remove_all_players(self):
        for player in self.game.get_players():
            self.game.remove_player(player)

    async def on_timeout(self):
        self.clear_all_items()
        self.remove_all_players()
        embed = discord.Embed(
            title = f'{self.game.gamemode} on {self.game.loc}',
            description = 'Game cancelled: Queue has timed out.',
            colour = DEFAULT_COLOR
        )
        embed.set_footer(text='Made by zAsdf')
        self.lobbymanager.remove_instance(self.game)
        await self.message.edit(embed = embed, view = self)
        self.stop()


    async def cancel_game(self, interaction: discord.Interaction):
        self.clear_all_items()
        self.remove_all_players()
        embed = interaction.message.embeds[0]
        embed.description = 'Game cancelled: No players left in queue.'
        embed.clear_fields()
        self.lobbymanager.remove_instance(self.game)
        await interaction.response.edit_message(embed = embed,view = self)
        self.stop()

    async def start_game(self, interaction: discord.Interaction):
        self.disable_all_items() # Maybe not disable the game? Testing phase.
        self.game.busy = True
        await interaction.response.edit_message(view = self)

    async def update_description(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = f'{len(self.game):d}/{self.game.capacity:d}'
        players = self.game.get_players()
        midpoint = len(players) // 2 + len(players) % 2
        embed.clear_fields()
        embed.add_field(name = 'Players', value = '\n'.join(player.display_name for player in players[:midpoint]), inline = True)
        embed.add_field(name = '\u200b', value = '\n'.join(player.display_name for player in players[midpoint:]), inline = True)
        await interaction.response.edit_message(embed = embed)

    @discord.ui.button(label = 'Join', style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button,):
        player = interaction.user

        if self.lobbymanager.is_player_in_instance(player):
            await interaction.response.send_message(f'{player} is already in a queue!')
            return
        elif self.game.is_full():
            await interaction.response.send_message(f'{player} cannot join the queue because it is full!')
            return
        self.game.add_player(player)
        if self.game.is_full():
            interaction.response.send_message("Queue is now full!")

        await self.update_description(interaction)

    @discord.ui.button(label = 'Leave', style = discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button,):
        player = interaction.user

        if self.game.player_in_lobby(player):
            self.game.remove_player(player)
            if len(self.game) == 0:
                await self.cancel_game(interaction)
            else:
                await self.update_description(interaction)
        else:
            await interaction.response.send_message(f"{player} is not in queue.")

    
    @discord.ui.button(label = 'Change Map', style = discord.ButtonStyle.blurple)
    async def change_map(self, interaction: discord.Interaction, button: discord.ui.Button,):
        # Only useable by author
        if interaction.user != self.game.author:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
            return
        
        # Disable change map button and add dropdown
        self.last_removed = button
        self.remove_item(button)
        self.add_item(MapDropdown(self))
        await interaction.response.edit_message(view = self)
        # The callback will handle the rest

    @discord.ui.button(label = 'Change Gamemode', style = discord.ButtonStyle.blurple)
    async def change_gamemode(self, interaction: discord.Interaction, button: discord.ui.Button,):
        # Only useable by author
        if interaction.user != self.game.author:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
            return
        
        # Disable change gamemode button and add dropdown
        self.last_removed = button
        self.remove_item(button)
        self.add_item(GamemodeDropdown(self))
        await interaction.response.edit_message(view = self)
        # The callback will handle the rest

    @discord.ui.button(label = 'Start', style = discord.ButtonStyle.green)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button,):
        # Only useable by author
        if interaction.user != self.game.author:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
            return

        self.host = Host(self.game, print_output= False, status= True, ROQ = False) # The view has the Host object. Might need to change this later?
        
        
        # Change buttons for server specific stuff? (map, gamemode, lobby size)
        # Update embed description

        await asyncio.gather(
            self.host.start(),
            self.start_game(interaction)
        )
        # await self.host.start()
        # await self.start_game(interaction)

class MapDropdown(discord.ui.Select):
    """
    A custom dropdown menu for selecting a map.
    """
    def __init__(self, view: CustomView):
        self.view = view
        options = [discord.SelectOption(label = map) for map in MAPS]

        super().__init__(placeholder = 'Select a map', 
                         min_values = 1, 
                         max_values = 1, 
                         options = options
                         )
        
    async def callback(self, interaction: discord.Interaction):
        if self.view.game.author != interaction.user:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
        else:
            # Update game object
            self.view.game.loc = self.values[0]
            # Update embed title
            embed = interaction.message.embeds[0]
            embed.title = f'{self.view.game.gamemode} on {self.view.game.loc}'
            # Remove dropdown
            self.view.remove_item(self)
            # Re-enable change map button
            self.view.add_item(self.view.last_removed)
            self.view.last_removed = None
            await interaction.response.edit_message(embed = embed, view = self.view)

class GamemodeDropdown(discord.ui.Select):
    """
    A custom dropdown menu for selecting a gamemode.
    """

    def __init__(self, view: CustomView):
        self.view = view
        options = [discord.SelectOption(label=gamemode) for gamemode in GAMEMODES]

        super().__init__(
            placeholder='Select a gamemode',
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.view.game.author != interaction.user:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
        else:
            # Update game object
            self.view.game.gamemode = self.values[0]
            # Update embed title
            embed = interaction.message.embeds[0]
            embed.title = f'{self.view.game.gamemode} on {self.view.game.loc}'
            # Remove dropdown
            self.view.remove_item(self)
            # Re-enable change gamemode button
            self.view.add_item(self.view.last_removed)
            self.view.last_removed = None
            await interaction.response.edit_message(embed=embed, view=self.view)
        
        
