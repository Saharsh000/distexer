/**
 * Browser-free LaTeX → PNG rendering.
 *
 * Backends (tried in order with `backend: "auto"`):
 *  1. `mathjax`    – fully offline: MathJax (TeX → SVG) + resvg (SVG → PNG, Rust/WASM).
 *                    Optional deps: `npm i mathjax-full @resvg/resvg-js`
 *  2. `codecogs`   – CodeCogs LaTeX CDN.
 *  3. `quicklatex` – QuickLaTeX API (supports mhchem `\ce`).
 */

export type Backend = "auto" | "mathjax" | "codecogs" | "quicklatex";

export interface RenderConfig {
  dpi: number;
  textColor: string;
  /** `null` → transparent PNG */
  background: string | null;
  fontSize: number;
  backend: Backend;
  timeoutMs: number;
  cacheSize: number;
}

export const DEFAULT_RENDER_CONFIG: RenderConfig = {
  dpi: 200,
  textColor: "#FFFFFF",
  background: null,
  fontSize: 15,
  backend: "auto",
  timeoutMs: 8000,
  cacheSize: 256,
};

export class RenderError extends Error {
  override name = "RenderError";
}

const USER_AGENT = "distexer/0.1 (+https://github.com/Saharsh000/distexer)";
const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47];
const hex = (c: string) => c.replace(/^#/, "").toUpperCase();
const isPng = (b: Uint8Array) => PNG_SIGNATURE.every((v, i) => b[i] === v);

// Dynamic import through a variable so bundlers/TS don't require the optional deps.
const optionalImport = (name: string): Promise<any> => import(name);

let mathjaxPromise: Promise<{ toSvg: (tex: string) => string }> | null = null;

async function loadMathJax() {
  mathjaxPromise ??= (async () => {
    const [{ mathjax }, { TeX }, { SVG }, { liteAdaptor }, { RegisterHTMLHandler }, { AllPackages }] =
      await Promise.all([
        optionalImport("mathjax-full/js/mathjax.js"),
        optionalImport("mathjax-full/js/input/tex.js"),
        optionalImport("mathjax-full/js/output/svg.js"),
        optionalImport("mathjax-full/js/adaptors/liteAdaptor.js"),
        optionalImport("mathjax-full/js/handlers/html.js"),
        optionalImport("mathjax-full/js/input/tex/AllPackages.js"),
      ]);
    const adaptor = liteAdaptor();
    RegisterHTMLHandler(adaptor);
    const doc = mathjax.document("", {
      InputJax: new TeX({ packages: AllPackages }),
      OutputJax: new SVG({ fontCache: "none" }),
    });
    return {
      toSvg: (tex: string) => adaptor.innerHTML(doc.convert(tex, { display: true })) as string,
    };
  })();
  try {
    return await mathjaxPromise;
  } catch (err) {
    mathjaxPromise = null;
    throw err;
  }
}

export class MathRenderer {
  readonly config: RenderConfig;
  private cache = new Map<string, Buffer>();

  constructor(config: Partial<RenderConfig> = {}) {
    this.config = { ...DEFAULT_RENDER_CONFIG, ...config };
  }

  /** Render one formula to a PNG Buffer. */
  render(expr: string): Promise<Buffer> {
    return this.renderMany([expr], false);
  }

  /** Render several formulas stacked into ONE labelled PNG (embeds hold a single image). */
  async renderMany(formulasRaw: string[], labels?: boolean): Promise<Buffer> {
    const formulas = formulasRaw.map((f) => f.trim().replace(/^\$+|\$+$/g, "").trim()).filter(Boolean);
    if (!formulas.length) throw new RenderError("Nothing to render");
    const useLabels = labels ?? formulas.length > 1;
    const key = JSON.stringify([formulas, useLabels, this.config]);
    const cached = this.cache.get(key);
    if (cached) {
      this.cache.delete(key);
      this.cache.set(key, cached);
      return cached;
    }

    const backends: Exclude<Backend, "auto">[] =
      this.config.backend === "auto" ? ["mathjax", "codecogs", "quicklatex"] : [this.config.backend];
    const errors: string[] = [];
    for (const backend of backends) {
      try {
        const png = await this[backend](this.document(formulas, useLabels));
        this.cache.set(key, png);
        while (this.cache.size > this.config.cacheSize) this.cache.delete(this.cache.keys().next().value!);
        return png;
      } catch (err) {
        errors.push(`${backend}: ${(err as Error).message}`);
      }
    }
    throw new RenderError(`All render backends failed → ${errors.join(" | ")}`);
  }

  private document(formulas: string[], labels: boolean): string {
    if (formulas.length === 1 && !labels) return `\\displaystyle ${formulas[0]}`;
    const rows = formulas.map((f, i) => (labels ? `\\text{(${i + 1})}\\quad ` : "") + `\\displaystyle ${f}`);
    return `\\begin{array}{l} ${rows.join(" \\\\[10pt] ")} \\end{array}`;
  }

  private async fetchBytes(url: string, init: RequestInit = {}): Promise<Buffer> {
    const res = await fetch(url, {
      ...init,
      headers: { "User-Agent": USER_AGENT, ...(init.headers ?? {}) },
      signal: AbortSignal.timeout(this.config.timeoutMs),
    });
    if (!res.ok) throw new RenderError(`HTTP ${res.status}`);
    return Buffer.from(await res.arrayBuffer());
  }

  private async mathjax(tex: string): Promise<Buffer> {
    const [{ toSvg }, resvg] = await Promise.all([loadMathJax(), optionalImport("@resvg/resvg-js")]);
    const exPx = (this.config.fontSize * this.config.dpi) / 72 / 2; // 1ex ≈ half the font size
    const svg = toSvg(tex)
      .replace(/currentColor/g, this.config.textColor)
      .replace(/(width|height)="([\d.]+)ex"/g, (_m, attr: string, v: string) => `${attr}="${(+v * exPx).toFixed(2)}"`);
    const instance = new resvg.Resvg(svg, {
      background: this.config.background ?? "rgba(0,0,0,0)",
      fitTo: { mode: "original" },
      font: { loadSystemFonts: false },
    });
    return Buffer.from(instance.render().asPng());
  }

  private async codecogs(tex: string): Promise<Buffer> {
    const bg = this.config.background === null ? "\\bg{transparent}" : `\\bg{${hex(this.config.background)}}`;
    const latex = `\\dpi{${this.config.dpi}}${bg}\\fg{${hex(this.config.textColor)}} ${tex}`;
    const png = await this.fetchBytes(`https://latex.codecogs.com/png.image?${encodeURIComponent(latex)}`);
    if (!isPng(png)) throw new RenderError("CodeCogs did not return a PNG");
    return png;
  }

  private async quicklatex(tex: string): Promise<Buffer> {
    const body = new URLSearchParams({
      formula: tex,
      fsize: `${Math.max(12, Math.round((this.config.fontSize * this.config.dpi) / 110))}px`,
      fcolor: hex(this.config.textColor),
      bcolor: this.config.background ? hex(this.config.background) : "FFFFFF",
      mode: "0",
      out: "1",
      errors: "1",
      remhost: "quicklatex.com",
      preamble: "\\usepackage{amsmath}\\usepackage{amssymb}\\usepackage[version=4]{mhchem}",
    });
    const res = (
      await this.fetchBytes("https://quicklatex.com/latex3.f", {
        method: "POST",
        body,
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
    )
      .toString("utf8")
      .split(/\s+/);
    if (res[0] !== "0" || !res[1]) throw new RenderError(`QuickLaTeX error: ${res.slice(0, 12).join(" ")}`);
    const png = await this.fetchBytes(res[1]);
    if (!isPng(png)) throw new RenderError("QuickLaTeX did not return a PNG");
    return png;
  }
}

let defaultRenderer: MathRenderer | null = null;

/** Shortcut: `await renderPng("\\frac{a}{b}")` → PNG Buffer. */
export function renderPng(expr: string, config?: Partial<RenderConfig>): Promise<Buffer> {
  if (config) return new MathRenderer(config).render(expr);
  defaultRenderer ??= new MathRenderer();
  return defaultRenderer.render(expr);
}
