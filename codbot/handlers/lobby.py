import discord
from discord import app_commands
from discord.ext import commands
import collections
import logging
import asyncio
# import random
# from .orderedset import OrderedSet
import os
from .server import Host
from .game import Game, MAPS, GAMEMODES

# TODO:
# - Set capacity
# - !help in bot.py
# - What happens when game is starting?

logger = logging.getLogger("lobby")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


DEFAULT_COLOR = discord.Colour.from_rgb(79,121,66)

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
        players = self.instances[player].get_players() # This feels pointless. Currently a safety net.
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

        self.host = Host(self.game) # The view has the Host object. Might need to change this later?
        
        
        # Change buttons for server specific stuff? (map, gamemode, lobby size)
        # Update embed description

        await asyncio.gather(
            self.host.start(),
            self.start_game(interaction)
        )
        # await self.host.start()
        # await self.start_game(interaction)

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
        
        
