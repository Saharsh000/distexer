"""Auto-listifier: turns run-on STEM stems into readable bullet trees.

Detects (in priority order):

* ``Assertion (A): … Reason (R): …``
* ``Statement 1: … Statement 2: …`` / ``Statement I: … Statement II: …``
* ``(i) … (ii) …``, ``(I) … (II) …``, ``(a) … (b) …``, ``(A) … (B) …``, ``(1) … (2) …``

Lists nest: an ``(i)`` item that itself contains ``(a) … (b) …`` becomes a sub-list.
"""

from __future__ import annotations

import re
from typing import Callable, List, Tuple

from .text import find_math

INDENT = "\u2003"  # em space – Discord does not collapse it
BULLET = "▸"
SUB_BULLET = "◦"

Match = Tuple[int, int, str]  # (start, end, display label)

_ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]
_FAMILIES: List[List[str]] = [
    _ROMAN,
    [r.upper() for r in _ROMAN],
    list("abcdefghijklmnopqrstuvwxyz"),
    list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    [str(n) for n in range(1, 31)],
]

_ENUM_RE = re.compile(
    r"(?:^|(?<=[\s,;:.\-–—]))\(\s*([ivxlIVXL]{1,5}|[a-zA-Z]|\d{1,2})\s*\)(?=\s|$)"
)
_STATEMENT_RE = re.compile(
    r"\bStatement\s*[-–]?\s*(\d+|IV|V|I{1,3}|[A-D])\s*[:.)\-–]", re.I
)
_ASSERTION_RE = re.compile(r"\bAssertion\s*(?:\(\s*A\s*\))?\s*[:.\-–]?", re.I)
_REASON_RE = re.compile(r"\bReason\s*(?:\(\s*R\s*\))?\s*[:.\-–]?", re.I)

TAIL_RE = re.compile(
    r"(?<=[.?!])\s+(?=(?:Which|What|Choose|Select|Identify|How many|The correct|"
    r"Find|Pick|Mark|Among|In the light|Then|Hence|Now)\b)"
)


def _outside_math(text: str) -> Callable[[int], bool]:
    spans = [(s.start, s.end) for s in find_math(text)]
    return lambda pos: not any(start <= pos < end for start, end in spans)


def _find_assertion_reason(text: str) -> List[Match]:
    a = _ASSERTION_RE.search(text)
    if not a:
        return []
    r = _REASON_RE.search(text, a.end())
    if not r:
        return []
    return [(a.start(), a.end(), "Assertion (A):"), (r.start(), r.end(), "Reason (R):")]


def _find_statements(text: str) -> List[Match]:
    ok = _outside_math(text)
    found = [
        (m.start(), m.end(), f"Statement {m.group(1).upper()}:")
        for m in _STATEMENT_RE.finditer(text)
        if ok(m.start())
    ]
    return found if len(found) >= 2 else []


def find_enumeration(text: str) -> List[Match]:
    """Return the first ordered run (length ≥ 2) of ``(x)`` markers."""
    ok = _outside_math(text)
    found = [(m.start(), m.end(), m.group(1)) for m in _ENUM_RE.finditer(text) if ok(m.start())]
    for family in _FAMILIES:
        run: List[Match] = []
        want = 0
        for start, end, token in found:
            if want < len(family) and token == family[want]:
                run.append((start, end, f"({token})"))
                want += 1
        if len(run) >= 2:
            return run
    return []


def clean_item(text: str) -> str:
    text = re.sub(r"^[\s:.\-–—]+", "", text)
    text = re.sub(r"[\s,;]*(?:\band\b|\bor\b)?[\s,;]*$", "", text)
    return text.strip()


def split_tail(text: str) -> Tuple[str, str]:
    """Split ``"… last item. Which of the above is correct?"`` into (item, question)."""
    m = TAIL_RE.search(text)
    if not m:
        return text, ""
    return text[:m.start()], text[m.end():].strip()


def _render(text: str, matches: List[Match], depth: int) -> str:
    lead = text[:matches[0][0]].rstrip()
    items: List[List[str]] = []
    for index, (_, end, label) in enumerate(matches):
        stop = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        items.append([label, text[end:stop]])
    items[-1][1], tail = split_tail(items[-1][1])

    bullet = BULLET if depth == 0 else SUB_BULLET
    lines: List[str] = [lead] if lead else []
    for label, body in items:
        rendered = listify(clean_item(body), _depth=depth + 1)
        first, _, rest = rendered.partition("\n")
        lines.append(f"{INDENT * depth}{bullet} **{label}** {first}".rstrip())
        if rest:
            lines.append(rest)
    if tail:
        lines.append(tail)
    return "\n".join(lines)


def listify(text: str, *, _depth: int = 0) -> str:
    """Convert inline run-on enumerations into an indented bullet tree."""
    if not text or _depth > 3:
        return text
    for finder in (_find_assertion_reason, _find_statements, find_enumeration):
        matches = finder(text)
        if len(matches) >= 2:
            return _render(text, matches, _depth)
    return text


def split_options(text: str) -> List[Tuple[str, str]]:
    """Split ``"(A) foo (B) bar (C) baz"`` into ``[("A","foo"), ("B","bar"), …]``."""
    matches = find_enumeration(text)
    if len(matches) >= 2 and matches[0][2].strip("()").isalpha() and len(matches[0][2]) == 3:
        out = []
        for index, (_, end, label) in enumerate(matches):
            stop = matches[index + 1][0] if index + 1 < len(matches) else len(text)
            out.append((label.strip("()").upper(), clean_item(text[end:stop])))
        return out
    plain = re.split(r"(?:^|\n|\s)(?=[A-Da-d][.)]\s)", text)
    plain = [p.strip() for p in plain if p.strip()]
    if len(plain) >= 2:
        return [(p[0].upper(), clean_item(p[2:])) for p in plain]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [(chr(65 + i), line) for i, line in enumerate(lines)]
