import {
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
} from "./symbols.js";

export const MODE_PRESERVE_KATEX = "katex" as const;
export const MODE_UNICODE_NATIVE = "unicode" as const;
export type Mode = typeof MODE_PRESERVE_KATEX | typeof MODE_UNICODE_NATIVE;

const MATH_SOURCE = String.raw`(?<!\\)\$\$([\s\S]+?)(?<!\\)\$\$|(?<!\\)\$(?!\s)([^$\n]+?)(?<![\s\\])\$(?!\d)`;
export const mathRegex = (): RegExp => new RegExp(MATH_SOURCE, "g");

const DOUBLE_ESCAPE = /\\\\(?=[A-Za-z()])/g;
const OPERATOR_CHARS = new Set("+-−±∓×÷·/=<>≤≥≠≈,;:→←⇌↔∪∩");
const SCRIPT_CHARS = new Set([...Object.values(SUPERSCRIPTS), ...Object.values(SUBSCRIPTS)]);
const isLetter = (c: string | undefined): boolean => !!c && /[A-Za-z]/.test(c);

const TEXT_COMMANDS = new Set([
  "text", "textrm", "textit", "textnormal", "textsf", "texttt", "mbox", "mathrm", "mathit",
  "mathsf", "mathtt", "operatorname", "mathcal", "mathscr", "mathfrak", "textup", "emph", "hbox",
]);
const BOLD_COMMANDS = new Set(["mathbf", "textbf", "boldsymbol", "bm", "pmb"]);
const FRAC_COMMANDS = new Set(["frac", "dfrac", "tfrac", "cfrac"]);
const ARG_COMMANDS = new Set([
  ...TEXT_COMMANDS, ...BOLD_COMMANDS, ...FRAC_COMMANDS, ...Object.keys(ACCENTS),
  "sqrt", "ce", "pu", "mathbb", "binom", "dbinom", "tbinom", "boxed", "xrightarrow", "xleftarrow",
  "overset", "underset", "stackrel", "overbrace", "underbrace", "textcolor", "pmod",
]);

export interface MathSpan {
  start: number;
  end: number;
  content: string;
  display: boolean;
}

// ---------------------------------------------------------------- normalize

export function balanceBraces(expr: string): string {
  let out = "";
  let depth = 0;
  for (let i = 0; i < expr.length; i++) {
    const c = expr[i];
    if (c === "\\" && i + 1 < expr.length) {
      out += expr.slice(i, i + 2);
      i++;
      continue;
    }
    if (c === "{") depth++;
    else if (c === "}") {
      if (depth === 0) continue;
      depth--;
    }
    out += c;
  }
  return out + "}".repeat(depth);
}

function closeDollars(text: string): string {
  if ((text.match(/(?<!\\)\$\$/g) ?? []).length % 2) text += "$$";
  const singles = text.replace(/(?<!\\)\$\$/g, "");
  const positions = [...singles.matchAll(/(?<!\\)\$/g)].map((m) => m.index ?? 0);
  if (positions.length % 2) {
    const tail = singles.slice(positions[positions.length - 1] + 1);
    if (/\\[A-Za-z]|[\^_]/.test(tail)) text = text.trimEnd() + "$";
  }
  return text;
}

/** Repair double-escaping, `\( \)`/`\[ \]` delimiters, unclosed `$` and unbalanced braces. */
export function normalize(text: string): string {
  if (!text) return "";
  let t = text.replace(/\r\n/g, "\n").replace(DOUBLE_ESCAPE, "\\");
  t = t.replace(/\\\[([\s\S]+?)\\\]/g, (_m, a: string) => `$$${a}$$`);
  t = t.replace(/\\\(([\s\S]+?)\\\)/g, (_m, a: string) => `$${a}$`);
  t = closeDollars(t);
  return t.replace(mathRegex(), (_m, d?: string, i?: string) =>
    d !== undefined ? `$$${balanceBraces(d)}$$` : `$${balanceBraces(i ?? "")}$`,
  );
}

