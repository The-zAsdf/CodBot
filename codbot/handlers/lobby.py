import discord
from discord import app_commands
from discord.ext import commands
import collections
import logging
import random
from .orderedset import OrderedSet
import os

# TODO:
# - Set capacity
# - !help in bot.py
# - What happens when game is starting?

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
        self.instances = collections.defaultdict(Game)
        self.instances.default_factory = lambda: None

    def add_instance(self, player, game):
        self.instances[player] = game

    def remove_instance(self, player):
        self.instances.pop(player)

    # Before creating a new instance, check if player is already in one.
    def is_player_in_instance(self, player):
        return any(player in game for game in self.instances.values())
    
    def __getitem__(self, player):
        return self.instances[player]
        

    # How about creating a default embedded message template?

    # Create a embedded message, buttons to join/leave queue, update dynamically.
    @commands.command(name = 'mixme', aliases = ['mm'], description = 'test mixme')
    async def mixme(self, ctx):
        player = ctx.author
        if self.is_player_in_instance(player):
            await ctx.send(f'{player} is already in a queue!')
            return
        self.add_instance(player, Game(player))
        view = CustomView(self.instances[player], timeout = None)
        embed = discord.Embed(
            title = f'{self.instances[player].gamemode} on {self.instances[player].loc}',
            description = f'{len(self.instances[player]):d}/{self.instances[player].capacity:d}',
            colour = DEFAULT_COLOR,
        )
        # image, name = self.bot.get_image(self.instances[player].loc).values()
        # embed.set_thumbnail(url = f'attachment://{name}')
        # embed.set_footer(text='Made by zAsdf')
        players = self.instances[player].get_players() # This feels pointless
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
    
class CustomView(discord.ui.View):
    message = None

    def __init__(self, game, timeout:float=None):
        super().__init__(timeout = timeout)
        self.game = game
        self.last_removed = None
        

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
        await self.message.edit(embed = embed, view = self)
        self.stop()


    async def cancel_game(self, interaction: discord.Interaction):
        self.clear_all_items()
        self.remove_all_players()
        embed = interaction.message.embeds[0]
        embed.description = 'Game cancelled: No players left in queue.'
        embed.clear_fields()
        await interaction.response.edit_message(embed = embed,view = self)
        self.stop()

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

        if self.game.player_in_lobby(player):
            await interaction.response.send_message(f'{player} is already in the queue!')
            return
        elif self.game.is_full():
            await interaction.response.send_message(f'{player} cannot join the queue because it is full!')
            return
        self.game.add_player(player)
        if self.game.is_full():
            interaction.response.send_message("Queue is now full!")

        await self.update_description(interaction)

    # If there are zero people in lobby, cancel game
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

class MapDropdown(discord.ui.Select):
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
    def __init__(self, view: CustomView):
        self.view = view
        options = [discord.SelectOption(label = gamemode) for gamemode in GAMEMODES]

        super().__init__(placeholder = 'Select a gamemode', 
                         min_values = 1, 
                         max_values = 1, 
                         options = options
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
            await interaction.response.edit_message(embed = embed, view = self.view)
        
        
