from asyncio import TimeoutError
from logging import getLogger
from typing import Optional

import discord
from discord import User, Message
from discord.ext.commands import Cog, Bot, Context, command

from discord_slash import ComponentContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component

from .parser import parse_embed, NoBodyException

logger = getLogger(__name__)


class EmbedCog(Cog):
    """ユーザーの投稿をEmbedに変換するCog"""

    EMOJI_OK = '🙆'
    EMOJI_NG = '🙅'

    ID_OK = 'button_ok'
    ID_NG = 'button_ng'

    def __init__(self, bot: Bot):
        self.bot = bot

    @command('embed')
    async def on_message(self, ctx: Context, color: Optional[discord.Color] = None):
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
            await ctx.send('見出しに対応する内容がありません', delete_after=5)
            return
        except Exception as e:
            await ctx.send('メッセージの変換に失敗しました', delete_after=5)
            return

        embed_message = await ctx.send(embed=embed)

        action_row = create_actionrow(
            create_button(custom_id=self.ID_OK, label='OK', style=ButtonStyle.green, emoji=self.EMOJI_OK),
            create_button(custom_id=self.ID_NG, label='NG', style=ButtonStyle.red, emoji=self.EMOJI_NG),
        )
        await ctx.send('正しく表示されていますか？', components=[action_row])

        try:
            logger.debug('wait for button')
            cpn: ComponentContext = await wait_for_component(self.bot, components=action_row)

            if cpn.custom_id == self.ID_OK:
                logger.debug('reaction ok')
                await source_message.delete()
                await cpn.edit_origin(content='完了しました', delete_after=5, components=None)  # todo delete_after seems not working
            elif cpn.custom_id == self.ID_NG:
                logger.debug('reaction ng')
                await embed_message.delete()
                await cpn.edit_origin(content='取り消しました', delete_after=5, components=None)
        except TimeoutError:
            logger.debug('reaction timeout')


def setup(bot):
    return bot.add_cog(EmbedCog(bot))
