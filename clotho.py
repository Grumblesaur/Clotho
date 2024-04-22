import os
import discord
import configuration
import helpfiles
from messaging import reply
from dicelang.script import execute
from more_itertools import ilen
from discord.ext.commands import Bot, Context, parameter

prefix = configuration.data['bot']['prefix']
token = configuration.data['auth']['token']
intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix=prefix, intents=intents)


@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name=f'{prefix}docs quickstart')
    await bot.change_presence(activity=activity)
    print('Connection to Discord initialized.')
    print(f'Connected to {ilen(bot.guilds)} server(s).')


@bot.command(name='roll', help="Accept a dicelang procedure and send the result back as a message.")
async def roll(ctx: Context, *, dicelang: str = parameter(description='An expression or script in Dicelang.')):
    owner = ctx.author
    async with ctx.typing():
        result = execute(str(owner.id), dicelang)
        try:
            await ctx.reply(embed=reply.roll_embed(dicelang, owner, result))
        except reply.EmbedTooLarge:
            try:
                await ctx.reply(content=reply.roll_content(dicelang, owner, result))
            except reply.ContentTooLarge:
                try:
                    await ctx.reply(content="Response too large. See attached file.",
                                    file=discord.File(path := reply.roll_attachment(dicelang, owner, result)))
                except reply.AttachmentTooLarge:
                    await ctx.reply(content="Response too large (> 25MB) to attach. Try a more reasonable command.")
                else:
                    os.remove(path)


@bot.command(name='docs', help="Access the documentation for the Dicelang language.")
async def docs(ctx: Context, *, keyword: str = parameter(description="A topic to request help on.")):
    async with ctx.typing():
        try:
            markdown = helpfiles.retrieve(keyword)
        except helpfiles.InvalidHelpTopic:
            topic_list = '- ' + '\n- '.join(sorted(helpfiles.retrieve.topics.keys()))
            markdown = f"""No help file defined for `keyword`. Try one of the following topics:\n{topic_list}"""
        await ctx.reply(content=markdown)

bot.run(token)