export function findMath(text: string): MathSpan[] {
  return [...text.matchAll(mathRegex())].map((m) => ({
    start: m.index ?? 0,
    end: (m.index ?? 0) + m[0].length,
    content: m[1] ?? m[2] ?? "",
    display: m[1] !== undefined,
  }));
}

// ------------------------------------------------------------------ reader

function readGroup(s: string, i: number): [string, number] {
  let depth = 0;
  for (let j = i; j < s.length; j++) {
    const c = s[j];
    if (c === "\\") {
      j++;
      continue;
    }
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return [s.slice(i + 1, j), j + 1];
    }
  }
  return [s.slice(i + 1), s.length];
}

function readArg(s: string, i: number): [string, number] {
  while (i < s.length && s[i] === " ") i++;
  if (i >= s.length) return ["", i];
  const c = s[i];
  if (c === "{") return readGroup(s, i);
  if (c === "\\") {
    let j = i + 1;
    if (isLetter(s[j])) {
      while (isLetter(s[j])) j++;
      return [s.slice(i, j), j];
    }
    return [s.slice(i, j + 1), j + 1];
  }
  return [c, i + 1];
}

function readOptional(s: string, i: number): [string | null, number] {
  let j = i;
  while (j < s.length && s[j] === " ") j++;
  if (s[j] !== "[") return [null, i];
  let depth = 0;
  for (let k = j; k < s.length; k++) {
    if (s[k] === "[") depth++;
    else if (s[k] === "]") {
      depth--;
      if (depth === 0) return [s.slice(j + 1, k), k + 1];
    }
  }
  return [null, i];
}

// ---------------------------------------------------------------- helpers

const mapAll = (text: string, table: Record<string, string>): string | null => {
  const chars = Array.from(text);
  return chars.every((c) => c in table) ? chars.map((c) => table[c]).join("") : null;
};
export const toSuperscript = (t: string): string | null => mapAll(t, SUPERSCRIPTS);
export const toSubscript = (t: string): string | null => mapAll(t, SUBSCRIPTS);

function script(text: string, sup: boolean): string {
  const t = text.trim();
  if (!t) return "";
  if (sup && (t === "∘" || t === "°")) return "°";
  const mapped = sup ? toSuperscript(t) : toSubscript(t);
  if (mapped !== null) return mapped;
  if (!sup && t.includes("→")) return ` (${t})`;
  const wrapped = Array.from(t).length === 1 ? t : `(${t})`;
  return (sup ? "^" : "_") + wrapped;
}

const isLooseAtomic = (text: string): boolean => {
  const t = text.trim();
  if (!t) return false;
  if (t.startsWith("(") && t.endsWith(")")) {
    let depth = 0;
    let balanced = true;
    for (let idx = 0; idx < t.length; idx++) {
      if (t[idx] === "(") depth++;
      else if (t[idx] === ")") {
        depth--;
        if (depth === 0 && idx < t.length - 1) {
          balanced = false;
          break;
        }
      }
    }
    if (balanced && depth === 0) return true;
  }
  if (/^(\w+|\([^)]+\))(\([^)]+\))+$/.test(t)) return true;
  if (/^[∂dΔ]\w*(?:[²³ⁿ])?$/.test(t)) return true;
  return !Array.from(t).some((c) => /\s/.test(c) || OPERATOR_CHARS.has(c));
};

const isStrictAtomic = (text: string): boolean => {
  const t = text.trim();
  if (/^\d+(?:\.\d+)?$/.test(t)) return true;
  if (/^[d∂Δ][a-zA-Z](?:[²³ⁿ])?$/.test(t)) return true;
  if (t.length === 1 && !OPERATOR_CHARS.has(t)) return true;
  const chars = Array.from(t);
  return chars.length >= 1 && !OPERATOR_CHARS.has(chars[0]) && chars.slice(1).every((c) => SCRIPT_CHARS.has(c));
};

