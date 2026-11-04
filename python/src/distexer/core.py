"""Framework-agnostic question layout (used by the Discord helpers, usable anywhere)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

from .formatters.lists import listify, split_options
from .formatters.matching import _HEADER_RE, format_match, format_match_options, parse_mapping, parse_match
from .formatters.symbols import REGIONAL_INDICATORS
from .formatters.text import MODE_UNICODE_NATIVE, format_text, normalize

OptionsInput = Union[None, str, Sequence[str], Sequence[Tuple[str, str]], Dict[str, str]]

Q_TYPES = ("single", "multiple", "integer", "match", "numeric", "truefalse")

FOOTERS = {
    "single": "🎯 Single correct • choose ONE option",
    "multiple": "✅ Multiple correct • choose ALL that apply",
    "integer": "🔢 Integer type • reply with a whole number",
    "numeric": "🔢 Numerical • reply with a number",
    "match": "🔗 Match the following • choose the correct mapping",
    "truefalse": "⚖️ True or False",
}

_OPTION_PREFIX = re.compile(r"^\s*\(?([A-Za-z])[).:]\s+")


@dataclass
class QuestionLayout:
    body: str
    options: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    footer: str = ""
    q_type: str = "single"

    def as_text(self) -> str:
        """Body + options as one Discord message / embed description."""
        if not self.options:
            return self.body
        return f"{self.body}\n\n" + "\n".join(self.options)


def badge(label: str) -> str:
    """``"A"`` → 🇦 (regional indicator). Non-letters fall back to `` `label` ``."""
    upper = label.strip().upper()
    return REGIONAL_INDICATORS.get(upper, f"`{label}`") if len(upper) == 1 else f"`{label}`"


def _coerce_options(options: OptionsInput) -> List[Tuple[str, str]]:
    if options is None:
        return []
    if isinstance(options, str):
        return split_options(options)
    if isinstance(options, dict):
        return [(str(k), str(v)) for k, v in options.items()]
    out: List[Tuple[str, str]] = []
    for index, option in enumerate(options):
        default = chr(65 + index)
        if isinstance(option, (tuple, list)):
            out.append((str(option[0]), str(option[1])))
            continue
        text = str(option)
        m = _OPTION_PREFIX.match(text)
        if m and m.group(1).upper() == default:
            text = text[m.end():]
        out.append((default, text))
    return out


def format_message(text: str, mode: str = MODE_UNICODE_NATIVE) -> str:
    """Normalize + listify + format math for any plain Discord message."""
    return format_text(listify(normalize(text)), mode)


def build_question(
    question: str,
    options: OptionsInput = None,
    *,
    q_type: str = "single",
    mode: str = MODE_UNICODE_NATIVE,
    render_complex_math: bool = True,
) -> QuestionLayout:
    """Turn a raw (LLM-generated) question into a clean :class:`QuestionLayout`.

    Complex formulas are pulled into ``layout.formulas`` (to be rendered as an
    image) when ``render_complex_math`` is True; everything else becomes Unicode
    (or clean KaTeX in ``MODE_PRESERVE_KATEX``).
    """
    if q_type not in Q_TYPES:
        raise ValueError(f"q_type must be one of {Q_TYPES}, got {q_type!r}")
    raw = normalize(question)

    structured: Optional[str] = None
    if q_type == "match" or len(_HEADER_RE.findall(raw)) >= 2:
        match = parse_match(raw)
        if match:
            structured = format_match(match)
            q_type = "match"
    if structured is None:
        structured = listify(raw)

    formulas: List[str] = []
    body = format_text(structured, mode, collect=formulas if render_complex_math else None)
    if len(formulas) == 1:
        body = body.replace("`[eq. 1]`", "`[equation ↓]`")

    option_lines: List[str] = []
    for label, text in _coerce_options(options):
        text = normalize(text)
        if q_type == "match" and parse_mapping(text):
            option_lines.append(f"{badge(label)} ({label.upper()})  {format_match_options(text)}")
        else:
            option_lines.append(f"{badge(label)}  {format_text(text, mode)}")

    return QuestionLayout(
        body=body,
        options=option_lines,
        formulas=formulas,
        footer=FOOTERS.get(q_type, ""),
        q_type=q_type,
    )
