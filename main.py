from colorama import init

init()
from colorama import Fore

import disnake
from disnake.ext import commands
import os
from core.enums import *

from dotenv import load_dotenv
load_dotenv()

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('!'),
    intents=disnake.Intents.all(),
    test_guilds=[ClientInfo.BOT_GUILD_ID])
bot.remove_command('help')

def cogs_names():
    cogs_list = []
    for filename in os.listdir(f"./cogs"):
        if filename.endswith(".py"):
            cogs_list.append(disnake.OptionChoice(
                name=f'{filename[:-3]}',
                value=f'{filename[:-3]}'
            ))
    return cogs_list


@bot.slash_command(
    name='reload',
    description='Reloading the bot file',
    options=[
        disnake.Option(
            name='extension',
            description="The name of the cog",
            type=disnake.OptionType.string,
            required=True,
            choices=cogs_names()
        )
    ]
)
async def reload(ctx: disnake.ApplicationCommandInteraction, extension: str):
    if ctx.author.id != ClientInfo.DEVELOPER_ID:
        await ctx.send(embed=disnake.Embed(description=f'Нет доступа!', colour=Color.GRAY), ephemeral=True)
        return
    try:
        bot.reload_extension(f"cogs.{extension}")
    except Exception as e:
        await ctx.send(
            embed=disnake.Embed(
                description=f'Cog: **{extension}** -  **not** uploaded!\n Error: **```{e}```**',
                colour=Color.GRAY), 
                ephemeral=True)
        return
    await ctx.send(
        embed=disnake.Embed(
            description=f'Cog: **{extension}** Successfully rebooted!', colour=Color.GRAY),
            ephemeral=True)

@bot.event
async def on_ready():
    print(Fore.GREEN + "The bot is running")
    print(Fore.GREEN + f'You entered as {bot.user}')

for filename in os.listdir(f"./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(os.getenv("TOKEN"))
