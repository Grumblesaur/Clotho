import discord
import configuration
from dicelang.script import execute
from more_itertools import ilen
from discord.ext.commands import Bot, Context

prefix = configuration.data['bot']['prefix']
token = configuration.data['auth']['token']
intents = discord.Intents.default()
intents.message_content = True
TEST_SERVER = discord.Object(1228469917976629258)
bot = Bot(command_prefix=prefix, intents=intents)


@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name='dice rolls')
    await bot.change_presence(activity=activity)
    print('Connection to Discord initialized.')
    print(f'Connected to {ilen(bot.guilds)} server(s).')


@bot.command()
async def roll(ctx: Context, *, arg):
    owner = str(ctx.author.id)
    result = execute(owner, arg)
    await ctx.reply(result)


bot.run(token)