function fraction(numRaw: string, denRaw: string): string {
  const num = numRaw.trim();
  const den = denRaw.trim();
  if (/^\d+$/.test(num) && /^\d+$/.test(den)) {
    return VULGAR_FRACTIONS[`${num}/${den}`] ?? `${toSuperscript(num)}⁄${toSubscript(den)}`;
  }
  const left = isLooseAtomic(num) ? num : `(${num})`;
  const right = isStrictAtomic(den) ? den : `(${den})`;
  return `${left}/${right}`;
}

function sqrt(index: string | null, radicandRaw: string): string {
  const radicand = radicandRaw.trim();
  const idx = index?.trim() ?? "";
  let root = "√";
  if (idx === "3") root = "∛";
  else if (idx === "4") root = "∜";
  else if (idx && idx !== "2") root = (toSuperscript(idx) ?? `(${idx})`) + "√";
  return root + (isLooseAtomic(radicand) ? radicand : `(${radicand})`);
}

function bold(text: string): string {
  return Array.from(text)
    .map((c) => {
      const code = c.codePointAt(0) ?? 0;
      if (c >= "A" && c <= "Z") return String.fromCodePoint(0x1d400 + code - 65);
      if (c >= "a" && c <= "z") return String.fromCodePoint(0x1d41a + code - 97);
      if (c >= "0" && c <= "9") return String.fromCodePoint(0x1d7ce + code - 48);
      return c;
    })
    .join("");
}

function accent(text: string, mark: string, name = ""): string {
  if (!text) return "";
  if (name === "hat") {
    if (text === "i") return "î";
    if (text === "j") return "ĵ";
    if (text === "k") return "k̂";
  }
  if (["\u0305", "\u0332", "\u0338"].includes(mark)) return Array.from(text).map((c) => c + mark).join("");
  return text + mark;
}

function chem(arg: string): string {
  let t = arg;
  t = t.replace(/\s*[.*]\s*(?=\d*H2O|\d*[A-Z])/g, " · ");
  t = t.replace(/->\[([^\]]+)\]/g, (_m, c: string) => ` —${c.replace(/\\Delta/g, "Δ")}→ `);
  t = t
    .replace(/<=>/g, "\\rightleftharpoons ")
    .replace(/<->/g, "\\leftrightarrow ")
    .replace(/->/g, "\\to ")
    .replace(/<-/g, "\\gets ");
  t = t.replace(/(?<=[A-Za-z)\]])(\d+)/g, (_m, d: string) => `_{${d}}`);
  t = t.replace(/(?<=[A-Za-z)\]}])(\d*[+-])(?=\s|$|[+→⇌])/g, (_m, c: string) => `^{${c}}`);
  return convert(t, true);
}

function environment(env: string, bodyRaw: string): string {
  let base = env.replace(/\*$/, "");
  let body = bodyRaw;
  if (base === "array") {
    body = body.slice(readArg(body, 0)[1]);
    base = "matrix";
  }
  const rows = body.split(/\\\\(?:\[[^\]]*\])?/).filter((r) => r.trim());
  const cells = rows.map((r) => r.split(/(?<!\\)&/).map((c) => convert(c, true).trim()));
  const delims = MATRIX_DELIMS[base];
  if (delims) return delims[0] + cells.map((r) => r.join(", ")).join("; ") + delims[1];
  if (["cases", "dcases", "rcases"].includes(base)) {
    const formattedRows = cells.map((row) => {
      if (!row.length) return "";
      if (row.length === 1) return row[0];
      const exprPart = row[0].trim();
      const condPart = row.slice(1).join(" ").trim();
      if (exprPart.endsWith(",") || condPart.startsWith("if ") || condPart.startsWith("for ")) {
        return `${exprPart}  ${condPart}`.trim();
      }
      return `${exprPart},  ${condPart}`.trim();
    }).filter(Boolean);
    return "{ " + formattedRows.join("; ") + " }";
  }
  return cells.map((r) => r.filter(Boolean).join(" ")).join("\n");
}

