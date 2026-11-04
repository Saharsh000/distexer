"""Embed + formula-image color themes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union


@dataclass(frozen=True)
class Theme:
    name: str
    embed_color: int
    text_color: str
    background: Optional[str]  # None = transparent PNG


THEMES = {
    # Transparent PNG, white glyphs. Looks native in dark mode (invisible in light mode).
    "discord_dark": Theme("discord_dark", 0x5865F2, "#FFFFFF", None),
    # Transparent PNG, near-black glyphs for light-mode servers.
    "discord_light": Theme("discord_light", 0x5865F2, "#060607", None),
    # Solid embed-gray card: readable in BOTH light and dark mode.
    "solid_dark": Theme("solid_dark", 0x2B2D31, "#FFFFFF", "#2B2D31"),
    "amoled": Theme("amoled", 0x111214, "#FFFFFF", "#000000"),
    "emerald": Theme("emerald", 0x57F287, "#FFFFFF", None),
    "crimson": Theme("crimson", 0xED4245, "#FFFFFF", None),
    "gold": Theme("gold", 0xFEE75C, "#FFFFFF", None),
}


def get_theme(theme: Union[str, Theme, None]) -> Theme:
    if theme is None:
        return THEMES["discord_dark"]
    if isinstance(theme, Theme):
        return theme
    try:
        return THEMES[theme]
    except KeyError as exc:
        raise ValueError(f"Unknown theme {theme!r}. Available: {', '.join(THEMES)}") from exc
