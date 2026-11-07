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


def clean_card_mathtext(s: str) -> str:
    """Normalize equations and chemistry tags for Matplotlib mathtext rendering."""
    s = s.replace("$$", "$")

    # Convert \ce{...}
    def rep_ce(m: "re.Match[str]") -> str:
        inner = m.group(1).strip()
        inner = inner.replace("->", r" \rightarrow ").replace("<=>", r" \rightleftharpoons ")
        inner = re.sub(r"([A-Za-z])(\d+)", r"\1_{\2}", inner)
        inner = inner.replace(" . ", r" \cdot ")
        return rf"\mathrm{{{inner}}}"

    s = re.sub(r"\\ce\{([^}]+)\}", rep_ce, s)
    s = re.sub(r"\\frac(?![a-z])", r"\\dfrac", s)
    s = re.sub(r"\\le(?![a-z])", r"\\leq", s)
    s = re.sub(r"\\ge(?![a-z])", r"\\geq", s)
    s = re.sub(r"\\ne(?![a-z])", r"\\neq", s)
    s = re.sub(r"\\degree\b", r"^{\\circ}", s)
    return s


def wrap_text_with_math(text: str, max_chars: int = 52) -> List[str]:
    """Break text into lines while keeping math tokens atomic."""
    raw_tokens: List[str] = []
    pattern = re.compile(r"(\$[^\$]+\$|\S+)")
    for m in pattern.finditer(text):
        raw_tokens.append(m.group(0))

    # Merge isolated punctuation with preceding token
    tokens: List[str] = []
    for tok in raw_tokens:
        if tokens and tok in (",", ".", ";", ":", "?", "!"):
            tokens[-1] += tok
        else:
            tokens.append(tok)

    lines: List[str] = []
    curr: List[str] = []
    curr_len = 0
    for tok in tokens:
        vis = re.sub(r"\\[A-Za-z]+|\$|[{}]", "", tok)
        tok_len = max(len(vis), 1)
        if curr and (curr_len + tok_len + 1 > max_chars):
            lines.append(" ".join(curr))
            curr = [tok]
            curr_len = tok_len
        else:
            curr.append(tok)
            curr_len += tok_len + (1 if len(curr) > 1 else 0)
    if curr:
        lines.append(" ".join(curr))
    return lines


def render_question_card(
    question: str,
    options: Any = None,
    *,
    subject: str = "",
    chapter: str = "",
    fontsize: int = 22,
    dpi: int = 200,
    bg_color: str = "#1E1F22",
    text_color: str = "#FFFFFF",
    max_chars: int = 52,
) -> io.BytesIO:
    """Render a full textbook-style STEM question card (+ options) into a high-res PNG image.

    Designed specifically for Discord embed images so mobile and desktop users
    can read questions effortlessly without zooming.
    """
    try:
        from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: PLC0415
        from matplotlib.figure import Figure  # noqa: PLC0415
        import matplotlib  # noqa: PLC0415
    except ImportError as exc:
        raise RenderError("matplotlib is required to render question cards (pip install matplotlib)") from exc

    lines: List[str] = []

    # 1. Subject Header
    hdr = "   •   ".join(p for p in (subject.upper(), chapter) if p)
    if hdr:
        lines.append(hdr)
        lines.append("―" * 44)
        lines.append("")

    # 2. Question text wrapped
    q_clean = clean_card_mathtext(question)
    q_wrapped = wrap_text_with_math(q_clean, max_chars=max_chars)
    lines.extend(q_wrapped)

    # 3. Options
    if options:
        lines.append("")
        lines.append("―" * 44)
        for opt in options:
            if isinstance(opt, dict):
                k = opt.get("key", "")
                txt = opt.get("text", "").strip()
            elif isinstance(opt, tuple):
                k, txt = opt
            else:
                k, txt = "", str(opt).strip()
            txt_clean = clean_card_mathtext(txt)
            if txt_clean.startswith("$") and txt_clean.endswith("$"):
                math_content = txt_clean[1:-1]
                lines.append(rf"$\mathbf{{({k})}}\quad {math_content}$")
            else:
                lines.append(rf"$\mathbf{{({k})}}\quad$ {txt_clean}")

    card_text = "\n".join(lines)

    # Figure height directly proportional to line count
    num_lines = len(lines)
    fig_width = 9.5
    fig_height = max(2.5, (num_lines * 0.32) + 0.6)

    fig = Figure(figsize=(fig_width, fig_height), dpi=dpi)
    FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    fig.patch.set_facecolor(bg_color)

    with matplotlib.rc_context({"mathtext.fontset": "cm"}):
        ax.text(
            0.05, 0.94, card_text,
            color=text_color,
            fontsize=fontsize,
            va="top",
            ha="left",
            linespacing=1.65,
        )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=bg_color, bbox_inches="tight", pad_inches=0.3)
    buf.seek(0)
    return buf


async def arender_question_card(
    question: str,
    options: Any = None,
    *,
    subject: str = "",
    chapter: str = "",
    fontsize: int = 22,
    dpi: int = 200,
    bg_color: str = "#1E1F22",
    text_color: str = "#FFFFFF",
    max_chars: int = 52,
) -> io.BytesIO:
    """Async version of :func:`render_question_card` (runs off-thread)."""
    return await asyncio.to_thread(
        render_question_card,
        question,
        options,
        subject=subject,
        chapter=chapter,
        fontsize=fontsize,
        dpi=dpi,
        bg_color=bg_color,
        text_color=text_color,
        max_chars=max_chars,
    )
