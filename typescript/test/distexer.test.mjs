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
