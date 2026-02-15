import os
import argparse
import sys
import discord
import stoat
import configuration
import helpfiles
from messaging import reply
from dicelang.script import execute
from more_itertools import ilen
from discord.ext.commands import Bot, Context, parameter

MESSAGE_LIMIT = 2000
COMMAND_PREFIX = prefix = configuration.data['bot']['prefix']

stoat_bot = stoat.Client()

intents = discord.Intents.default()
intents.message_content = True
discord_bot = Bot(command_prefix=COMMAND_PREFIX, intents=intents)


def make_parser():
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description="Runs an instance of Clotho for a Stoat or Discord server.")
    parser.add_argument('service', help="Discord or Stoat", choices=('discord', 'stoat'))
    return parser


@discord_bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name=f'{COMMAND_PREFIX}docs quickstart')
    await discord_bot.change_presence(activity=activity)
    print('Connection to Discord initialized.')
    print(f'Connected to {ilen(discord_bot.guilds)} Discord server(s).')


@discord_bot.command(name='roll', help="Excecute a Dicelang procedure and display the result.")
async def roll(ctx: Context, *, dicelang: str = parameter(description='An expression or script in Dicelang.')):
    owner = ctx.author
    async with ctx.typing():
        result = execute(str(owner.id), str(ctx.guild.id), dicelang)
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


@discord_bot.command(name='docs', help="Access the documentation for the Dicelang language.")
async def docs(ctx: Context, *, keyword: str = parameter(description="A topic to request help on.")):
    async with ctx.typing():
        try:
            markdown, source_path = helpfiles.retrieve(keyword)
        except helpfiles.InvalidHelpTopic:
            topic_list = '- ' + '\n- '.join(sorted(helpfiles.retrieve.topics.keys()))
            markdown = f"""No help file defined for `{keyword}`. Try one of the following topics:\n{topic_list}"""
        # NOTE: Unless *I* fuck up the help files, none of the files should exceed the file attachment limit.
        if len(markdown) > MESSAGE_LIMIT:
            await ctx.reply(content="Help text too large. See attached file.", file=discord.File(source_path))
        else:
            await ctx.reply(content=markdown)


@stoat_bot.on(stoat.ReadyEvent)
async def s_ready(event: stoat.ReadyEvent, /):
    await stoat_bot.user.edit(status=stoat.UserStatusEdit(text=f'{COMMAND_PREFIX}docs quickstart',
                                                          presence=stoat.Presence.online))
    print(f'Connection to Stoat initialized with prefix {COMMAND_PREFIX}')
    print(f'Connected to {len(event.servers)} Stoat server(s).')


@stoat_bot.on(stoat.MessageCreateEvent)
async def s_on_message(event: stoat.MessageCreateEvent):
    message = event.message
    if message.author.relationship is stoat.RelationshipStatus.user:
        return

    owner = message.author
    server = message.server

    if message.content.startswith(remove := f'{COMMAND_PREFIX}roll'):
        async with stoat_bot.user.typing():
            dicelang = message.content.removeprefix(remove).lstrip()
            result = execute(str(owner.id), str(server), dicelang)
            try:
                await message.reply(reply.s_roll_content(dicelang, owner, result))
            except reply.ContentTooLarge:
                try:
                    await message.reply(content="Response too large. See attached file.",
                                        attachments=[stoat.Upload(path := reply.roll_attachment(dicelang, owner, result))])
                except reply.AttachmentTooLarge:
                    await message.reply(content="Response too large (> 25MB) to attach. Try a more reasonable command.")
                else:
                    os.remove(path)

    if message.content.startswith(remove := f'{COMMAND_PREFIX}docs'):
        async with stoat_bot.user.typing():
            # XXX: handle doc lookups
            pass


def main():
    parser = make_parser()
    args = parser.parse_args()
    discord_token = configuration.data['auth']['token']
    stoat_token = configuration.data['stoat']['token']
    if args.service.casefold() == 'discord':
        discord_bot.run(discord_token)
    elif args.service.casefold() == 'stoat':
        stoat_bot.run(stoat_token)


if __name__ == '__main__':
    main()
