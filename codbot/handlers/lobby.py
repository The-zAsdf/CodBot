import discord
from discord import app_commands
from discord.ext import commands
import collections
import logging
from queue import Queue
import random
import asyncio

logger = logging.getLogger("lobby")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

DEFAULT_LOBBY_SIZE = 10
DEFAULT_COLOR = discord.Colour.from_rgb(79,121,66)
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

async def setup(bot):
    await bot.add_cog(Lobby(bot))

class Lobby(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.capacity = DEFAULT_LOBBY_SIZE
        self.lobby = set()
        self.game = None
        self.busy = False

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

    @commands.command(name = "queue", aliases = ['q'], description = "Join the queue")
    async def add_to_queue(self, ctx):
        player = ctx.message.author

        if player in self.lobby:
            await ctx.send(f'{player.display_name} is already in the queue!')
            return
        elif self.is_full():
            await ctx.send(f'{player.display_name} cannot join the queue because it is full!')
            return
        self.lobby.add(player)
        await ctx.send("{} added to queue. ({:d}/{:d})".format(player.display_name, len(self.lobby), self.capacity))
        if self.is_full():
            ctx.send("Queue is now full!")

    @commands.command(name="dequeue", aliases=["dq"], description="Remove yourself from the queue")
    async def dq(self, ctx):
        player = ctx.message.author

        if player in self.lobby:
            self.lobby.remove(player)
            await ctx.send(
                f"{player.display_name} removed from queue. ({len(self.lobby):d}/{self.capacity:d})")
        else:
            await ctx.send(f"{player.display_name} is not in queue.")

    # Create a embedded message, buttons to join/leave queue, update dynamically.
    @commands.command(name = 'mixme', aliases = ['mm'], description = 'test mixme')
    async def mixme(self, ctx):
        self.game = Game()
        embed = discord.Embed(
            title = f'{self.game.gamemode} on {self.game.loc}',
            description = f'{len(self.lobby):d}/{self.capacity:d}',
            colour = DEFAULT_COLOR
        )
        view = testView(ctx.author, self, self.game, timeout = None)
        embed.set_footer(text='Made by zAsdf')
        await ctx.send(embed = embed, view = view)
        await view.wait()


    @app_commands.command(name = 'test')
    @app_commands.choices(loc = [
        app_commands.Choice(name='strike', value = 0),
        app_commands.Choice(name='crash', value = 1),
        app_commands.Choice(name='backlot', value = 2)
    ])
    @app_commands.choices(gamemode = [
        app_commands.Choice(name = 'SnD',value = 0), 
        app_commands.Choice(name = 'TDM',value = 1), 
        app_commands.Choice(name = 'FFA',value = 2)
    ])
    async def test(self, interaction: discord.Interaction, loc: app_commands.Choice[int], gamemode: app_commands.Choice[int]):
        await interaction.response.send_message(f'Hey {interaction.user.name}, you chose {loc.name} and {gamemode.name}')

    @commands.Cog.listener()
    async def on_ready(self):
        print('Lobby cog loaded')

class Game:
    def __init__(self, loc:str=None, gamemode:str=None):
        self.loc = self.set_loc(loc)
        self.gamemode = self.set_gamemode(gamemode)

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
    

class testView(discord.ui.View):
    def __init__(self, author, lobby, game, timeout:float=None):
        super().__init__(timeout = timeout)
        self.author = author
        self.lobby = lobby
        self.game = game
        self.last_removed = None

    async def disable_all_items(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view = self)

    async def on_timeout(self):
        await self.message.channel.send('Timed out!')
        await self.disable_all_items()

    async def update_description(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        embed.description = f'{len(self.lobby):d}/{self.lobby.capacity:d}'
        players = self.lobby.get_players()
        midpoint = len(players) // 2 + len(players) % 2
        embed.clear_fields()
        embed.add_field(name = 'Players', value = '\n'.join(player.display_name for player in players[:midpoint]), inline = True)
        embed.add_field(name = '\u200b', value = '\n'.join(player.display_name for player in players[midpoint:]), inline = True)
        await interaction.response.edit_message(embed = embed)

    @discord.ui.button(label = 'Join', style = discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button,):
        player = interaction.user

        if self.lobby.player_in_lobby(player):
            await interaction.response.send_message(f'{player} is already in the queue!')
            return
        elif self.lobby.is_full():
            await interaction.response.send_message(f'{player} cannot join the queue because it is full!')
            return
        self.lobby.add_player(player)
        if self.lobby.is_full():
            interaction.response.send_message("Queue is now full!")

        await self.update_description(interaction)

    @discord.ui.button(label = 'Leave', style = discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button,):
        player = interaction.user

        if self.lobby.player_in_lobby(player):
            self.lobby.remove_player(player)
            await self.update_description(interaction)
        else:
            await interaction.response.send_message(f"{player} is not in queue.")

    
    @discord.ui.button(label = 'Change Map', style = discord.ButtonStyle.blurple)
    async def change_map(self, interaction: discord.Interaction, button: discord.ui.Button,):
        # Only useable by author
        if interaction.user != self.author:
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
        if interaction.user != self.author:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
            return
        
        # Disable change gamemode button and add dropdown
        self.last_removed = button
        self.remove_item(button)
        self.add_item(GamemodeDropdown(self))
        await interaction.response.edit_message(view = self)
        # The callback will handle the rest

class MapDropdown(discord.ui.Select):
    def __init__(self, view: testView):
        self.viewTemp = view
        options = [discord.SelectOption(label = map) for map in MAPS]

        super().__init__(placeholder = 'Select a map', 
                         min_values = 1, 
                         max_values = 1, 
                         options = options
                         )
        
    async def callback(self, interaction: discord.Interaction):
        if self.viewTemp.author != interaction.user:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
        else:
            # Update game object
            self.viewTemp.game.loc = self.values[0]
            # Update embed title
            embed = interaction.message.embeds[0]
            embed.title = f'{self.viewTemp.game.gamemode} on {self.viewTemp.game.loc}'
            # Remove dropdown
            self.viewTemp.remove_item(self)
            # Re-enable change map button
            self.viewTemp.add_item(self.viewTemp.last_removed)
            self.viewTemp.last_removed = None
            await interaction.response.edit_message(embed = embed, view = self.viewTemp)

class GamemodeDropdown(discord.ui.Select):
    def __init__(self, view: testView):
        self.viewTemp = view
        options = [discord.SelectOption(label = gamemode) for gamemode in GAMEMODES]

        super().__init__(placeholder = 'Select a gamemode', 
                         min_values = 1, 
                         max_values = 1, 
                         options = options
                         )
    
    async def callback(self, interaction: discord.Interaction):
        if self.viewTemp.author != interaction.user:
            await interaction.response.send_message(f'{interaction.user} stop touching my buttons.')
        else:
            # Update game object
            self.viewTemp.game.gamemode = self.values[0]
            # Update embed title
            embed = interaction.message.embeds[0]
            embed.title = f'{self.viewTemp.game.gamemode} on {self.viewTemp.game.loc}'
            # Remove dropdown
            self.viewTemp.remove_item(self)
            # Re-enable change gamemode button
            self.viewTemp.add_item(self.viewTemp.last_removed)
            self.viewTemp.last_removed = None
            await interaction.response.edit_message(embed = embed, view = self.viewTemp)
        
        