function findEnvEnd(s: string, j: number, env: string): [string, number] {
  const beginTok = `\\begin{${env}}`;
  const endTok = `\\end{${env}}`;
  let depth = 1;
  let k = j;
  for (;;) {
    const nb = s.indexOf(beginTok, k);
    const ne = s.indexOf(endTok, k);
    if (ne === -1) return [s.slice(j), s.length];
    if (nb !== -1 && nb < ne) {
      depth++;
      k = nb + beginTok.length;
      continue;
    }
    depth--;
    if (depth === 0) return [s.slice(j, ne), ne + endTok.length];
    k = ne + endTok.length;
  }
}

function command(name: string, s: string, j0: number, inMath = true): [string, number] {
  let j = j0;
  let a: string;
  let b: string;
  if (FRAC_COMMANDS.has(name)) {
    [a, j] = readArg(s, j);
    [b, j] = readArg(s, j);
    return [fraction(convert(a, inMath), convert(b, inMath)), j];
  }
  if (["binom", "dbinom", "tbinom"].includes(name)) {
    [a, j] = readArg(s, j);
    [b, j] = readArg(s, j);
    return [`C(${convert(a, inMath).trim()}, ${convert(b, inMath).trim()})`, j];
  }
  if (name === "sqrt") {
    let idx: string | null;
    [idx, j] = readOptional(s, j);
    [a, j] = readArg(s, j);
    return [sqrt(idx !== null ? convert(idx, inMath) : null, convert(a, inMath)), j];
  }
  if (TEXT_COMMANDS.has(name)) {
    [a, j] = readArg(s, j);
    return [convert(a, inMath), j];
  }
  if (BOLD_COMMANDS.has(name)) {
    [a, j] = readArg(s, j);
    return [bold(convert(a, inMath)), j];
  }
  if (name === "mathbb") {
    [a, j] = readArg(s, j);
    return [Array.from(a.trim()).map((c) => BLACKBOARD[c] ?? c).join(""), j];
  }
  if (name in ACCENTS) {
    [a, j] = readArg(s, j);
    return [accent(convert(a, inMath).trim(), ACCENTS[name], name), j];
  }
  if (name === "ce" || name === "pu") {
    [a, j] = readArg(s, j);
    return [chem(a), j];
  }
  if (name === "xrightarrow" || name === "xleftarrow") {
    [, j] = readOptional(s, j);
    [a, j] = readArg(s, j);
    const label = convert(a, inMath).trim();
    const arrow = name === "xrightarrow" ? "→" : "←";
    return [label ? ` —${label}${arrow} ` : ` ${arrow} `, j];
  }
  if (["overset", "stackrel", "underset"].includes(name)) {
    [a, j] = readArg(s, j);
    [b, j] = readArg(s, j);
    const top = convert(a, inMath).trim();
    const base = convert(b, inMath).trim();
    if (["→", "←", "⇌", "⟶", "="].includes(base)) return [` —${top}${base} `, j];
    return [base + script(top, name !== "underset"), j];
  }
  if (["overbrace", "underbrace", "boxed"].includes(name)) {
    [a, j] = readArg(s, j);
    return [name === "boxed" ? `[${convert(a, inMath)}]` : convert(a, inMath), j];
  }
  if (name === "textcolor") {
    [, j] = readArg(s, j);
    [a, j] = readArg(s, j);
    return [convert(a, inMath), j];
  }
  if (name === "pmod") {
    [a, j] = readArg(s, j);
    return [` (mod ${convert(a, inMath).trim()})`, j];
  }
  if (name === "begin") {
    let env: string;
    let body: string;
    [env, j] = readArg(s, j);
    [body, j] = findEnvEnd(s, j, env);
    return [environment(env, body), j];
  }
  if (name === "end" || IGNORED_WITH_ARG.has(name)) {
    [, j] = readArg(s, j);
    return ["", j];
  }
  if (IGNORED.has(name)) {
    if (["left", "right", "middle"].includes(name) || /^big|^Big/.test(name)) {
      while (j < s.length && s[j] === " ") j++;
      if (j < s.length && s[j] === ".") j++;
    }
    return ["", j];
  }
  if (name === "bmod" || name === "mod") return [" mod ", j];
  if (name === "partial") {
    if (inMath && s[j] === " " && isLetter(s[j + 1])) j++;
    return ["∂", j];
  }
  if (name === "Delta") {
    if (inMath && s[j] === " " && isLetter(s[j + 1]) && (/[A-Z]/.test(s[j + 1]) || !isLetter(s[j + 2]))) j++;
    return ["Δ", j];
  }
  if (name === "nabla") {
    if (inMath && s[j] === " " && isLetter(s[j + 1]) && !isLetter(s[j + 2])) j++;
    return ["∇", j];
  }
  if (FUNCTIONS.has(name)) return [name, j];
  if (name in GREEK) {
    if (inMath && s[j] === " " && isLetter(s[j + 1]) && !isLetter(s[j + 2])) j++;
    return [GREEK[name], j];
  }
  if (name in SYMBOLS) return [SYMBOLS[name], j];
  return [name, j];
}

