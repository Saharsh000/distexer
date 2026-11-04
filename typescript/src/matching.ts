import { cleanItem, splitTail } from "./lists.js";

export type Pair = [label: string, text: string];

export interface MatchQuestion {
  stem: string;
  listI: Pair[];
  listII: Pair[];
  tail: string;
  headerI: string;
  headerII: string;
}

export const HEADER_RE = /\b(List|Column|Col\.?)\s*[-–—]?\s*(II|I|1|2|A|B)\b/gi;
const ITEM_PAREN_RE = /\(\s*([A-Za-z]|\d{1,2}|[ivx]{1,4})\s*\)/g;
const ITEM_PLAIN_RE = /(?:^|(?<=[\s,;:]))([A-Z]|\d{1,2}|[ivx]{1,4})[.)](?=\s)/g;
const PAIR_RE =
  /\b([A-Za-z]|[ivxIVX]{1,4})\s*(?:->|-|–|—|→|➔|⟶|:|=|\bto\b)\s*([A-Za-z]|\d{1,2}|[ivxIVX]{1,4})\b/g;

const isFirst = (t: string) => ["I", "1", "A"].includes(t.toUpperCase());
const isSecond = (t: string) => ["II", "2", "B"].includes(t.toUpperCase());

function family(token: string): string {
  if (/^\d+$/.test(token)) return "num";
  if (["i", "ii", "iii", "iv", "v", "vi"].includes(token)) return "roman";
  return token === token.toUpperCase() ? "upper" : "lower";
}

function parseItems(segment: string): [Pair[], string] {
  let matches = [...segment.matchAll(ITEM_PAREN_RE)];
  if (matches.length < 2) matches = [...segment.matchAll(ITEM_PLAIN_RE)];
  if (matches.length < 2) {
    const parts = segment.split(/\n|;/).map((p) => p.trim()).filter((p) => p.replace(/[ :]/g, ""));
    return [parts.length >= 2 ? parts.map((p, i) => [String(i + 1), cleanItem(p)] as Pair) : [], ""];
  }
  const fam = family(matches[0][1]);
  const kept: RegExpMatchArray[] = [];
  let tailStart: number | null = null;
  for (const m of matches) {
    if (family(m[1]) !== fam) {
      tailStart = m.index ?? 0;
      break;
    }
    kept.push(m);
  }
  const items: Pair[] = kept.map((m, k) => {
    const stop = k + 1 < kept.length ? (kept[k + 1].index ?? 0) : (tailStart ?? segment.length);
    const label = fam === "num" ? m[1] : m[1].toUpperCase();
    return [label, segment.slice((m.index ?? 0) + m[0].length, stop)];
  });
  let tail = tailStart !== null ? segment.slice(tailStart).trim() : "";
  const [lastText, cue] = splitTail(items[items.length - 1][1]);
  items[items.length - 1][1] = lastText;
  tail = [cue, tail].filter(Boolean).join(" ");
  return [items.map(([l, t]) => [l, cleanItem(t)] as Pair), tail];
}

/** Parse "Match List-I with List-II …" text. Returns `null` if no two-list structure is found. */
export function parseMatch(text: string): MatchQuestion | null {
  const headers = [...text.matchAll(HEADER_RE)];
  const end = (m: RegExpMatchArray) => (m.index ?? 0) + m[0].length;
  let first = headers.find((h) => isFirst(h[2]));
  if (!first) return null;
  let second = headers.find((h) => (h.index ?? 0) > end(first!) && isSecond(h[2]));
  if (!second) return null;

  let stem = text.slice(0, first.index).trim().replace(/:$/, "");
  const later = headers.filter((h) => (h.index ?? 0) > end(second!));
  const between = text.slice(end(first), second.index);
  if (later.length && between.length < 40 && !/\(\s*([A-Za-z]|\d{1,2})\s*\)/.test(between)) {
    stem = text.slice(0, later[0].index).trim().replace(/:$/, "");
    first = later.find((h) => isFirst(h[2])) ?? first;
    second = later.find((h) => (h.index ?? 0) > end(first!) && isSecond(h[2])) ?? second;
  }

  const [left] = parseItems(text.slice(end(first), second.index));
  const [right, tail] = parseItems(text.slice(end(second)));
  if (!left.length || !right.length) return null;
  const kind = first[1].toUpperCase().startsWith("COL") ? "COLUMN" : "LIST";
  return { stem, listI: left, listII: right, tail, headerI: `${kind} — I`, headerII: `${kind} — II` };
}

type ItemsInput = string[] | Pair[] | Record<string, string>;

function coerce(items: ItemsInput, labels: string[]): Pair[] {
  if (!Array.isArray(items)) return Object.entries(items);
  return (items as (string | Pair)[]).map((item, i) =>
    Array.isArray(item) ? [String(item[0]), String(item[1])] : [labels[i] ?? String(i + 1), String(item)],
  );
}

/** Build a MatchQuestion from structured data instead of parsing. */
export function buildMatch(
  listI: ItemsInput,
  listII: ItemsInput,
  { stem = "Match List — I with List — II", tail = "" } = {},
): MatchQuestion {
  return {
    stem,
    listI: coerce(listI, [..."PQRSTUVW"]),
    listII: coerce(listII, Array.from({ length: 10 }, (_, i) => String(i + 1))),
    tail,
    headerI: "LIST — I",
    headerII: "LIST — II",
  };
}

export function formatMatch(q: MatchQuestion): string {
  const lines: string[] = [];
  if (q.stem) lines.push(q.stem, "");
  lines.push(`📋 **${q.headerI}**`, ...q.listI.map(([l, t]) => `\`[${l}]\` ${t}`));
  lines.push("", `📋 **${q.headerII}**`, ...q.listII.map(([l, t]) => `\`[${l}]\` ${t}`));
  if (q.tail) lines.push("", q.tail);
  return lines.join("\n");
}

/** `"P-1, Q-2"` → `[["P","1"],["Q","2"]]` */
export function parseMapping(option: string): Pair[] {
  const cleaned = option.replace(/\(\s*(\w{1,4})\s*\)/g, "$1");
  const pairs = [...cleaned.matchAll(PAIR_RE)].map((m) => [m[1].toUpperCase(), m[2]] as Pair);
  return pairs.length >= 2 ? pairs : [];
}

/** `"P-1, Q-2, R-3"` → `"P ➔ 1  •  Q ➔ 2  •  R ➔ 3"` */
export function formatMatchOptions(option: string): string {
  const pairs = parseMapping(option);
  return pairs.length ? pairs.map(([a, b]) => `${a} ➔ ${b}`).join("  •  ") : option.trim();
}
