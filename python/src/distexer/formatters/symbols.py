"""Lookup tables used to transliterate LaTeX into Discord-friendly Unicode."""

from __future__ import annotations

GREEK: dict[str, str] = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
    "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "omicron": "ο", "pi": "π", "varpi": "ϖ", "rho": "ρ", "varrho": "ϱ",
    "sigma": "σ", "varsigma": "ς", "tau": "τ", "upsilon": "υ", "phi": "φ",
    "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}

SYMBOLS: dict[str, str] = {
    # arithmetic
    "pm": "±", "mp": "∓", "times": "×", "div": "÷", "cdot": "·", "ast": "∗",
    "star": "⋆", "circ": "∘", "bullet": "•", "oplus": "⊕", "otimes": "⊗",
    "ominus": "⊖", "odot": "⊙", "dagger": "†",
    # relations
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠",
    "approx": "≈", "sim": "∼", "simeq": "≃", "cong": "≅", "equiv": "≡",
    "propto": "∝", "ll": "≪", "gg": "≫", "mid": "∣", "parallel": "∥",
    "perp": "⊥", "leqslant": "⩽", "geqslant": "⩾", "doteq": "≐",
    # arrows
    "to": "→", "rightarrow": "→", "leftarrow": "←", "gets": "←",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "leftrightarrow": "↔",
    "Leftrightarrow": "⇔", "longrightarrow": "⟶", "longleftarrow": "⟵",
    "Longrightarrow": "⟹", "implies": "⟹", "iff": "⟺", "impliedby": "⟸",
    "rightleftharpoons": "⇌", "leftrightharpoons": "⇋", "uparrow": "↑",
    "downarrow": "↓", "mapsto": "↦", "rightharpoonup": "⇀", "nearrow": "↗",
    "searrow": "↘",
    # big operators / calculus
    "sum": "∑", "prod": "∏", "coprod": "∐", "int": "∫", "iint": "∬",
    "iiint": "∭", "oint": "∮", "partial": "∂", "nabla": "∇", "infty": "∞",
    # sets & logic
    "in": "∈", "notin": "∉", "ni": "∋", "subset": "⊂", "subseteq": "⊆",
    "supset": "⊃", "supseteq": "⊇", "cup": "∪", "cap": "∩", "emptyset": "∅",
    "varnothing": "∅", "forall": "∀", "exists": "∃", "nexists": "∄",
    "neg": "¬", "lnot": "¬", "land": "∧", "wedge": "∧", "lor": "∨", "vee": "∨",
    "setminus": "∖", "therefore": "∴", "because": "∵",
    # misc
    "degree": "°", "angle": "∠", "measuredangle": "∡", "triangle": "△",
    "square": "□", "prime": "′", "hbar": "ℏ", "ell": "ℓ", "Re": "ℜ",
    "Im": "ℑ", "aleph": "ℵ", "wp": "℘", "cdots": "⋯", "ldots": "…",
    "dots": "…", "vdots": "⋮", "ddots": "⋱", "langle": "⟨", "rangle": "⟩",
    "lceil": "⌈", "rceil": "⌉", "lfloor": "⌊", "rfloor": "⌋", "lvert": "|",
    "rvert": "|", "vert": "|", "Vert": "‖", "lbrace": "{", "rbrace": "}",
    "checkmark": "✓", "AA": "Å", "angstrom": "Å", "S": "§", "copyright": "©",
    "quad": " ", "qquad": "  ", "space": " ", "enspace": " ", "thinspace": " ",
    "textdegree": "°", "celsius": "°C", "ohm": "Ω", "micro": "µ",
}

FUNCTIONS: set[str] = {
    "sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh", "tanh", "coth",
    "arcsin", "arccos", "arctan", "log", "ln", "lg", "exp", "lim", "liminf",
    "limsup", "max", "min", "sup", "inf", "det", "dim", "ker", "gcd", "lcm",
    "deg", "arg", "Pr", "hom", "tr",
}

# Commands whose arguments are swallowed and replaced by nothing.
IGNORED_WITH_ARG: set[str] = {"color", "label", "tag", "hspace", "vspace", "phantom", "hphantom", "vphantom"}

