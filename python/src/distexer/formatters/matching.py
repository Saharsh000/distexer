"""Match-the-following layout: ``List-I`` / ``List-II`` parsing and mapping badges."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from .lists import clean_item, split_tail

Pair = Tuple[str, str]
ItemsInput = Union[Sequence[str], Sequence[Pair], Dict[str, str]]

_HEADER_RE = re.compile(r"\b(List|Column|Col\.?)\s*[-–—]?\s*(II|I|1|2|A|B)\b", re.I)
_ITEM_PAREN_RE = re.compile(r"\(\s*([A-Za-z]|\d{1,2}|[ivx]{1,4})\s*\)")
_ITEM_PLAIN_RE = re.compile(r"(?:^|(?<=[\s,;:]))([A-Z]|\d{1,2}|[ivx]{1,4})[.)](?=\s)")
_PAIR_RE = re.compile(
    r"\b([A-Za-z]|[ivxIVX]{1,4})\s*(?:->|-|–|—|→|➔|⟶|:|=|\bto\b)\s*([A-Za-z]|\d{1,2}|[ivxIVX]{1,4})\b"
)

DEFAULT_LEFT_LABELS = "PQRSTUVW"
DEFAULT_RIGHT_LABELS = [str(n) for n in range(1, 11)]


@dataclass
class MatchQuestion:
    stem: str
    list_i: List[Pair]
    list_ii: List[Pair]
    tail: str = ""
    header_i: str = "LIST — I"
    header_ii: str = "LIST — II"
    extra: Dict[str, str] = field(default_factory=dict)


def _family(token: str) -> str:
    if token.isdigit():
        return "num"
    if token in ("i", "ii", "iii", "iv", "v", "vi"):
        return "roman"
    return "upper" if token.isupper() else "lower"


def _parse_items(segment: str) -> Tuple[List[Pair], str]:
    """Return (items, leftover_tail)."""
    matches = list(_ITEM_PAREN_RE.finditer(segment))
    if len(matches) < 2:
        matches = list(_ITEM_PLAIN_RE.finditer(segment))
    if len(matches) < 2:
        parts = [p.strip() for p in re.split(r"\n|;", segment) if p.strip(" :\n")]
        return ([(str(i + 1), clean_item(p)) for i, p in enumerate(parts)] if len(parts) >= 2 else []), ""

    family = _family(matches[0].group(1))
    kept = []
    tail_start = None
    for m in matches:
        if _family(m.group(1)) != family:
            tail_start = m.start()
            break
        kept.append(m)

    items: List[Pair] = []
    for index, m in enumerate(kept):
        stop = kept[index + 1].start() if index + 1 < len(kept) else (tail_start or len(segment))
        items.append((m.group(1).upper() if family != "num" else m.group(1), segment[m.end():stop]))

    tail = segment[tail_start:].strip() if tail_start is not None else ""
    last_label, last_text = items[-1]
    last_text, cue = split_tail(last_text)
    items[-1] = (last_label, last_text)
    tail = " ".join(t for t in (cue, tail) if t)
    return [(label, clean_item(text)) for label, text in items], tail


def parse_match(text: str) -> Optional[MatchQuestion]:
    """Parse an unstructured "Match List-I with List-II" question.

    Returns ``None`` when the text has no recognizable two-list structure.
    """
    headers = list(_HEADER_RE.finditer(text))
    first = next((h for h in headers if h.group(2).upper() in ("I", "1", "A")), None)
    if first is None:
        return None
    second = next(
        (h for h in headers if h.start() > first.end() and h.group(2).upper() in ("II", "2", "B")),
        None,
    )
    if second is None:
        return None

    stem = text[:first.start()].strip().rstrip(":")
    # "Match List-I with List-II" – the real lists start at the *next* header pair
    later = [h for h in headers if h.start() > second.end()]
    between = text[first.end():second.start()]
    if later and len(between) < 40 and not _ITEM_PAREN_RE.search(between):
        stem = text[:later[0].start()].strip().rstrip(":")
        first = next((h for h in later if h.group(2).upper() in ("I", "1", "A")), first)
        second = next(
            (h for h in later if h.start() > first.end() and h.group(2).upper() in ("II", "2", "B")),
            second,
        )

    left, _ = _parse_items(text[first.end():second.start()])
    right, tail = _parse_items(text[second.end():])
    if not left or not right:
        return None
    kind = first.group(1).rstrip(".").upper()
    kind = "COLUMN" if kind.startswith("COL") else "LIST"
    return MatchQuestion(
        stem=stem,
        list_i=left,
        list_ii=right,
        tail=tail,
        header_i=f"{kind} — I",
        header_ii=f"{kind} — II",
    )


def _coerce(items: ItemsInput, default_labels: Iterable[str]) -> List[Pair]:
    if isinstance(items, dict):
        return [(str(k), str(v)) for k, v in items.items()]
    labels = list(default_labels)
    out: List[Pair] = []
    for index, item in enumerate(items):
        if isinstance(item, (tuple, list)):
            out.append((str(item[0]), str(item[1])))
        else:
            out.append((labels[index] if index < len(labels) else str(index + 1), str(item)))
    return out


def build_match(
    list_i: ItemsInput,
    list_ii: ItemsInput,
    *,
    stem: str = "Match List — I with List — II",
    tail: str = "",
) -> MatchQuestion:
    """Build a :class:`MatchQuestion` from structured data instead of parsing."""
    return MatchQuestion(
        stem=stem,
        list_i=_coerce(list_i, DEFAULT_LEFT_LABELS),
        list_ii=_coerce(list_ii, DEFAULT_RIGHT_LABELS),
        tail=tail,
    )


def format_match(question: MatchQuestion) -> str:
    """Render a :class:`MatchQuestion` as mobile-friendly Discord markdown."""
    lines: List[str] = []
    if question.stem:
        lines += [question.stem, ""]
    lines.append(f"📋 **{question.header_i}**")
    lines += [f"`[{label}]` {text}" for label, text in question.list_i]
    lines += ["", f"📋 **{question.header_ii}**"]
    lines += [f"`[{label}]` {text}" for label, text in question.list_ii]
    if question.tail:
        lines += ["", question.tail]
    return "\n".join(lines)


def parse_mapping(option: str) -> List[Pair]:
    """``"P-1, Q-2, R-3"`` / ``"P→1; Q→2"`` / ``"(P)-(1)"`` → ``[("P","1"), …]``."""
    cleaned = re.sub(r"\(\s*(\w{1,4})\s*\)", r"\1", option)
    pairs = [(a.upper(), b) for a, b in _PAIR_RE.findall(cleaned)]
    return pairs if len(pairs) >= 2 else []


def format_match_options(option: str) -> str:
    """Format a mapping option as ``P ➔ 1  •  Q ➔ 2  •  R ➔ 3``.

    Returns the option unchanged if no mapping could be parsed.
    """
    pairs = parse_mapping(option)
    if not pairs:
        return option.strip()
    return "  •  ".join(f"{a} ➔ {b}" for a, b in pairs)
