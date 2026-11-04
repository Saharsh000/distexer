"""Browser-free LaTeX → PNG rendering.

Backends (tried in order with ``backend="auto"``):

1. ``matplotlib`` – fully offline mathtext engine (``pip install distexer[render]``).
   Renders in a few milliseconds; supports fractions, radicals, integrals, sums,
   Greek, accents… but not matrices/environments or ``\\ce``.
2. ``codecogs`` – CodeCogs LaTeX CDN (full LaTeX incl. matrices, amsmath).
3. ``quicklatex`` – QuickLaTeX API (full LaTeX incl. ``mhchem``).

Results are cached in-process (LRU), so repeated trivia questions are instant.
"""

from __future__ import annotations

import asyncio
import io
import re
import threading
import urllib.parse
import urllib.request
from collections import OrderedDict
from dataclasses import dataclass, replace
from typing import Any, List, Optional, Sequence, Tuple

USER_AGENT = "distexer/0.1 (+https://github.com/Saharsh000/distexer)"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# Things matplotlib's mathtext can't parse – go straight to a LaTeX backend.
_MATHTEXT_UNSUPPORTED = re.compile(
    r"\\(?:begin|end|ce|pu|xrightarrow|xleftarrow|boxed|cancel|substack|tag|"
    r"dbinom|tbinom|cfrac|textcolor|textbf|mathscr|middle|iiint)\b"
)


class RenderError(RuntimeError):
    """Raised when every configured backend failed to render a formula."""


@dataclass(frozen=True)
class RenderConfig:
    dpi: int = 200
    text_color: str = "#FFFFFF"
    background: Optional[str] = None  # None → transparent
    fontsize: int = 15
    backend: str = "auto"  # auto | matplotlib | codecogs | quicklatex
    timeout: float = 8.0
    cache_size: int = 256


def _hex(color: str) -> str:
    return color.lstrip("#").upper()


def _rgba(color: Optional[str]) -> Tuple[int, int, int, int]:
    if color is None:
        return (0, 0, 0, 0)
    value = _hex(color)
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


