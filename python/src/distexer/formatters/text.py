"""Math-mode detection, normalization and LaTeX → Unicode transliteration.

Two output modes are supported:

* ``MODE_UNICODE_NATIVE`` – converts LaTeX into readable Unicode that renders on
  every Discord client (``\\alpha`` → ``α``, ``x^2`` → ``x²``, ``H_2O`` → ``H₂O``).
* ``MODE_PRESERVE_KATEX`` – keeps clean ``$...$`` KaTeX for clients/plugins that
  render LaTeX themselves (e.g. Vencord, BetterDiscord).
"""

from __future__ import annotations

import re
from typing import List, NamedTuple, Optional, Tuple

from .symbols import (
    ACCENTS,
    BLACKBOARD,
    CONTROL_SYMBOLS,
    FUNCTIONS,
    GREEK,
    IGNORED,
    IGNORED_WITH_ARG,
    MATRIX_DELIMS,
    SUBSCRIPTS,
    SUPERSCRIPTS,
    SYMBOLS,
    VULGAR_FRACTIONS,
)

MODE_PRESERVE_KATEX = "katex"
MODE_UNICODE_NATIVE = "unicode"
MODES = (MODE_UNICODE_NATIVE, MODE_PRESERVE_KATEX)

# $$display$$ first, then $inline$. Inline math may not start/end with
# whitespace and may not be followed by a digit, so "$5 and $10" is left alone.
MATH_RE = re.compile(
    r"(?<!\\)\$\$(.+?)(?<!\\)\$\$|(?<!\\)\$(?!\s)([^$\n]+?)(?<![\s\\])\$(?!\d)",
    re.S,
)

_DOUBLE_ESCAPE = re.compile(r"\\\\(?=[A-Za-z()])")
_OPERATOR_CHARS = set("+-−±∓×÷·/=<>≤≥≠≈,;:→←⇌↔∪∩")
_SCRIPT_CHARS = set(SUPERSCRIPTS.values()) | set(SUBSCRIPTS.values())

_TEXT_COMMANDS = {
    "text", "textrm", "textit", "textnormal", "textsf", "texttt", "mbox",
    "mathrm", "mathit", "mathsf", "mathtt", "operatorname", "mathcal",
    "mathscr", "mathfrak", "textup", "emph", "hbox",
}
_BOLD_COMMANDS = {"mathbf", "textbf", "boldsymbol", "bm", "pmb"}
_FRAC_COMMANDS = {"frac", "dfrac", "tfrac", "cfrac"}
_ARG_COMMANDS = (
    _TEXT_COMMANDS | _BOLD_COMMANDS | _FRAC_COMMANDS | set(ACCENTS)
    | {"sqrt", "ce", "pu", "mathbb", "binom", "dbinom", "tbinom", "boxed",
       "xrightarrow", "xleftarrow", "overset", "underset", "stackrel",
       "overbrace", "underbrace", "textcolor", "begin", "pmod"}
)