# Commands that produce no output on their own.
IGNORED: set[str] = {
    "left", "right", "middle", "big", "Big", "bigg", "Bigg", "bigl", "bigr",
    "Bigl", "Bigr", "biggl", "biggr", "displaystyle", "textstyle",
    "scriptstyle", "limits", "nolimits", "nonumber", "notag", "centering",
    "rm", "bf", "it", "mathstrut", "strut",
}

CONTROL_SYMBOLS: dict[str, str] = {
    ",": "\u2009", ";": " ", ":": " ", ">": " ", "!": "", " ": " ",
    "\\": " ", "{": "{", "}": "}", "%": "%", "$": "$", "&": "&", "#": "#",
    "_": "_", "|": "‖",
}

SUPERSCRIPTS: dict[str, str] = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹", "+": "⁺", "-": "⁻", "−": "⁻", "=": "⁼",
    "(": "⁽", ")": "⁾", "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
    "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ",
    "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ",
    "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ", "A": "ᴬ",
    "B": "ᴮ", "D": "ᴰ", "E": "ᴱ", "G": "ᴳ", "H": "ᴴ", "I": "ᴵ", "J": "ᴶ",
    "K": "ᴷ", "L": "ᴸ", "M": "ᴹ", "N": "ᴺ", "O": "ᴼ", "P": "ᴾ", "R": "ᴿ",
    "T": "ᵀ", "U": "ᵁ", "V": "ⱽ", "W": "ᵂ", "α": "ᵅ", "β": "ᵝ", "γ": "ᵞ",
    "δ": "ᵟ", "θ": "ᶿ", "φ": "ᵠ", "χ": "ᵡ", "∘": "°", "′": "′", "*": "*",
    "∗": "*", ".": "·", " ": "",
}

SUBSCRIPTS: dict[str, str] = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆",
    "7": "₇", "8": "₈", "9": "₉", "+": "₊", "-": "₋", "−": "₋", "=": "₌",
    "(": "₍", ")": "₎", "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
    "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "r": "ᵣ",
    "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "x": "ₓ", "β": "ᵦ", "γ": "ᵧ",
    "ρ": "ᵨ", "φ": "ᵩ", "χ": "ᵪ", " ": "",
}

VULGAR_FRACTIONS: dict[tuple[str, str], str] = {
    ("1", "2"): "½", ("1", "3"): "⅓", ("2", "3"): "⅔", ("1", "4"): "¼",
    ("3", "4"): "¾", ("1", "5"): "⅕", ("2", "5"): "⅖", ("3", "5"): "⅗",
    ("4", "5"): "⅘", ("1", "6"): "⅙", ("5", "6"): "⅚", ("1", "7"): "⅐",
    ("1", "8"): "⅛", ("3", "8"): "⅜", ("5", "8"): "⅝", ("7", "8"): "⅞",
    ("1", "9"): "⅑", ("1", "10"): "⅒",
}

BLACKBOARD: dict[str, str] = {
    "R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ", "P": "ℙ", "H": "ℍ",
    "E": "𝔼", "1": "𝟙",
}

# combining characters placed after the base character
ACCENTS: dict[str, str] = {
    "vec": "\u20d7", "hat": "\u0302", "widehat": "\u0302", "bar": "\u0304",
    "overline": "\u0305", "dot": "\u0307", "ddot": "\u0308", "tilde": "\u0303",
    "widetilde": "\u0303", "underline": "\u0332", "acute": "\u0301",
    "grave": "\u0300", "check": "\u030c", "breve": "\u0306",
    "overrightarrow": "\u20d7", "cancel": "\u0338",
}

MATRIX_DELIMS: dict[str, tuple[str, str]] = {
    "matrix": ("[", "]"), "smallmatrix": ("[", "]"), "pmatrix": ("(", ")"),
    "bmatrix": ("[", "]"), "Bmatrix": ("{", "}"), "vmatrix": ("|", "|"),
    "Vmatrix": ("‖", "‖"),
}

REGIONAL_INDICATORS: dict[str, str] = {
    letter: chr(0x1F1E6 + index) for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
}
