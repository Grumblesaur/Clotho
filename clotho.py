import os
import discord
import configuration
from messaging import reply
from dicelang.script import execute
from more_itertools import ilen
from discord.ext.commands import Bot, Context

prefix = configuration.data['bot']['prefix']
token = configuration.data['auth']['token']
intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix=prefix, intents=intents)


@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name='dice rolls')
    await bot.change_presence(activity=activity)
    print('Connection to Discord initialized.')
    print(f'Connected to {ilen(bot.guilds)} server(s).')


@bot.command()
async def roll(ctx: Context, *, arg):
    owner = ctx.author
    async with ctx.typing():
        result = execute(str(owner.id), arg)
        try:
            await ctx.reply(embed=reply.roll_embed(arg, owner, result))
        except reply.EmbedTooLarge:
            try:
                await ctx.reply(content=reply.roll_content(arg, owner, result))
            except reply.ContentTooLarge:
                try:
                    await ctx.reply(content="Response too large. See attached file.",
                                    file=discord.File(path := reply.roll_attachment(arg, owner, result)))
                except reply.AttachmentTooLarge:
                    await ctx.reply(content="Response too large (> 25MB) to attach. Try a more reasonable command.")
                else:
                    os.remove(path)

bot.run(token)
