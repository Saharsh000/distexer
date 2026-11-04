import { type BuildQuestionOptions, type OptionsInput, type QuestionLayout, buildQuestion, layoutText } from "./core.js";
import { MathRenderer, RenderError } from "./renderer.js";
import { type Theme, getTheme } from "./themes.js";

/** Plain objects accepted directly by discord.js (`channel.send({ embeds, files })`) – no hard dependency. */
export interface EmbedData {
  title?: string;
  description: string;
  color: number;
  url?: string;
  footer?: { text: string };
  image?: { url: string };
}

export interface FileData {
  attachment: Buffer;
  name: string;
}

export interface QuestionMessage {
  embeds: [EmbedData];
  files: FileData[];
  layout: QuestionLayout;
}

export interface CreateQuestionEmbedOptions extends BuildQuestionOptions {
  title: string;
  question: string;
  options?: OptionsInput;
  theme?: string | Theme;
  renderer?: MathRenderer;
  color?: number;
  footer?: string;
  url?: string;
  filename?: string;
}

const renderers = new Map<string, MathRenderer>();

export function rendererFor(theme?: string | Theme): MathRenderer {
  const t = getTheme(theme);
  let r = renderers.get(t.name);
  if (!r) {
    r = new MathRenderer({ textColor: t.textColor, background: t.background });
    renderers.set(t.name, r);
  }
  return r;
}

const truncate = (s: string, n: number) => (s.length <= n ? s : s.slice(0, n - 1) + "…");

/**
 * Build a ready-to-send question message.
 *
 * ```ts
 * const msg = await createQuestionEmbed({ title, question, options: ["A", "B", "C", "D"] });
 * await interaction.reply({ embeds: msg.embeds, files: msg.files });
 * ```
 */
export async function createQuestionEmbed(opts: CreateQuestionEmbedOptions): Promise<QuestionMessage> {
  const theme = getTheme(opts.theme);
  const filename = opts.filename ?? "formula.png";
  const build = (renderComplexMath: boolean) =>
    buildQuestion(opts.question, opts.options, { qType: opts.qType, mode: opts.mode, renderComplexMath });

  let layout = build(opts.renderComplexMath ?? true);
  let png: Buffer | null = null;
  if (layout.formulas.length) {
    try {
      png = await (opts.renderer ?? rendererFor(theme)).renderMany(layout.formulas);
    } catch (err) {
      if (!(err instanceof RenderError)) throw err;
      layout = build(false);
    }
  }

  const embed: EmbedData = {
    title: opts.title ? truncate(opts.title, 256) : undefined,
    description: truncate(layoutText(layout), 4096),
    color: opts.color ?? theme.embedColor,
    url: opts.url,
  };
  const footer = opts.footer ?? layout.footer;
  if (footer) embed.footer = { text: footer };
  const files: FileData[] = [];
  if (png) {
    files.push({ attachment: png, name: filename });
    embed.image = { url: `attachment://${filename}` };
  }
  return { embeds: [embed], files, layout };
}

/** Render a single formula as a discord.js-compatible file object. */
export async function renderFormula(expr: string, filename = "formula.png", theme?: string | Theme): Promise<FileData> {
  return { attachment: await rendererFor(theme).render(expr), name: filename };
}
