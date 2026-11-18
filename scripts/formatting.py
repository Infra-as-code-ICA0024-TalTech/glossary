"""Shared Markdown and PDF text formatting for course materials."""
import html
import re

import markdown

EMPHASIS = re.compile(r'(?<![*\w])\*([^*\n]+?)\*(?![*\w])')


def to_html(value):
    return markdown.markdown(value, extensions=['fenced_code', 'sane_lists'])


def ascii_text(value):
    return value.translate(str.maketrans({'—':'-', '–':'-', '−':'-', '“':'"', '”':'"', '’':"'", '‘':"'", ' ':' '}))


def inline(value, mono='Courier'):
    value = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', value)
    value = html.escape(ascii_text(value))
    value = re.sub(r'`([^`]+)`', rf'<font name="{mono}">\1</font>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    return EMPHASIS.sub(r'<i>\1</i>', value)
