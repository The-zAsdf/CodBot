import discord
from discord import app_commands
from discord.ext import commands

async def setup(bot):
    await bot.add_cog(Temp(bot))

class Temp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.str = "Hello World!"

    @commands.Cog.listener()
    async def on_ready(self):
        print('Temp cog loaded')

    # @commands.command(name = "sync", description = 'sync')
    # async def sync(self, ctx) -> None:
    #     fmt = await ctx.bot.tree.sync(guild=ctx.guild)
    #     await ctx.send(f'Synced {len(fmt)} commands')

    @commands.command(name = "change_string",aliases=['cs'], description= 'test change string')
    async def change_string(self, ctx, buf:str):
        self.str = buf
        await ctx.send(f'New string: {self.str}')

    @commands.command(name = "print_string",aliases=['ps'], description= 'test print string')
    async def print_string(self, ctx):
        await ctx.send(self.str)

    @app_commands.command()
    async def hello(self,interaction: discord.Interaction):
        await interaction.response.send_message(f'Hey {interaction.user.name}!',ephemeral=True)