class MathSpan(NamedTuple):
    start: int
    end: int
    content: str
    display: bool


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Repair common LLM output problems before formatting.

    * ``\\\\frac`` (double-escaped) → ``\\frac``
    * ``\\( … \\)`` / ``\\[ … \\]`` → ``$ … $`` / ``$$ … $$``
    * unclosed ``$`` / ``$$`` delimiters are closed
    * unbalanced braces inside math are balanced
    """
    if not text:
        return ""
    text = text.replace("\r\n", "\n")
    text = _DOUBLE_ESCAPE.sub(lambda _m: "\\", text)
    text = re.sub(r"\\\[(.+?)\\\]", lambda m: f"$${m.group(1)}$$", text, flags=re.S)
    text = re.sub(r"\\\((.+?)\\\)", lambda m: f"${m.group(1)}$", text, flags=re.S)
    text = _close_dollars(text)

    def fix(match: "re.Match[str]") -> str:
        if match.group(1) is not None:
            return f"$${balance_braces(match.group(1))}$$"
        return f"${balance_braces(match.group(2))}$"

    return MATH_RE.sub(fix, text)


def _close_dollars(text: str) -> str:
    if len(re.findall(r"(?<!\\)\$\$", text)) % 2:
        text += "$$"
    singles = re.sub(r"(?<!\\)\$\$", "", text)
    positions = [m.start() for m in re.finditer(r"(?<!\\)\$", singles)]
    if len(positions) % 2:
        tail = singles[positions[-1] + 1:]
        # only close it if what follows actually looks like math (not "$5")
        if re.search(r"\\[A-Za-z]|[\^_]", tail):
            text = text.rstrip() + "$"
    return text


def balance_braces(expr: str) -> str:
    """Drop stray ``}`` and append missing ``}`` (escaped braces are ignored)."""
    out: List[str] = []
    depth = 0
    i = 0
    while i < len(expr):
        char = expr[i]
        if char == "\\" and i + 1 < len(expr):
            out.append(expr[i:i + 2])
            i += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            if depth == 0:
                i += 1
                continue
            depth -= 1
        out.append(char)
        i += 1
    return "".join(out) + "}" * depth


def find_math(text: str) -> List[MathSpan]:
    """Return every ``$…$`` / ``$$…$$`` span in ``text``."""
    spans = []
    for m in MATH_RE.finditer(text):
        display = m.group(1) is not None
        spans.append(MathSpan(m.start(), m.end(), m.group(1) if display else m.group(2), display))
    return spans


# ---------------------------------------------------------------------------
# Tiny LaTeX reader
# ---------------------------------------------------------------------------

def _read_group(s: str, i: int) -> Tuple[str, int]:
    depth = 0
    j = i
    while j < len(s):
        char = s[j]
        if char == "\\":
            j += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def _read_arg(s: str, i: int) -> Tuple[str, int]:
    n = len(s)
    while i < n and s[i] == " ":
        i += 1
    if i >= n:
        return "", i
    char = s[i]
    if char == "{":
        return _read_group(s, i)
    if char == "\\":
        j = i + 1
        if j < n and s[j].isalpha():
            while j < n and s[j].isalpha():
                j += 1
            return s[i:j], j
        return s[i:j + 1], j + 1
    return char, i + 1


def _read_optional(s: str, i: int) -> Tuple[Optional[str], int]:
    j = i
    n = len(s)
    while j < n and s[j] == " ":
        j += 1
    if j < n and s[j] == "[":
        depth = 0
        k = j
        while k < n:
            if s[k] == "[":
                depth += 1
            elif s[k] == "]":
                depth -= 1
                if depth == 0:
                    return s[j + 1:k], k + 1
            k += 1
    return None, i


# ---------------------------------------------------------------------------
# Unicode helpers
# ---------------------------------------------------------------------------

def to_superscript(text: str) -> Optional[str]:
    if all(ch in SUPERSCRIPTS for ch in text):
        return "".join(SUPERSCRIPTS[ch] for ch in text)
    return None


def to_subscript(text: str) -> Optional[str]:
    if all(ch in SUBSCRIPTS for ch in text):
        return "".join(SUBSCRIPTS[ch] for ch in text)
    return None


def _script(text: str, sup: bool) -> str:
    t = text.strip()
    if not t:
        return ""
    if sup and t in ("∘", "°"):
        return "°"
    mapped = to_superscript(t) if sup else to_subscript(t)
    if mapped is not None:
        return mapped
    wrapped = t if len(t) == 1 else f"({t})"
    # "\_" so Discord doesn't turn the rest of the line into italics
    return ("^" if sup else "\\_") + wrapped


def _is_loose_atomic(text: str) -> bool:
    return bool(text) and not any(ch.isspace() or ch in _OPERATOR_CHARS for ch in text)


def _is_strict_atomic(text: str) -> bool:
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return True
    return len(text) >= 1 and text[0] not in _OPERATOR_CHARS and all(ch in _SCRIPT_CHARS for ch in text[1:])


def _fraction(num: str, den: str) -> str:
    num, den = num.strip(), den.strip()
    if num.isdigit() and den.isdigit():
        vulgar = VULGAR_FRACTIONS.get((num, den))
        if vulgar:
            return vulgar
        return f"{to_superscript(num)}⁄{to_subscript(den)}"
    left = num if _is_loose_atomic(num) else f"({num})"
    right = den if _is_strict_atomic(den) else f"({den})"
    return f"{left}/{right}"


def _sqrt(index: Optional[str], radicand: str) -> str:
    radicand = radicand.strip()
    if index is None or index.strip() in ("", "2"):
        root = "√"
    elif index.strip() == "3":
        root = "∛"
    elif index.strip() == "4":
        root = "∜"
    else:
        root = (to_superscript(index.strip()) or f"({index.strip()})") + "√"
    return root + (radicand if _is_loose_atomic(radicand) else f"({radicand})")


def _bold(text: str) -> str:
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(chr(0x1D400 + ord(ch) - ord("A")))
        elif "a" <= ch <= "z":
            out.append(chr(0x1D41A + ord(ch) - ord("a")))
        elif "0" <= ch <= "9":
            out.append(chr(0x1D7CE + ord(ch) - ord("0")))
        else:
            out.append(ch)
    return "".join(out)


def _accent(text: str, mark: str) -> str:
    if not text:
        return ""
    if mark in ("\u0305", "\u0332", "\u0338"):  # overline / underline / cancel span everything
        return "".join(ch + mark for ch in text)
    return text + mark


def _chem(arg: str) -> str:
    """Minimal mhchem (``\\ce{}``) support."""
    t = arg
    t = t.replace("<=>", r"\rightleftharpoons ").replace("<->", r"\leftrightarrow ")
    t = t.replace("->", r"\to ").replace("<-", r"\gets ")
    t = re.sub(r"(?<=[A-Za-z)\]])(\d+)", lambda m: "_{" + m.group(1) + "}", t)
    t = re.sub(r"(?<=[A-Za-z)\]}])(\d*[+-])(?=\s|$)", lambda m: "^{" + m.group(1) + "}", t)
    return _convert(t)


def _environment(env: str, body: str) -> str:
    base = env.rstrip("*")
    if base == "array":
        _, k = _read_arg(body, 0)
        body = body[k:]
        base = "matrix"
    rows = [row for row in re.split(r"\\\\(?:\[[^\]]*\])?", body) if row.strip()]
    cells = [[_convert(cell).strip() for cell in re.split(r"(?<!\\)&", row)] for row in rows]
    if base in MATRIX_DELIMS:
        left, right = MATRIX_DELIMS[base]
        return left + "; ".join(", ".join(row) for row in cells) + right
    if base in ("cases", "dcases", "rcases"):
        return "{ " + "; ".join(" ".join(c for c in row if c) for row in cells) + " }"
    return "\n".join(" ".join(c for c in row if c) for row in cells)


def _find_env_end(s: str, j: int, env: str) -> Tuple[str, int]:
    begin_tok, end_tok = "\\begin{" + env + "}", "\\end{" + env + "}"
    depth, k = 1, j
    while True:
        nb, ne = s.find(begin_tok, k), s.find(end_tok, k)
        if ne == -1:
            return s[j:], len(s)
        if nb != -1 and nb < ne:
            depth += 1
            k = nb + len(begin_tok)
            continue
        depth -= 1
        if depth == 0:
            return s[j:ne], ne + len(end_tok)
        k = ne + len(end_tok)


def _command(name: str, s: str, j: int) -> Tuple[str, int]:
    """Convert ``\\name`` (already consumed up to ``j``) and return (text, new_index)."""
    if name in _FRAC_COMMANDS:
        num, j = _read_arg(s, j)
        den, j = _read_arg(s, j)
        return _fraction(_convert(num), _convert(den)), j
    if name in ("binom", "dbinom", "tbinom"):
        n, j = _read_arg(s, j)
        k, j = _read_arg(s, j)
        return f"C({_convert(n).strip()}, {_convert(k).strip()})", j
    if name == "sqrt":
        index, j = _read_optional(s, j)
        radicand, j = _read_arg(s, j)
        return _sqrt(_convert(index) if index is not None else None, _convert(radicand)), j
    if name in _TEXT_COMMANDS:
        arg, j = _read_arg(s, j)
        return (arg if name.startswith("text") or name == "mbox" else _convert(arg)), j
    if name in _BOLD_COMMANDS:
        arg, j = _read_arg(s, j)
        return _bold(_convert(arg)), j
    if name == "mathbb":
        arg, j = _read_arg(s, j)
        return "".join(BLACKBOARD.get(ch, ch) for ch in arg.strip()), j
    if name in ACCENTS:
        arg, j = _read_arg(s, j)
        return _accent(_convert(arg).strip(), ACCENTS[name]), j
    if name in ("ce", "pu"):
        arg, j = _read_arg(s, j)
        return _chem(arg), j
    if name in ("xrightarrow", "xleftarrow"):
        _, j = _read_optional(s, j)
        arg, j = _read_arg(s, j)
        label = _convert(arg).strip()
        arrow = "→" if name == "xrightarrow" else "←"
        return (f" —{label}{arrow} " if label else f" {arrow} "), j
    if name in ("overset", "stackrel", "underset"):
        top, j = _read_arg(s, j)
        base, j = _read_arg(s, j)
        top_u, base_u = _convert(top).strip(), _convert(base).strip()
        if base_u in ("→", "←", "⇌", "⟶", "="):
            return f" —{top_u}{base_u} ", j
        return base_u + _script(top_u, sup=name != "underset"), j
    if name in ("overbrace", "underbrace", "boxed"):
        arg, j = _read_arg(s, j)
        inner = _convert(arg)
        return (f"[{inner}]" if name == "boxed" else inner), j
    if name == "textcolor":
        _, j = _read_arg(s, j)
        arg, j = _read_arg(s, j)
        return _convert(arg), j
    if name == "pmod":
        arg, j = _read_arg(s, j)
        return f" (mod {_convert(arg).strip()})", j
    if name == "begin":
        env, j = _read_arg(s, j)
        body, j = _find_env_end(s, j, env)
        return _environment(env, body), j
    if name == "end":
        _, j = _read_arg(s, j)
        return "", j
    if name in IGNORED_WITH_ARG:
        _, j = _read_arg(s, j)
        return "", j
    if name in IGNORED:
        if name in ("left", "right", "middle") or name.startswith(("big", "Big")):
            if j < len(s) and s[j] == ".":
                j += 1
        return "", j
    if name in ("bmod", "mod"):
        return " mod ", j
    if name in FUNCTIONS:
        return name, j
    if name in GREEK:
        # "\Delta H" -> "ΔH"
        if j + 1 < len(s) and s[j] == " " and s[j + 1].isalnum():
            j += 1
        return GREEK[name], j
    if name in SYMBOLS:
        return SYMBOLS[name], j
    return name, j


def _convert(s: str) -> str:
    out: List[str] = []
    i, n = 0, len(s)
    while i < n:
        char = s[i]
        if char == "\\":
            if i + 1 < n and s[i + 1].isalpha():
                j = i + 1
                while j < n and s[j].isalpha():
                    j += 1
                text, i = _command(s[i + 1:j], s, j)
                out.append(text)
                continue
            if i + 1 < n:
                out.append(CONTROL_SYMBOLS.get(s[i + 1], s[i + 1]))
                i += 2
                continue
            i += 1
            continue
        if char in "^_":
            arg, i = _read_arg(s, i + 1)
            out.append(_script(_convert(arg), sup=char == "^"))
            continue
        if char == "{":
            content, i = _read_group(s, i)
            out.append(_convert(content))
            continue
        if char == "}":
            i += 1
            continue
        if char == "~":
            out.append(" ")
        elif char == "*":
            out.append("∗")
        elif char == "'":
            out.append("′")
        else:
            out.append(char)
        i += 1
    return "".join(out)


def latex_to_unicode(expr: str) -> str:
    """Transliterate a LaTeX math expression (without ``$``) to Unicode."""
    e = balance_braces(_DOUBLE_ESCAPE.sub(lambda _m: "\\", expr))
    e = e.replace("<=>", "⇌").replace("<->", "↔").replace("->", "→")
    out = _convert(e)
    out = re.sub(r"[ \t\u2009]{2,}", " ", out)
    out = "\n".join(line.strip() for line in out.split("\n"))
    return out.strip()


def is_complex(expr: str) -> bool:
    """Heuristic: would this formula be noticeably clearer as an image?

    True for matrices/environments, fractions with compound numerators or
    denominators (anything that would need ``(a)/(b)``), radicals containing
    fractions, and scripts that Unicode can't express.
    """
    if re.search(r"\\begin\{", expr):
        return True
    if re.search(r"\\sqrt\s*(\[[^\]]*\])?\s*\{[^}]*\\[dt]?frac", expr):
        return True
    if re.search(r"\\(?:overset|underset|stackrel|overbrace|underbrace)", expr):
        return True
    unicode = latex_to_unicode(expr)
    if re.search(r"\)/|/\(", unicode):
        return True
    if re.search(r"(?:\^|\\_)\([^)]{5,}\)", unicode):
        return True
    if len(re.findall(r"\\[dtc]?frac", expr)) >= 2 and "/" in unicode:
        return True
    return False


_BARE_CMD = re.compile(r"\\([A-Za-z]+)")
_BARE_SUP = re.compile(r"(?<=[A-Za-z0-9)\]])\^(\{[^{}\n]*\}|[0-9]+|[a-z](?![a-z]))")
_BARE_SUB = re.compile(r"(?<=[A-Za-z)\]])_(\{[^{}\n]*\}|\d+)(?![A-Za-z_])")


def _convert_bare(text: str) -> str:
    """Convert LaTeX that an LLM forgot to wrap in ``$`` (``\\alpha-amino``, ``H_2O``)."""
    out: List[str] = []
    i = 0
    for m in _BARE_CMD.finditer(text):
        if m.start() < i:
            continue
        name = m.group(1)
        if name in GREEK or name in SYMBOLS or name in _ARG_COMMANDS - {"begin"}:
            out.append(text[i:m.start()])
            converted, i = _command(name, text, m.end())
            out.append(converted)
    out.append(text[i:])
    result = "".join(out)

    def sup(m: "re.Match[str]") -> str:
        raw = m.group(1).strip("{}")
        return to_superscript(raw) or m.group(0)

    def sub(m: "re.Match[str]") -> str:
        raw = m.group(1).strip("{}")
        return to_subscript(raw) or m.group(0)

    return _BARE_SUB.sub(sub, _BARE_SUP.sub(sup, result))


def format_text(
    text: str,
    mode: str = MODE_UNICODE_NATIVE,
    *,
    collect: Optional[List[str]] = None,
    bare_commands: bool = True,
) -> str:
    """Format every math span in ``text`` for Discord.

    Args:
        text: Raw text, possibly containing ``$…$``/``$$…$$`` math.
        mode: ``MODE_UNICODE_NATIVE`` or ``MODE_PRESERVE_KATEX``.
        collect: If a list is given, *complex* formulas are appended to it and
            replaced by an ``[eq. N]`` marker so they can be rendered as an image.
        bare_commands: In Unicode mode, also convert stray LaTeX found outside
            of ``$`` delimiters.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES!r}, got {mode!r}")
    text = normalize(text)

    def replace(m: "re.Match[str]") -> str:
        display = m.group(1) is not None
        expr = (m.group(1) if display else m.group(2)).strip()
        if collect is not None and is_complex(expr):
            collect.append(expr)
            marker = f"`[eq. {len(collect)}]`"
            return f"\n{marker}\n" if display else marker
        if mode == MODE_PRESERVE_KATEX:
            return f"$${expr}$$" if display else f"${expr}$"
        converted = latex_to_unicode(expr)
        return f"\n{converted}\n" if display else converted

    pieces: List[str] = []
    last = 0
    for m in MATH_RE.finditer(text):
        plain = text[last:m.start()]
        pieces.append(_convert_bare(plain) if mode == MODE_UNICODE_NATIVE and bare_commands else plain)
        pieces.append(replace(m))
        last = m.end()
    plain = text[last:]
    pieces.append(_convert_bare(plain) if mode == MODE_UNICODE_NATIVE and bare_commands else plain)

    out = "".join(pieces)
    out = re.sub(r"[ \t]+\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
