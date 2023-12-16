# Skeleton for codbot
import sys
from config.config import Config
from discord.ext import commands
import discord
import asyncio
import logging
import traceback
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

extensions = ['handlers.sandbox']

config = Config()
if not config.discord_token:
    logger.error("Please enter your Discord bot account token in config.ini")
    sys.exit()

client = commands.Bot(command_prefix = '!', description='test123', intents = intents)
# client.run(config.discord_token)

# async def load_extensions():
#     for extension in extensions:
#         await client.load_extension(extension)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    loaded_extensions, failed_extensions = await load_extensions()
    logger.info("LOADED: {}".format(loaded_extensions))
    logger.info("FAILED: {}".format(failed_extensions))
    # await load_extensions()

async def load_extensions():
    loaded_extensions = []
    failed_extensions = []

    for extension in extensions:
        try:
            await client.load_extension(extension)
        except ImportError:
            failed_extensions.append((extension, traceback.format_exc()))
        else:
            loaded_extensions.append(extension)

    return loaded_extensions, failed_extensions


@client.command(name = "sync", description = 'sync')
async def sync(ctx) -> None:
    synced = await client.tree.sync()
    await ctx.send(f'Synced {len(synced)} commands')

async def main():
    async with client:
        await client.start(config.discord_token)

asyncio.run(main())