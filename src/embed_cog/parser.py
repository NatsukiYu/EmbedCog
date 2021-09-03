import re
from copy import deepcopy

from discord.embeds import Embed, EmptyEmbed

section_pattern = re.compile(r'\n(?=={1,3})')


class NoBodyException(Exception):
    pass


def parse_embed(text: str, options: dict = None) -> Embed:
    """
    テキストをEmbedに解析

    :param text: 解析するテキスト
    :param options: Embedに追加する要素
    :return: テキストを変換したEmbed
    """
    result = deepcopy(options) if options is not None else {}

    sections = re.split(section_pattern, text)

    def split(txt: str, body_required: bool):
        r = txt.split('\n', 1)
        if len(r) == 1:
            if body_required:
                raise NoBodyException(f'body is required: {txt}')
            else:
                return [r[0], EmptyEmbed]
        return r

    sec = sections[0]
    if not sec.startswith('='):
        # no title
        description = sec
        result['description'] = description
        sections = sections[1:]
    elif sec.startswith('= '):
        # title
        title, description = split(sec, False)
        title = title[2:]
        result['title'] = title
        result['description'] = description
        sections = sections[1:]

    def parse_section(txt: str):
        name, value = split(txt, True)
        name: str
        if name.startswith('== '):
            inline = False
            name = name[3:]  # '==  name' should be 'name'
        elif name.startswith('=== '):
            inline = True
            name = name[4:]
        else:
            return {'name': 'parse error', 'value': text}
        return {'name': name, 'value': value, 'inline': inline}

    embeds = list(map(lambda s: parse_section(s), sections))
    if len(embeds) > 0:
        result['fields'] = embeds

    return Embed.from_dict(result)
