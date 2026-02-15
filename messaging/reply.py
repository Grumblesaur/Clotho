import os
import discord
import stoat
from pathlib import Path
from datetime import datetime
from dicelang import result

EMBED_FIELD_LIMIT = 1024        # 1 KB
EMBED_DESCRIPTION_LIMIT = 4096  # 4 KB
CONTENT_LIMIT = 2000            # 2000 characters
FILE_LIMIT = 25 * 1024 * 1024   # 25 MB


class ReplyError(Exception):
    pass


class EmbedTooLarge(ReplyError):
    pass


class ContentTooLarge(ReplyError):
    pass


class AttachmentTooLarge(ReplyError):
    pass


def roll_embed(m: str, t: discord.User, r: result.Result) -> discord.Embed:
    em = discord.Embed(title=f'Roll', description=f'```\n{m.strip()}```', color=t.color)
    em.set_author(name=t.display_name)
    if r.helptext:
        em.add_field(name='Help', value=f'{r.value}', inline=False)
    else:
        if r.console:
            em.add_field(name='Message', value=f'```diff\n{r.console}```', inline=False)
        if r.value is not None:
            em.add_field(name='Result', value=f'```diff\n{r.value}```', inline=False)
        if r.error is not None:
            em.add_field(name='Error', value=f'```diff\n{r.error.__class__.__name__}: {r.error}```', inline=False)
    if len(em.description) > EMBED_DESCRIPTION_LIMIT:
        raise EmbedTooLarge('description')
    for field in em.fields:
        if len(field.value) > EMBED_FIELD_LIMIT:
            raise EmbedTooLarge(f'{field.name}')
    return em


def roll_content(m: str, t: discord.User, r: result.Result) -> str:
    contents = [f'**{t.display_name}**', f'```{m}```']
    if r.helptext:
        contents.append(f'**Help**\n{r.value}')
    else:
        if r.console:
            contents.append(f"**Message**```diff\n{r.console}```")
        if r.value is not None:
            contents.append(f"**Result**```diff\n{r.value}```")
        if r.error is not None:
            contents.append(f"**Error**```diff\n{r.error}```")
    content = '\n'.join(contents)
    if (n := len(content)) > CONTENT_LIMIT:
        raise ContentTooLarge(n)
    return content


def s_roll_content(m: str, t: stoat.User | stoat.Member, r: result.Result) -> str:
    name = t.nick or t.name if isinstance(t, stoat.Member) else t.display_name
    contents = [f'**{name}**', f'```\n{m}\n```']
    if r.helptext:
        contents.append(f'**Help**\n{r.value}')
    else:
        if r.console:
            contents.append(f'**Message**\n```diff\n{r.console}\n```')
        if r.value is not None:
            contents.append(f'**Result**\n```diff\n{r.value}\n```')
        if r.error is not None:
            contents.append(f'**Error**\n```diff\n{r.error}\n```')
    content = '\n'.join(contents)
    if (n := len(content)) > CONTENT_LIMIT:
        raise ContentTooLarge(n)
    return content


def roll_attachment(m: str, t: discord.User | stoat.User, r: result.Result) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    name = f'message-{timestamp}.md'
    with open(name, 'w') as f:
        f.write(f'**{t.display_name}**\n')
        f.write(f'```{m}```\n')
        if r.helptext:
            f.write(f'**Help**\n{r.value}\n')
        else:
            if r.console:
                f.write(f'**Message**\n```diff\n{r.console}```\n')
            if r.value is not None:
                f.write(f'**Result**\n```diff\n{r.value}```\n')
            if r.error is not None:
                f.write(f'**Error**\n```diff\n{r.error}```\n')

    if (in_bytes := os.path.getsize(name)) > FILE_LIMIT:
        os.remove(name)
        raise AttachmentTooLarge(in_bytes)
    return Path(name)