class MathRenderer:
    """Render LaTeX formulas to PNG bytes without a headless browser."""

    def __init__(self, config: Optional[RenderConfig] = None, **overrides: Any) -> None:
        self.config = replace(config or RenderConfig(), **overrides)
        self._cache: "OrderedDict[tuple, bytes]" = OrderedDict()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ API

    def render(self, expr: str) -> io.BytesIO:
        """Render a single formula and return a PNG buffer."""
        return self.render_many([expr], labels=False)

    def render_many(self, formulas: Sequence[str], *, labels: Optional[bool] = None) -> io.BytesIO:
        """Render several formulas stacked vertically into ONE PNG.

        Discord embeds hold one image, so multiple complex formulas are labelled
        ``(1)``, ``(2)``, … to match the ``[eq. N]`` markers in the embed text.
        """
        formulas = [f.strip().strip("$").strip() for f in formulas if f and f.strip()]
        if not formulas:
            raise RenderError("Nothing to render")
        labels = len(formulas) > 1 if labels is None else labels
        key = (tuple(formulas), labels, self.config)

        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                self._cache.move_to_end(key)
                return io.BytesIO(cached)

        backends = (
            ["matplotlib", "codecogs", "quicklatex"]
            if self.config.backend == "auto"
            else [self.config.backend]
        )
        errors: List[str] = []
        for backend in backends:
            try:
                data = getattr(self, f"_render_{backend}")(formulas, labels)
            except Exception as exc:  # noqa: BLE001 – fall through to next backend
                errors.append(f"{backend}: {exc}")
                continue
            with self._lock:
                self._cache[key] = data
                while len(self._cache) > self.config.cache_size:
                    self._cache.popitem(last=False)
            return io.BytesIO(data)
        raise RenderError("All render backends failed → " + " | ".join(errors))

    async def arender(self, expr: str) -> io.BytesIO:
        """Non-blocking :meth:`render` (runs in a worker thread)."""
        return await asyncio.to_thread(self.render, expr)

    async def arender_many(self, formulas: Sequence[str], *, labels: Optional[bool] = None) -> io.BytesIO:
        return await asyncio.to_thread(self.render_many, formulas, labels=labels)

    def to_discord_file(self, expr_or_formulas: Any, filename: str = "formula.png"):
        """Render and wrap the PNG in a ``discord.File``."""
        import discord  # noqa: PLC0415 – optional dependency

        formulas = [expr_or_formulas] if isinstance(expr_or_formulas, str) else list(expr_or_formulas)
        return discord.File(self.render_many(formulas), filename=filename)

    # ------------------------------------------------------------ backends

    def _render_matplotlib(self, formulas: Sequence[str], labels: bool) -> bytes:
        try:
            import matplotlib  # noqa: PLC0415
            from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: PLC0415
            from matplotlib.figure import Figure  # noqa: PLC0415
        except ImportError as exc:
            raise RenderError("matplotlib not installed (pip install 'distexer[render]')") from exc

        pngs = []
        for index, formula in enumerate(formulas, 1):
            tex = to_mathtext(formula)
            if labels:
                tex = rf"\mathrm{{({index})}}\quad " + tex
            buf = io.BytesIO()
            with matplotlib.rc_context({"mathtext.fontset": "cm"}):
                fig = Figure()
                FigureCanvasAgg(fig)
                fig.text(0, 0, f"${tex}$", fontsize=self.config.fontsize, color=self.config.text_color)
                fig.savefig(
                    buf,
                    format="png",
                    dpi=self.config.dpi,
                    transparent=self.config.background is None,
                    facecolor=self.config.background or (0, 0, 0, 0),
                    bbox_inches="tight",
                    pad_inches=0.12,
                )
            pngs.append(buf.getvalue())
        return pngs[0] if len(pngs) == 1 else self._stack(pngs)

    def _stack(self, pngs: Sequence[bytes]) -> bytes:
        from PIL import Image  # noqa: PLC0415 – ships with matplotlib

        images = [Image.open(io.BytesIO(p)).convert("RGBA") for p in pngs]
        gap = int(self.config.dpi * 0.1)
        width = max(im.width for im in images)
        height = sum(im.height for im in images) + gap * (len(images) - 1)
        canvas = Image.new("RGBA", (width, height), _rgba(self.config.background))
        y = 0
        for im in images:
            canvas.alpha_composite(im, dest=(0, y))
            y += im.height + gap
        out = io.BytesIO()
        canvas.save(out, format="PNG", optimize=True)
        return out.getvalue()

    def _latex_document(self, formulas: Sequence[str], labels: bool) -> str:
        if len(formulas) == 1 and not labels:
            return rf"\displaystyle {formulas[0]}"
        rows = [
            (rf"\text{{({i})}}\quad " if labels else "") + rf"\displaystyle {f}"
            for i, f in enumerate(formulas, 1)
        ]
        return r"\begin{array}{l} " + r" \\[10pt] ".join(rows) + r" \end{array}"

    def _fetch(self, request: urllib.request.Request) -> bytes:
        with urllib.request.urlopen(request, timeout=self.config.timeout) as response:  # noqa: S310
            return response.read()

    def _render_codecogs(self, formulas: Sequence[str], labels: bool) -> bytes:
        cfg = self.config
        background = r"\bg{transparent}" if cfg.background is None else rf"\bg{{{_hex(cfg.background)}}}"
        latex = (
            rf"\dpi{{{cfg.dpi}}}{background}\fg{{{_hex(cfg.text_color)}}} "
            + self._latex_document(formulas, labels)
        )
        url = "https://latex.codecogs.com/png.image?" + urllib.parse.quote(latex, safe="")
        data = self._fetch(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}))
        if not data.startswith(PNG_SIGNATURE):
            raise RenderError("CodeCogs did not return a PNG")
        return data

    def _render_quicklatex(self, formulas: Sequence[str], labels: bool) -> bytes:
        cfg = self.config
        payload = urllib.parse.urlencode({
            "formula": self._latex_document(formulas, labels),
            "fsize": f"{max(12, int(cfg.fontsize * cfg.dpi / 110))}px",
            "fcolor": _hex(cfg.text_color),
            "bcolor": _hex(cfg.background) if cfg.background else "FFFFFF",
            "mode": "0",
            "out": "1",
            "errors": "1",
            "remhost": "quicklatex.com",
            "preamble": r"\usepackage{amsmath}\usepackage{amssymb}\usepackage[version=4]{mhchem}",
        }).encode()
        request = urllib.request.Request(
            "https://quicklatex.com/latex3.f",
            data=payload,
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
        )
        lines = self._fetch(request).decode("utf-8", "replace").split()
        if len(lines) < 2 or lines[0] != "0":
            raise RenderError(f"QuickLaTeX error: {' '.join(lines[:12])}")
        data = self._fetch(urllib.request.Request(lines[1], headers={"User-Agent": USER_AGENT}))
        if not data.startswith(PNG_SIGNATURE):
            raise RenderError("QuickLaTeX did not return a PNG")
        return data


def to_mathtext(expr: str) -> str:
    """Translate KaTeX-flavoured LaTeX into something matplotlib mathtext accepts."""
    if _MATHTEXT_UNSUPPORTED.search(expr):
        raise RenderError("expression needs a full LaTeX backend")
    e = expr
    e = re.sub(r"\\(?:text|textrm|operatorname|textnormal|mbox)\s*\{([^{}]*)\}",
               lambda m: r"\mathrm{" + m.group(1).replace(" ", r"\ ") + "}", e)
    e = re.sub(r"\\frac(?![a-z])", r"\\dfrac", e)
    e = re.sub(r"\\(?:displaystyle|limits|nolimits)\b", "", e)
    e = re.sub(r"\\le(?![a-z])", r"\\leq", e)
    e = re.sub(r"\\ge(?![a-z])", r"\\geq", e)
    e = re.sub(r"\\ne(?![a-z])", r"\\neq", e)
    e = re.sub(r"\\implies\b", r"\\Rightarrow", e)
    e = re.sub(r"\\iff\b", r"\\Leftrightarrow", e)
    e = re.sub(r"\\degree\b", r"^{\\circ}", e)
    e = re.sub(r"\\(?:dots)\b", r"\\ldots", e)
    e = e.replace("->", r"\rightarrow ").replace("<=>", r"\rightleftharpoons ")
    return e


_default_renderer: Optional[MathRenderer] = None


def default_renderer() -> MathRenderer:
    global _default_renderer
    if _default_renderer is None:
        _default_renderer = MathRenderer()
    return _default_renderer


def render_png(expr: str, **config: Any) -> io.BytesIO:
    """Shortcut: ``distexer.render_png(r"\\frac{a}{b}")`` → PNG ``BytesIO``."""
    renderer = MathRenderer(**config) if config else default_renderer()
    return renderer.render(expr)
