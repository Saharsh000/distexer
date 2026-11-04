import { findMath } from "./text.js";

export const INDENT = "\u2003";
export const BULLET = "▸";
export const SUB_BULLET = "◦";

type Match = [start: number, end: number, label: string];

const ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"];
const FAMILIES: string[][] = [
  ROMAN,
  ROMAN.map((r) => r.toUpperCase()),
  [..."abcdefghijklmnopqrstuvwxyz"],
  [..."ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
  Array.from({ length: 30 }, (_, i) => String(i + 1)),
];

const ENUM_RE = /(?:^|(?<=[\s,;:.\-–—]))\(\s*([ivxlIVXL]{1,5}|[a-zA-Z]|\d{1,2})\s*\)(?=\s|$)/g;
const STATEMENT_RE = /\bStatement\s*[-–]?\s*(\d+|IV|V|I{1,3}|[A-D])\s*[:.)\-–]/gi;
const ASSERTION_RE = /\bAssertion\s*(?:\(\s*A\s*\))?\s*[:.\-–]?/i;
const REASON_RE = /\bReason\s*(?:\(\s*R\s*\))?\s*[:.\-–]?/i;
export const TAIL_RE =
  /(?<=[.?!])\s+(?=(?:Which|What|Choose|Select|Identify|How many|The correct|Find|Pick|Mark|Among|In the light|Then|Hence|Now)\b)/;

const outsideMath = (text: string) => {
  const spans = findMath(text);
  return (pos: number) => !spans.some((s) => s.start <= pos && pos < s.end);
};

function findAssertionReason(text: string): Match[] {
  const a = ASSERTION_RE.exec(text);
  if (!a) return [];
  const after = a.index + a[0].length;
  const r = REASON_RE.exec(text.slice(after));
  if (!r) return [];
  const rStart = after + r.index;
  return [
    [a.index, after, "Assertion (A):"],
    [rStart, rStart + r[0].length, "Reason (R):"],
  ];
}

function findStatements(text: string): Match[] {
  const ok = outsideMath(text);
  const found: Match[] = [...text.matchAll(STATEMENT_RE)]
    .filter((m) => ok(m.index ?? 0))
    .map((m) => [m.index ?? 0, (m.index ?? 0) + m[0].length, `Statement ${m[1].toUpperCase()}:`]);
  return found.length >= 2 ? found : [];
}

/** First ordered run (length ≥ 2) of `(x)` markers. */
export function findEnumeration(text: string): Match[] {
  const ok = outsideMath(text);
  const found = [...text.matchAll(ENUM_RE)].filter((m) => ok(m.index ?? 0));
  for (const family of FAMILIES) {
    const run: Match[] = [];
    let want = 0;
    for (const m of found) {
      if (want < family.length && m[1] === family[want]) {
        run.push([m.index ?? 0, (m.index ?? 0) + m[0].length, `(${m[1]})`]);
        want++;
      }
    }
    if (run.length >= 2) return run;
  }
  return [];
}

export const cleanItem = (text: string): string =>
  text
    .replace(/^[\s:.\-–—]+/, "")
    .replace(/[\s,;]*(?:\band\b|\bor\b)?[\s,;]*$/, "")
    .trim();

export function splitTail(text: string): [string, string] {
  const m = TAIL_RE.exec(text);
  if (!m) return [text, ""];
  return [text.slice(0, m.index), text.slice(m.index + m[0].length).trim()];
}

function render(text: string, matches: Match[], depth: number): string {
  const lead = text.slice(0, matches[0][0]).trimEnd();
  const items = matches.map(([, end, label], k) => {
    const stop = k + 1 < matches.length ? matches[k + 1][0] : text.length;
    return [label, text.slice(end, stop)] as [string, string];
  });
  const [lastBody, tail] = splitTail(items[items.length - 1][1]);
  items[items.length - 1][1] = lastBody;

  const bullet = depth === 0 ? BULLET : SUB_BULLET;
  const lines: string[] = lead ? [lead] : [];
  for (const [label, body] of items) {
    const rendered = listify(cleanItem(body), depth + 1);
    const nl = rendered.indexOf("\n");
    const first = nl === -1 ? rendered : rendered.slice(0, nl);
    lines.push(`${INDENT.repeat(depth)}${bullet} **${label}** ${first}`.trimEnd());
    if (nl !== -1) lines.push(rendered.slice(nl + 1));
  }
  if (tail) lines.push(tail);
  return lines.join("\n");
}

/** Convert inline run-on enumerations into an indented bullet tree. */
export function listify(text: string, depth = 0): string {
  if (!text || depth > 3) return text;
  for (const finder of [findAssertionReason, findStatements, findEnumeration]) {
    const matches = finder(text);
    if (matches.length >= 2) return render(text, matches, depth);
  }
  return text;
}

/** `"(A) foo (B) bar"` → `[["A","foo"], ["B","bar"]]`. */
export function splitOptions(text: string): [string, string][] {
  const matches = findEnumeration(text);
  if (matches.length >= 2 && /^\([A-Za-z]\)$/.test(matches[0][2])) {
    return matches.map(([, end, label], k) => {
      const stop = k + 1 < matches.length ? matches[k + 1][0] : text.length;
      return [label.slice(1, -1).toUpperCase(), cleanItem(text.slice(end, stop))];
    });
  }
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  return lines.map((line, i) => [String.fromCharCode(65 + i), line.replace(/^\(?[A-Da-d][.)]\s+/, "")]);
}