function convert(s: string, inMath = true): string {
  let out = "";
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === "\\") {
      if (isLetter(s[i + 1])) {
        let j = i + 1;
        while (isLetter(s[j])) j++;
        const [text, next] = command(s.slice(i + 1, j), s, j, inMath);
        out += text;
        i = next;
        continue;
      }
      if (i + 1 < s.length) {
        out += CONTROL_SYMBOLS[s[i + 1]] ?? s[i + 1];
        i += 2;
        continue;
      }
      i++;
      continue;
    }
    if (c === "^" || c === "_") {
      const [arg, next] = readArg(s, i + 1);
      out += script(convert(arg, inMath), c === "^");
      i = next;
      continue;
    }
    if (c === "{") {
      const [content, next] = readGroup(s, i);
      out += convert(content, inMath);
      i = next;
      continue;
    }
    if (c === "}") {
      i++;
      continue;
    }
    out += c === "~" ? " " : c === "*" ? "∗" : c === "'" ? "′" : c;
    i++;
  }
  return out;
}

function formatMathSpacing(s: string): string {
  let res = s
    .replace(/\(\s+/g, "(")
    .replace(/\s+\)/g, ")")
    .replace(/\[\s+/g, "[")
    .replace(/\s+\]/g, "]")
    .replace(/\{\s+/g, "{")
    .replace(/\s+\}/g, "}")
    .replace(/\s*,\s*/g, ", ")
    .replace(/\s*;\s*/g, "; ");

  const relPat = /(=|<|>|≤|≥|≠|≈|≡|∝|∈|∉|⊂|⊆|⊇|⊃|∪|∩|⇌|→|←|⇒|⟺)/g;
  res = res.replace(relPat, " $1 ").replace(/[ \t]{2,}/g, " ");

  const binPat = /([A-Za-z0-9)\]\u0080-\uffff])\s*([+±∓×·÷]|(?<![=<>≤≥≠≈∈(])[−\-])\s*([A-Za-z0-9(\[\u0080-\uffff])/g;
  res = res.replace(binPat, "$1 $2 $3").replace(binPat, "$1 $2 $3");

  res = res.replace(
    /\b(sin|cos|tan|cot|sec|csc|sinh|cosh|tanh|ln|log|exp|det|lim)([²³ⁿ])?\s*([A-Za-zα-ωΑ-Ω])\b/g,
    (_m, fn: string, pow: string | undefined, arg: string) => `${fn}${pow ?? ""} ${arg}`,
  );

  return res.replace(/[ \t\u2009]{2,}/g, " ").trim();
}

/** Transliterate a LaTeX math expression (without `$`) to Unicode. */
export function latexToUnicode(expr: string): string {
  const e = balanceBraces(expr.replace(DOUBLE_ESCAPE, "\\"))
    .replace(/<=>/g, "⇌")
    .replace(/<->/g, "↔")
    .replace(/->/g, "→");
  const out = formatMathSpacing(convert(e, true));
  return out
    .split("\n")
    .map((l) => l.trim())
    .join("\n")
    .trim();
}

/** Heuristic: would this formula be clearer as an image? */
export function isComplex(expr: string): boolean {
  if (/\\begin\{/.test(expr)) return true;
  if (/\\sqrt\s*(\[[^\]]*\])?\s*\{[^}]*\\[dt]?frac/.test(expr)) return true;
  if (/\\(?:overset|underset|stackrel|overbrace|underbrace)/.test(expr)) return true;
  const u = latexToUnicode(expr);
  if (/\)\/|\/\(/.test(u)) return true;
  if (/(?:\^|_)\([^)]{5,}\)/.test(u)) return true;
  if ((expr.match(/\\[dtc]?frac/g) ?? []).length >= 2 && u.includes("/")) return true;
  return false;
}

function convertBare(text: string): string {
  let out = "";
  let i = 0;
  for (const m of text.matchAll(/\\([A-Za-z]+)/g)) {
    const start = m.index ?? 0;
    if (start < i) continue;
    const name = m[1];
    if (name in GREEK || name in SYMBOLS || ARG_COMMANDS.has(name)) {
      out += text.slice(i, start);
      const [converted, next] = command(name, text, start + m[0].length, false);
      out += converted;
      i = next;
    }
  }
  out += text.slice(i);
  return out
    .replace(/(?<=[A-Za-z0-9)\]])\^(\{[^{}\n]*\}|[0-9]+|[a-z](?![a-z])|[∘°′*])/g, (m, g: string) => {
      const raw = g.replace(/[{}]/g, "");
      if (raw === "∘" || raw === "°") return "°";
      return toSuperscript(raw) ?? m;
    })
    .replace(/(?<=[A-Za-z)\]])_(\{[^{}\n]*\}|\d+)(?![A-Za-z_])/g, (m, g: string) =>
      toSubscript(g.replace(/[{}]/g, "")) ?? m,
    );
}

