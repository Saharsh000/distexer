import { listify, splitOptions } from "./lists.js";
import { HEADER_RE, formatMatch, formatMatchOptions, parseMapping, parseMatch } from "./matching.js";
import { REGIONAL_INDICATORS } from "./symbols.js";
import { MODE_UNICODE_NATIVE, type Mode, formatText, normalize } from "./text.js";

export type QType = "single" | "multiple" | "integer" | "numeric" | "match" | "truefalse";
export type OptionsInput = string | string[] | [string, string][] | Record<string, string> | null | undefined;

export const FOOTERS: Record<QType, string> = {
  single: "🎯 Single correct • choose ONE option",
  multiple: "✅ Multiple correct • choose ALL that apply",
  integer: "🔢 Integer type • reply with a whole number",
  numeric: "🔢 Numerical • reply with a number",
  match: "🔗 Match the following • choose the correct mapping",
  truefalse: "⚖️ True or False",
};

export interface QuestionLayout {
  body: string;
  options: string[];
  formulas: string[];
  footer: string;
  qType: QType;
}

export const layoutText = (l: QuestionLayout): string =>
  l.options.length ? `${l.body}\n\n${l.options.join("\n")}` : l.body;

export function badge(label: string): string {
  const upper = label.trim().toUpperCase();
  return upper.length === 1 && REGIONAL_INDICATORS[upper] ? REGIONAL_INDICATORS[upper] : `\`${label}\``;
}

function coerceOptions(options: OptionsInput): [string, string][] {
  if (options == null) return [];
  if (typeof options === "string") return splitOptions(options);
  if (!Array.isArray(options)) return Object.entries(options);
  return (options as (string | [string, string])[]).map((option, i) => {
    const def = String.fromCharCode(65 + i);
    if (Array.isArray(option)) return [String(option[0]), String(option[1])];
    const m = /^\s*\(?([A-Za-z])[).:]\s+/.exec(option);
    return [def, m && m[1].toUpperCase() === def ? option.slice(m[0].length) : option];
  });
}

/** Normalize + listify + format math for any plain Discord message. */
export const formatMessage = (text: string, mode: Mode = MODE_UNICODE_NATIVE): string =>
  formatText(listify(normalize(text)), mode);

export interface BuildQuestionOptions {
  qType?: QType;
  mode?: Mode;
  renderComplexMath?: boolean;
}

/** Turn a raw (LLM-generated) question into a clean QuestionLayout. */
export function buildQuestion(question: string, options?: OptionsInput, opts: BuildQuestionOptions = {}): QuestionLayout {
  let qType: QType = opts.qType ?? "single";
  const mode = opts.mode ?? MODE_UNICODE_NATIVE;
  const renderComplexMath = opts.renderComplexMath ?? true;
  const raw = normalize(question);

  let structured: string | null = null;
  if (qType === "match" || [...raw.matchAll(HEADER_RE)].length >= 2) {
    const match = parseMatch(raw);
    if (match) {
      structured = formatMatch(match);
      qType = "match";
    }
  }
  structured ??= listify(raw);

  const formulas: string[] = [];
  let body = formatText(structured, mode, { collect: renderComplexMath ? formulas : undefined });
  if (formulas.length === 1) body = body.replace("`[eq. 1]`", "`[equation ↓]`");

  const optionLines = coerceOptions(options).map(([label, text]) => {
    const t = normalize(text);
    if (qType === "match" && parseMapping(t).length) {
      return `${badge(label)} (${label.toUpperCase()})  ${formatMatchOptions(t)}`;
    }
    return `${badge(label)}  ${formatText(t, mode)}`;
  });

  return { body, options: optionLines, formulas, footer: FOOTERS[qType], qType };
}
