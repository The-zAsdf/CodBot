# Skeleton for codbot
import logging
import sys
import traceback
from config.config import Config
from discord.ext import commands
import discord

description = 'test123'

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

extensions = ['handlers.sandbox', 'handlers.lobby']


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)
        self.synced = False

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        await self.load_extensions()

        if not self.synced:
            fmt = await self.tree.sync()
            print(f'Synced {len(fmt)} commands')
            self.synced = True

    @commands.command(name = "sync", description = 'sync')
    async def sync(self, ctx) -> None:
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f'Synced {len(fmt)} commands')

    async def load_extensions(self):
        loaded_extensions = []
        failed_extensions = []

        for extension in extensions:
            try:
                await self.load_extension(extension)
            except ImportError:
                failed_extensions.append((extension, traceback.format_exc()))
            else:
                loaded_extensions.append(extension)

        print(f'LOADED: {loaded_extensions}')
        print(f'FAILED: {failed_extensions}')



def start():
    config = Config()
    if not config.discord_token:
        logger.error("Please enter your Discord bot account token in config.ini")
        sys.exit()

    bot = Bot(command_prefix = '!', description=description, intents = intents)
    bot.run(config.discord_token)

if __name__ == '__main__':
    start()



