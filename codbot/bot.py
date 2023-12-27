# Skeleton for codbot
import logging
import sys
import traceback
from handlers.config import Config
from discord.ext import commands
import discord
import os

RESOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/")

description = 'test123'

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

extensions = ['handlers.lobby']


class Bot(commands.Bot):
    image_dict = {}

    def __init__(self, *args, **kwargs):
        super(Bot, self).__init__(*args, **kwargs)
        self.synced = False

    # Maybe do this over. Used for loading images.
    def get_resources(self):
        if not os.path.exists(RESOURCE_PATH):
            os.makedirs(RESOURCE_PATH)
        for fname in os.listdir(RESOURCE_PATH):
            if fname.endswith((".webp", ".png", ".jpg", ".jpeg")):
                key = fname.split(".")[0]
                f = discord.File(os.path.join(RESOURCE_PATH, fname), filename=fname)
                self.image_dict[key] = {"file": f, "name": fname}

    def get_image(self, name):
        if name not in self.image_dict:
            return self.image_dict["Default"]
        return self.image_dict[name]

            
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        self.get_resources()
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
    if not config.discord_token or not config.cod_token:
        logger.error("Please configure config.ini")
        sys.exit()

    bot = Bot(command_prefix = '!', description=description, intents = intents)
    bot.run(config.discord_token)

if __name__ == '__main__':
    start()



