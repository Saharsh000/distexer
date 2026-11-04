"""distexer – the headless STEM & math presentation engine for Discord bots.

Quick start::

    import distexer

    distexer.format_message(r"The $\\alpha$-particle has charge $+2e$ and $E = mc^2$")
    # 'The α-particle has charge +2e and E = mc²'

    embed, file = await distexer.acreate_question_embed(
        title="Kinematics", question=raw, options=["A", "B", "C", "D"]
    )
    await channel.send(embed=embed, file=file)
"""

from .core import FOOTERS, Q_TYPES, QuestionLayout, badge, build_question, format_message
from .discord.embeds import acreate_question_embed, arender_formula, create_question_embed, render_formula
from .formatters import (
    MODE_PRESERVE_KATEX,
    MODE_UNICODE_NATIVE,
    MatchQuestion,
    build_match,
    find_math,
    format_match,
    format_match_options,
    format_text,
    is_complex,
    latex_to_unicode,
    listify,
    normalize,
    parse_match,
    split_options,
)
from .renderer import MathRenderer, RenderConfig, RenderError, render_png
from .themes import THEMES, Theme, get_theme

__version__ = "0.1.0"

__all__ = [
    "FOOTERS",
    "MODE_PRESERVE_KATEX",
    "MODE_UNICODE_NATIVE",
    "MatchQuestion",
    "MathRenderer",
    "Q_TYPES",
    "QuestionLayout",
    "RenderConfig",
    "RenderError",
    "THEMES",
    "Theme",
    "__version__",
    "acreate_question_embed",
    "arender_formula",
    "badge",
    "build_match",
    "build_question",
    "create_question_embed",
    "find_math",
    "format_match",
    "format_match_options",
    "format_message",
    "format_text",
    "get_theme",
    "is_complex",
    "latex_to_unicode",
    "listify",
    "normalize",
    "parse_match",
    "render_formula",
    "render_png",
    "split_options",
]
