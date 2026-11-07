import assert from "node:assert/strict";
import { test } from "node:test";
import { buildQuestion, formatText, latexToUnicode as u, listify } from "../dist/index.js";

test("symbols, scripts, fractions", () => {
  assert.equal(u(String.raw`\alpha + \beta \to \gamma`), "α + β → γ");
  assert.equal(u("H_2O"), "H₂O");
  assert.equal(u(String.raw`\frac{1}{2}`), "½");
  assert.equal(u(String.raw`\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}`), "(-b ± √(b² - 4ac))/(2a)");
  assert.equal(u(String.raw`\ce{2H2 + O2 -> 2H2O}`), "2H₂ + O₂ → 2H₂O");
});

test("formatText keeps money", () => {
  assert.equal(formatText("costs $5 and $10"), "costs $5 and $10");
});

test("listify roman", () => {
  const out = listify("Consider: (i) A + B → C, (ii) C → D + E, (iii) E → F. Which are redox?");
  assert.ok(out.includes("▸ **(ii)** C → D + E"));
  assert.ok(out.endsWith("Which are redox?"));
});

test("match layout", () => {
  const l = buildQuestion(
    "Match List-I with List-II. List-I (P) Newton (Q) Joule (R) Watt List-II (1) Force (2) Energy (3) Power",
    ["P-1, Q-2, R-3"],
    { qType: "match" },
  );
  assert.ok(l.body.includes("`[Q]` Joule"));
  assert.equal(l.options[0], "🇦 (A)  P ➔ 1  •  Q ➔ 2  •  R ➔ 3");
});

test("textbook math spacing", () => {
  assert.equal(u("x+y=z"), "x + y = z");
  assert.equal(u("f(x)=x^2-4x+4"), "f(x) = x² - 4x + 4");
  assert.equal(u(String.raw`a < b \le c > d \ge e`), "a < b ≤ c > d ≥ e");
  assert.equal(u(String.raw`2x+3y=5`), "2x + 3y = 5");
  assert.equal(u("x=-5"), "x = -5");
});

test("textbook calculus and limits", () => {
  assert.equal(u(String.raw`\lim_{x \to 0} \frac{\sin x}{x} = 1`), "lim (x → 0) (sin x)/x = 1");
  assert.equal(u(String.raw`\lim_{n \to \infty} \left(1 + \frac{1}{n}\right)^n = e`), "lim (n → ∞) (1 + 1/n)ⁿ = e");
  assert.equal(u(String.raw`\frac{d}{dx}(x^n) = nx^{n-1}`), "d/dx(xⁿ) = nxⁿ⁻¹");
  assert.equal(u(String.raw`\frac{\partial u}{\partial x} + \frac{\partial u}{\partial y} = 0`), "∂u/∂x + ∂u/∂y = 0");
  assert.equal(u(String.raw`\frac{\Delta y}{\Delta x}`), "Δy/Δx");
  assert.equal(u(String.raw`\sum_{i=1}^{n} i = \frac{n(n+1)}{2}`), "∑ᵢ₌₁ⁿ i = n(n + 1)/2");
  assert.equal(u(String.raw`\int_{0}^{1} x \, dx = \frac{1}{2}`), "∫₀¹ x dx = ½");
});

test("no backslashes in subscripts and vectors", () => {
  const res = formatText(String.raw`Values: $k_B T$, $N_A$, $K_{eq}$, and $\lambda_{1,2}$.`);
  assert.ok(!res.includes(String.raw`\_`));
  assert.ok(res.includes("k_B T"));
  assert.ok(res.includes("N_A"));
  assert.ok(res.includes("K_(eq)"));
  assert.ok(res.includes("λ₁, ₂"));

  const vec = u(String.raw`\vec{v} = v_x \hat{i} + v_y \hat{j} + v_z \hat{k}`);
  assert.ok(!vec.includes(String.raw`\_`));
  assert.equal(vec, "v⃗ = vₓ î + v_y ĵ + v_z k̂");
});

test("greek without eating spaces", () => {
  const text = String.raw`The value of \alpha + \beta is 5 and \theta is 45^\circ.`;
  const formatted = formatText(text);
  assert.ok(formatted.includes("β is 5"));
  assert.ok(formatted.includes("θ is 45°"));
  assert.ok(!formatted.includes("βis"));
  assert.ok(!formatted.includes("θis"));
});

test("cases and delimiters", () => {
  assert.equal(u(String.raw`|x| = \begin{cases} x & x \ge 0 \\ -x & x < 0 \end{cases}`), "|x| = {x, x ≥ 0; -x, x < 0}");
  assert.equal(u(String.raw`\left( \frac{a+b}{c} \right)^2`), "((a + b)/c)²");
});

test("enhanced chemistry", () => {
  assert.equal(u(String.raw`\ce{CuSO4 . 5H2O}`), "CuSO₄ · 5H₂O");
  assert.equal(u(String.raw`\ce{Fe^{2+} + e- -> Fe^{3+}}`), "Fe²⁺ + e⁻ → Fe³⁺");
  assert.equal(u(String.raw`\ce{CaCO3 ->[\Delta] CaO + CO2}`), "CaCO₃ → [Δ] CaO + CO₂");
});

test("new question types", () => {
  const layout1 = buildQuestion("Assertion (A): Ice floats. Reason (R): Less dense.", undefined, {
    qType: "assertion_reason",
  });
  assert.equal(layout1.qType, "assertion_reason");
  assert.ok(layout1.footer.includes("Assertion & Reason"));

  const layout2 = buildQuestion("Statement I: Water boils. Statement II: Ice melts.", undefined, {
    qType: "statements",
  });
  assert.equal(layout2.qType, "statements");
  assert.ok(layout2.footer.includes("Statement I & II"));
});
