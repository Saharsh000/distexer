# distexer

**Discord + TeX: the headless STEM and math presentation engine for Discord bots.**

Discord doesn't render LaTeX, so when an LLM or trivia bot sends `$\frac{h}{p}$` or `$\alpha$-amino acid`, users see raw code. distexer turns that into readable output:

| Input (what your LLM sends) | distexer output |
|---|---|
| `The $\alpha$-particle, $E = mc^2$` | The α-particle, E = mc² |
| `$\ce{N2 + 3H2 <=> 2NH3}$` | N₂ + 3H₂ ⇌ 2NH₃ |
| `$\frac{1}{2}$`, `$\frac{h}{p}$`, `$25^\circ C$` | ½, h/p, 25° C |
| `$\frac{-b \pm \sqrt{b^2-4ac}}{2a}$` | a **real fraction bar** rendered as an embed image (or `(-b ± √(b² - 4ac))/(2a)` as text) |
| `(i) A → B, (ii) C → D, (iii) …` | a clean, indented bullet list |
| `Match List-I … List-II …` | `📋 LIST — I` / `📋 LIST — II` sections and `🇦 (A)  P ➔ 1  •  Q ➔ 2` options |

It doesn't use headless browsers (no Playwright or Puppeteer). Text output is pure string processing. Formula images use offline matplotlib (Python) or MathJax + resvg (Node), with the CodeCogs and QuickLaTeX CDNs as fallbacks.

```
distexer/
├── python/        → pip install distexer      (discord.py)
├── typescript/    → npm i distexer            (discord.js)
├── docs/          → GITHUB_GUIDE.md (how to upload and publish)
└── .github/       → CI + automatic PyPI/npm publishing
```

---

## Python

```bash
pip install distexer               # text formatting only, no dependencies
pip install "distexer[render]"     # + offline formula images (matplotlib)
pip install "distexer[all]"        # + discord.py helpers
```

### Plain text

```python
import distexer

distexer.format_message(r"The \alpha-amino acid has $pK_a \approx 2.3$ and $\Delta G = \Delta H - T\Delta S$")
# 'The α-amino acid has pKₐ ≈ 2.3 and ΔG = ΔH - TΔS'

distexer.latex_to_unicode(r"\ce{CaCO3 -> CaO + CO2}")   # 'CaCO₃ → CaO + CO₂'
distexer.latex_to_unicode(r"\sqrt[3]{x} \leq \infty")    # '∛x ≤ ∞'

# Keep KaTeX for Vencord / BetterDiscord users:
distexer.format_text(r"$x^2$", mode=distexer.MODE_PRESERVE_KATEX)   # '$x^2$'
```

### Question embed in one line

```python
embed, file = await distexer.acreate_question_embed(
    title="Chemical Thermodynamics • JEE Advanced",
    question=raw_question,
    options=["...", "...", "...", "..."],   # list, dict, or "(A) .. (B) .." string
    q_type="single",                        # single | multiple | integer | numeric | match | truefalse
    theme="solid_dark",                     # discord_dark | discord_light | solid_dark | amoled | ...
    render_complex_math=True,               # complex formulas → embed image with real fraction bars
)
await channel.send(embed=embed, **({"file": file} if file else {}))
```

A synchronous `create_question_embed(...)` is also available. In bot code, use the `a`-prefixed versions so a network fallback never blocks your event loop.

When `render_complex_math=True`, formulas that look bad as text (compound fractions, matrices, radicals containing fractions) are rendered into a **single PNG** (Discord embeds hold one image). The text shows `` `[equation ↓]` `` or `` `[eq. 1]` ``, `` `[eq. 2]` `` markers that match the labels in the image. Simple formulas stay as Unicode text. If every renderer fails, it falls back to a text-only embed.

### Images only

```python
png = distexer.render_png(r"\int_0^\infty e^{-x^2}\,dx = \frac{\sqrt{\pi}}{2}")  # io.BytesIO
file = await distexer.arender_formula(r"\begin{bmatrix}1&2\\3&4\end{bmatrix}")   # discord.File
r = distexer.MathRenderer(dpi=250, background="#2B2D31", backend="matplotlib")
```

### Building blocks

| Module | Main functions |
|---|---|
| `distexer.formatters.text` | `normalize`, `format_text`, `latex_to_unicode`, `find_math`, `is_complex` |
| `distexer.formatters.lists` | `listify`, `split_options` |
| `distexer.formatters.matching` | `parse_match`, `build_match`, `format_match`, `format_match_options` |
| `distexer.renderer` | `MathRenderer`, `RenderConfig`, `render_png` |
| `distexer.discord` | `create_question_embed`, `acreate_question_embed`, `render_formula` |
| `distexer.core` | `build_question` → `QuestionLayout` (framework-agnostic, works for Slack, Telegram, and other platforms) |

See [`python/examples/trivia_bot.py`](python/examples/trivia_bot.py) for a complete slash-command bot.

---

## TypeScript / Node

```bash
npm i distexer
npm i mathjax-full @resvg/resvg-js   # optional: offline formula images
```

```ts
import { createQuestionEmbed, formatMessage, latexToUnicode } from "distexer";

formatMessage(String.raw`The $\alpha$-particle has $E = mc^2$`); // 'The α-particle has E = mc²'

const msg = await createQuestionEmbed({
  title: "Kinematics",
  question: raw,
  options: ["A", "B", "C", "D"],
  qType: "single",
  theme: "solid_dark",
});
await interaction.reply({ embeds: msg.embeds, files: msg.files }); // plain objects that discord.js accepts
```

There's no hard dependency on discord.js. See [`typescript/examples/bot.ts`](typescript/examples/bot.ts).

---

## Themes

| Theme | Image | Best for |
|---|---|---|
| `discord_dark` (default) | transparent, white text | dark mode only |
| `discord_light` | transparent, dark text | light mode only |
| `solid_dark` | `#2B2D31` card, white text | **both modes (recommended)** |
| `amoled` | black card, white text | AMOLED dark |

## What gets converted

Greek letters, operators (`\pm \times \cdot \leq \neq \approx \infty \partial \nabla`), arrows (`\to \Rightarrow \rightleftharpoons`), super- and subscripts, `\frac` (vulgar fractions like ½ where possible), `\sqrt[n]{}`, `\ce{}` chemistry, `\text`, `\mathrm`, `\mathbf` (𝐛𝐨𝐥𝐝), `\mathbb` (ℝ ℕ ℤ), accents (`\vec \hat \bar \dot`), matrices, `cases`, and `align`. It also repairs common LLM output problems: `\\frac` double-escaping, `\( \)` and `\[ \]` delimiters, unclosed `$`, and unbalanced braces. Money like `$5 and $10` is left alone.

## Development

```bash
cd python && pip install -e ".[dev]" && pytest
cd typescript && npm install && npm test
```

## License

MIT