export interface FormatTextOptions {
  /** When given, complex formulas are pushed here and replaced with `[eq. N]`. */
  collect?: string[];
  /** In Unicode mode, also convert stray LaTeX outside `$` delimiters. Default true. */
  bareCommands?: boolean;
}

/** Format every math span in `text` for Discord. */
export function formatText(text: string, mode: Mode = MODE_UNICODE_NATIVE, options: FormatTextOptions = {}): string {
  const { collect, bareCommands = true } = options;
  const t = normalize(text);
  const plain = (p: string) => (mode === MODE_UNICODE_NATIVE && bareCommands ? convertBare(p) : p);

  let out = "";
  let last = 0;
  for (const m of t.matchAll(mathRegex())) {
    const start = m.index ?? 0;
    out += plain(t.slice(last, start));
    const display = m[1] !== undefined;
    const expr = (m[1] ?? m[2] ?? "").trim();
    if (collect && isComplex(expr)) {
      collect.push(expr);
      const marker = `\`[eq. ${collect.length}]\``;
      out += display ? `\n${marker}\n` : marker;
    } else if (mode === MODE_PRESERVE_KATEX) {
      out += display ? `$$${expr}$$` : `$${expr}$`;
    } else {
      const u = latexToUnicode(expr);
      out += display ? `\n${u}\n` : u;
    }
    last = start + m[0].length;
  }
  out += plain(t.slice(last));
  return out.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}
