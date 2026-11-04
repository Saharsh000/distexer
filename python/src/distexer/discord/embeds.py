"""One-line ``discord.py`` embed builders.

``discord.py`` is an optional dependency: ``pip install "distexer[discord]"``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple, Union

from ..core import OptionsInput, QuestionLayout, build_question
from ..formatters.text import MODE_UNICODE_NATIVE
from ..renderer.engine import MathRenderer, RenderConfig, RenderError
from ..themes import Theme, get_theme

if TYPE_CHECKING:  # pragma: no cover
    import discord

EMBED_DESCRIPTION_LIMIT = 4096
EMBED_TITLE_LIMIT = 256

_renderers: Dict[Theme, MathRenderer] = {}


def _discord():
    try:
        import discord  # noqa: PLC0415 – top-level discord.py, not this subpackage
    except ImportError as exc:  # pragma: no cover
        raise ImportError('distexer.discord needs discord.py → pip install "distexer[discord]"') from exc
    return discord


def renderer_for(theme: Union[str, Theme, None]) -> MathRenderer:
    """Shared, cached renderer whose colors match the theme."""
    resolved = get_theme(theme)
    if resolved not in _renderers:
        _renderers[resolved] = MathRenderer(
            RenderConfig(text_color=resolved.text_color, background=resolved.background)
        )
    return _renderers[resolved]


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _embed(
    layout: QuestionLayout,
    *,
    title: str,
    theme: Theme,
    color: Optional[int],
    footer: Optional[str],
    url: Optional[str],
) -> "discord.Embed":
    discord = _discord()
    embed = discord.Embed(
        title=_truncate(title, EMBED_TITLE_LIMIT) if title else None,
        description=_truncate(layout.as_text(), EMBED_DESCRIPTION_LIMIT),
        color=color if color is not None else theme.embed_color,
        url=url,
    )
    footer_text = footer if footer is not None else layout.footer
    if footer_text:
        embed.set_footer(text=footer_text)
    return embed


def create_question_embed(
    title: str,
    question: str,
    options: OptionsInput = None,
    q_type: str = "single",
    theme: Union[str, Theme] = "discord_dark",
    render_complex_math: bool = True,
    *,
    mode: str = MODE_UNICODE_NATIVE,
    renderer: Optional[MathRenderer] = None,
    color: Optional[int] = None,
    footer: Optional[str] = None,
    url: Optional[str] = None,
    filename: str = "formula.png",
) -> Tuple["discord.Embed", Optional["discord.File"]]:
    """Build a clean question embed (+ formula image when needed).

    Returns ``(embed, file)``; ``file`` is ``None`` if no image was needed.
    Send with ``await channel.send(embed=embed, file=file)`` – when ``file`` is
    ``None`` discord.py simply sends no attachment.

    .. note:: Rendering may hit the network (CodeCogs fallback). Inside async
       bot code prefer :func:`acreate_question_embed` so the event loop never blocks.
    """
    resolved = get_theme(theme)
    layout = build_question(question, options, q_type=q_type, mode=mode, render_complex_math=render_complex_math)
    png = None
    if layout.formulas:
        try:
            png = (renderer or renderer_for(resolved)).render_many(layout.formulas)
        except RenderError:
            layout = build_question(question, options, q_type=q_type, mode=mode, render_complex_math=False)
    return _finish(layout, png, title=title, theme=resolved, color=color, footer=footer, url=url, filename=filename)


async def acreate_question_embed(
    title: str,
    question: str,
    options: OptionsInput = None,
    q_type: str = "single",
    theme: Union[str, Theme] = "discord_dark",
    render_complex_math: bool = True,
    *,
    mode: str = MODE_UNICODE_NATIVE,
    renderer: Optional[MathRenderer] = None,
    color: Optional[int] = None,
    footer: Optional[str] = None,
    url: Optional[str] = None,
    filename: str = "formula.png",
) -> Tuple["discord.Embed", Optional["discord.File"]]:
    """Async, non-blocking version of :func:`create_question_embed`."""
    resolved = get_theme(theme)
    layout = build_question(question, options, q_type=q_type, mode=mode, render_complex_math=render_complex_math)
    png = None
    if layout.formulas:
        try:
            png = await (renderer or renderer_for(resolved)).arender_many(layout.formulas)
        except RenderError:
            layout = build_question(question, options, q_type=q_type, mode=mode, render_complex_math=False)
    return _finish(layout, png, title=title, theme=resolved, color=color, footer=footer, url=url, filename=filename)


def _finish(layout, png, *, title, theme, color, footer, url, filename):
    discord = _discord()
    embed = _embed(layout, title=title, theme=theme, color=color, footer=footer, url=url)
    file = None
    if png is not None:
        file = discord.File(png, filename=filename)
        embed.set_image(url=f"attachment://{filename}")
    return embed, file


def render_formula(
    expr: str,
    filename: str = "formula.png",
    theme: Union[str, Theme] = "discord_dark",
) -> "discord.File":
    """Render a single formula straight to a ``discord.File``."""
    return _discord().File(renderer_for(theme).render(expr), filename=filename)


async def arender_formula(
    expr: str,
    filename: str = "formula.png",
    theme: Union[str, Theme] = "discord_dark",
) -> "discord.File":
    """Async version of :func:`render_formula`."""
    return _discord().File(await renderer_for(theme).arender(expr), filename=filename)
