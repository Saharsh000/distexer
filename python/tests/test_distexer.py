import distexer
from distexer import MODE_PRESERVE_KATEX, build_question, latex_to_unicode as u


def test_symbols_and_scripts():
    assert u(r"\alpha + \beta \to \gamma") == "α + β → γ"
    assert u("x^2 + y^{10}") == "x² + y¹⁰"
    assert u("H_2O") == "H₂O"
    assert u(r"25^\circ C") == "25° C"
    assert u(r"\pm \Delta H") == "± ΔH"


def test_fractions_and_roots():
    assert u(r"\frac{1}{2}") == "½"
    assert u(r"\frac{h}{p}") == "h/p"
    assert u(r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}") == "(-b ± √(b² - 4ac))/(2a)"
    assert u(r"\sqrt[3]{8}") == "∛8"


def test_chem_and_matrix():
    assert u(r"\ce{2H2 + O2 -> 2H2O}") == "2H₂ + O₂ → 2H₂O"
    assert u(r"\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}") == "(1, 2; 3, 4)"


def test_format_text_modes():
    raw = r"The \\alpha-amino acid has $pK_a \approx 2$"
    assert distexer.format_text(raw) == "The α-amino acid has pKₐ ≈ 2"
    assert distexer.format_text(r"Use $x^2$", MODE_PRESERVE_KATEX) == "Use $x^2$"
    assert distexer.format_text("costs $5 and $10") == "costs $5 and $10"


def test_normalize_fixes_delimiters():
    assert distexer.normalize(r"value \(x^2\)") == "value $x^2$"
    assert distexer.normalize(r"value $\frac{a}{b") == r"value $\frac{a}{b}$"


def test_listify_roman():
    out = distexer.listify("Consider: (i) A + B → C, (ii) C → D + E, (iii) E → F. Which are redox?")
    assert "▸ **(i)** A + B → C" in out
    assert "▸ **(iii)** E → F." in out
    assert out.endswith("Which are redox?")


def test_assertion_reason():
    out = distexer.listify("Assertion (A): Ice floats. Reason (R): Ice is less dense than water.")
    assert "**Assertion (A):** Ice floats." in out
    assert "**Reason (R):** Ice is less dense than water." in out


def test_match():
    q = ("Match List-I with List-II. List-I (P) Newton (Q) Joule (R) Watt "
         "List-II (1) Force (2) Energy (3) Power")
    layout = build_question(q, ["P-1, Q-2, R-3", "P-2, Q-1, R-3"], q_type="match")
    assert "📋 **LIST — I**" in layout.body
    assert "`[P]` Newton" in layout.body
    assert "`[3]` Power" in layout.body
    assert layout.options[0] == "🇦 (A)  P ➔ 1  •  Q ➔ 2  •  R ➔ 3"


def test_complex_math_collected():
    layout = build_question(r"Solve $$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$$", ["1", "2"])
    assert layout.formulas == [r"x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}"]
    assert "`[equation ↓]`" in layout.body
    assert layout.options == ["🇦  1", "🇧  2"]
