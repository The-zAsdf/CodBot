import discord
from discord import app_commands
from discord.ext import commands
import collections
from queue import Queue

DEFAULT_LOBBY_SIZE = 10


# First objective:
#  - Create a singular master lobby

# Second objective:
#  - Create multiple instances of lobbies tied to message ID or something

# Third objective:
#  - Connect dedicated server to lobby through async scripts

async def setup(bot):
    await bot.add_cog(Lobby(bot))

class Lobby(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.capacity = DEFAULT_LOBBY_SIZE
        self.lobby = set()

    def is_full(self):
        return len(self.lobby) >= self.capacity

    def clear_queue(self):
        self.lobby = set()

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
        embed = discord.Embed(
            title = 'Mixme',
            description = 'Mixme',
            colour = discord.Colour.from_rgb(79,121,66)
        )
        embed.set_footer(text='Made by zAsdf')
        await ctx.send(embed = embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print('Lobby cog loaded')
