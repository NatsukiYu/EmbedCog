from asyncio import TimeoutError
from logging import getLogger
from typing import Optional, Union

import discord
from discord import TextChannel, User, Message, Embed
from discord.ext.commands import Cog, Bot, Context, command
from discord_slash import SlashContext, ComponentContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component

from .parser import parse_embed, NoBodyException

logger = getLogger(__name__)


class EmbedCog(Cog):
    """ユーザーの投稿をEmbedに変換するCog"""

    EMOJI_OK = '⭕'
    EMOJI_NG = '❌'

    ID_OK = 'button_ok'
    ID_NG = 'button_ng'

    def __init__(self, bot: Bot):
        self.bot = bot

    @command('embed')
    async def on_message(self, ctx: Union[Context, SlashContext], color: Optional[discord.Color] = None):
        author: User = ctx.author

        await ctx.message.delete()

        if ctx.message.reference is None:
            logger.debug('no source message found.')
            await ctx.send('適用するメッセージに対してコマンドを送信してください')
            return
        source_message: Message = ctx.message.reference.resolved

        # async with ctx.typing():
        try:
            option = {
                'author': {
                    'name': author.name,
                    'icon_url': str(author.avatar_url)
                }
            }
            if color is not None:
                option['color'] = color.value

            logger.debug('creating embed')
            embed = parse_embed(source_message.content, option)
        except NoBodyException:
            await ctx.send('見出しに対応する内容がありません', hidden=True, delete_after=5)
            return
        except Exception as e:
            await ctx.send('メッセージの変換に失敗しました', hidden=True, delete_after=5)
            return

        await self.confirm(ctx, embed)

    async def confirm(self, ctx: Context, embed: Embed):
        channel: TextChannel = ctx.channel
        author: User = ctx.author
        source_message: Message = ctx.message.reference.resolved

        embedded_message = await channel.send(embed=embed)
        confirm_message = await embedded_message.reply('正しく表示されていますか？', delete_after=20)
        await confirm_message.add_reaction(self.EMOJI_OK)
        await confirm_message.add_reaction(self.EMOJI_NG)

        def check(_reaction: discord.Reaction, _user: discord.User):
            return _reaction.message == confirm_message and author == _user and _reaction.emoji in [self.EMOJI_OK, self.EMOJI_NG]

        try:
            logger.debug('wait for reaction')
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=20)

            if reaction.emoji == self.EMOJI_OK:
                logger.debug('reaction ok')
                await source_message.delete()
                await channel.send('完了しました', delete_after=5)
            elif reaction.emoji == self.EMOJI_NG:
                logger.debug('reaction ng')
                await embedded_message.delete()
                await channel.send('取り消しました', delete_after=5)
            await confirm_message.delete()
        except TimeoutError:
            logger.debug('reaction timeout')
            await confirm_message.delete()

    # async def confirm_slash(self, ctx: SlashContext, embed: Embed):
    #     preview = await ctx.send(embed=embed, hidden=True)
    #
    #     action_row = create_actionrow(
    #         create_button(custom_id=id_o, label='OK', emoji=emoji_o, style=ButtonStyle.green),
    #         create_button(custom_id=id_x, label='NG', emoji=emoji_x, style=ButtonStyle.red),
    #     )
    #     await ctx.send('正しく表示されていますか？', components=[action_row], hidden=True)
    #
    #     try:
    #         logger.debug('wait for reaction')
    #         cpn: ComponentContext = await wait_for_component(self.bot, components=action_row)
    #
    #         if cpn.custom_id == id_o:
    #             logger.debug('reaction ok')
    #             await preview.delete()
    #             await ctx.send(embed=embed)
    #         elif cpn.custom_id == id_x:
    #             logger.debug('reaction ng')
    #             await preview.delete()
    #     except TimeoutError:
    #         logger.debug('reaction timeout')
    #         # await preview.delete()


def setup(bot):
    return bot.add_cog(EmbedCog(bot))
