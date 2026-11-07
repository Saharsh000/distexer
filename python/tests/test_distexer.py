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


def test_textbook_math_spacing():
    assert u("x+y=z") == "x + y = z"
    assert u("f(x)=x^2-4x+4") == "f(x) = x² - 4x + 4"
    assert u(r"a < b \le c > d \ge e") == "a < b ≤ c > d ≥ e"
    assert u(r"2x+3y=5") == "2x + 3y = 5"
    assert u(r"x=-5") == "x = -5"


def test_textbook_calculus_and_limits():
    assert u(r"\lim_{x \to 0} \frac{\sin x}{x} = 1") == "lim (x → 0) (sin x)/x = 1"
    assert u(r"\lim_{n \to \infty} \left(1 + \frac{1}{n}\right)^n = e") == "lim (n → ∞) (1 + 1/n)ⁿ = e"
    assert u(r"\frac{d}{dx}(x^n) = nx^{n-1}") == "d/dx(xⁿ) = nxⁿ⁻¹"
    assert u(r"\frac{\partial u}{\partial x} + \frac{\partial u}{\partial y} = 0") == "∂u/∂x + ∂u/∂y = 0"
    assert u(r"\frac{\Delta y}{\Delta x}") == "Δy/Δx"
    assert u(r"\sum_{i=1}^{n} i = \frac{n(n+1)}{2}") == "∑ᵢ₌₁ⁿ i = n(n + 1)/2"
    assert u(r"\int_{0}^{1} x \, dx = \frac{1}{2}") == "∫₀¹ x dx = ½"


def test_no_backslashes_in_subscripts_and_vectors():
    res = distexer.format_text(r"Values: $k_B T$, $N_A$, $K_{eq}$, and $\lambda_{1,2}$.")
    assert r"\_" not in res
    assert "k_B T" in res
    assert "N_A" in res
    assert "K_(eq)" in res
    assert "λ₁, ₂" in res

    vec = u(r"\vec{v} = v_x \hat{i} + v_y \hat{j} + v_z \hat{k}")
    assert r"\_" not in vec
    assert "v⃗ = vₓ î + v_y ĵ + v_z k̂" == vec


def test_greek_without_eating_spaces():
    text = r"The value of \alpha + \beta is 5 and \theta is 45^\circ."
    formatted = distexer.format_text(text)
    assert "β is 5" in formatted
    assert "θ is 45°" in formatted
    assert "βis" not in formatted
    assert "θis" not in formatted


def test_cases_and_delimiters():
    assert u(r"|x| = \begin{cases} x & x \ge 0 \\ -x & x < 0 \end{cases}") == "|x| = {x, x ≥ 0; -x, x < 0}"
    assert u(r"\left( \frac{a+b}{c} \right)^2") == "((a + b)/c)²"


def test_enhanced_chemistry():
    assert u(r"\ce{CuSO4 . 5H2O}") == "CuSO₄ · 5H₂O"
    assert u(r"\ce{Fe^{2+} + e- -> Fe^{3+}}") == "Fe²⁺ + e⁻ → Fe³⁺"
    assert u(r"\ce{CaCO3 ->[\Delta] CaO + CO2}") == "CaCO₃ → [Δ] CaO + CO₂"


def test_new_question_types():
    layout1 = build_question("Assertion (A): Ice floats. Reason (R): Less dense.", q_type="assertion_reason")
    assert layout1.q_type == "assertion_reason"
    assert "Assertion & Reason" in layout1.footer

    layout2 = build_question("Statement I: Water boils. Statement II: Ice melts.", q_type="statements")
    assert layout2.q_type == "statements"
    assert "Statement I & II" in layout2.footer


def test_horizontal_fraction_bar():
    bar = distexer.format_fraction_bar("-b ± √(b² - 4ac)", "2a", prefix="x =")
    assert "─" in bar
    assert "x =" in bar

    disp = distexer.format_text(r"Solve: $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$")
    assert "─" in disp
    assert "/" not in disp.split("\n")[1]  # Horizontal bar, no slash

    dfrac = distexer.format_text(r"Value: $\dfrac{a + b}{c}$")
    assert "─" in dfrac


def test_render_question_card():
    buf = distexer.render_question_card(
        question=r"A particle executes SHM: $x = A \cos(\omega t)$. Find $E = \frac{1}{2}m\omega^2 A^2$.",
        options=[
            {"key": "A", "text": r"$E = \frac{1}{2}kA^2$"},
            {"key": "B", "text": r"$E = kA^2$"},
        ],
        subject="Physics",
        chapter="Oscillations",
        fontsize=20,
    )
    val = buf.getvalue()
    assert len(val) > 1000
    assert val.startswith(b"\x89PNG")
