// Keep in sync with python/src/distexer/formatters/symbols.py

export const GREEK: Record<string, string> = {
  "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
  "varepsilon": "ε", "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ",
  "iota": "ι", "kappa": "κ", "varkappa": "ϰ", "lambda": "λ", "mu": "μ",
  "nu": "ν", "xi": "ξ", "omicron": "ο", "pi": "π", "varpi": "ϖ",
  "rho": "ρ", "varrho": "ϱ", "sigma": "σ", "varsigma": "ς", "tau": "τ",
  "upsilon": "υ", "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ",
  "omega": "ω",
  "Alpha": "Α", "Beta": "Β", "Gamma": "Γ", "Delta": "Δ", "Epsilon": "Ε",
  "Zeta": "Ζ", "Eta": "Η", "Theta": "Θ", "Iota": "Ι", "Kappa": "Κ",
  "Lambda": "Λ", "Mu": "Μ", "Nu": "Ν", "Xi": "Ξ", "Omicron": "Ο",
  "Pi": "Π", "Rho": "Ρ", "Sigma": "Σ", "Tau": "Τ", "Upsilon": "Υ",
  "Phi": "Φ", "Chi": "Χ", "Psi": "Ψ", "Omega": "Ω"
};

export const SYMBOLS: Record<string, string> = {
  // arithmetic & binary operations
  "pm": "±", "mp": "∓", "times": "×", "div": "÷", "cdot": "·", "ast": "∗",
  "star": "⋆", "circ": "∘", "bullet": "•", "oplus": "⊕", "otimes": "⊗",
  "ominus": "⊖", "odot": "⊙", "oslash": "⊘", "dagger": "†", "ddagger": "‡",
  "diamond": "◇", "bigtriangleup": "△", "bigtriangledown": "▽",

  // relations
  "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠",
  "approx": "≈", "napprox": "≉", "sim": "∼", "nsim": "≁", "simeq": "≃",
  "cong": "≅", "ncong": "≇", "equiv": "≡", "nequiv": "≢", "propto": "∝",
  "ll": "≪", "gg": "≫", "mid": "∣", "parallel": "∥", "nparallel": "∦",
  "perp": "⊥", "leqslant": "⩽", "geqslant": "⩾", "doteq": "≐",
  "prec": "≺", "succ": "≻", "preceq": "⪯", "succeq": "⪰",
  "asymp": "≍", "smile": "⌣", "frown": "⌢", "models": "⊨", "vdash": "⊢", "dashv": "⊣",

  // arrows
  "to": "→", "rightarrow": "→", "leftarrow": "←", "gets": "←",
  "Rightarrow": "⇒", "Leftarrow": "⇐", "leftrightarrow": "↔",
  "Leftrightarrow": "⇔", "longrightarrow": "⟶", "longleftarrow": "⟵",
  "Longrightarrow": "⟹", "Longleftarrow": "⟸", "implies": "⟹", "iff": "⟺", "impliedby": "⟸",
  "rightleftharpoons": "⇌", "leftrightharpoons": "⇋", "leftrightarrows": "⇆", "rightleftarrows": "⇄",
  "uparrow": "↑", "downarrow": "↓", "updownarrow": "↕", "Updownarrow": "⇕",
  "mapsto": "↦", "rightharpoonup": "⇀", "rightharpoondown": "⇁", "leftharpoonup": "↼", "leftharpoondown": "⇃",
  "nearrow": "↗", "searrow": "↘", "nwarrow": "↖", "swarrow": "↙",
  "hookrightarrow": "↪", "hookleftarrow": "↩", "leadsto": "↝",

  // big operators / calculus
  "sum": "∑", "prod": "∏", "coprod": "∐", "int": "∫", "iint": "∬",
  "iiint": "∭", "oint": "∮", "oiint": "∯", "oiiint": "∰",
  "partial": "∂", "nabla": "∇", "infty": "∞",

  // sets & logic
  "in": "∈", "notin": "∉", "ni": "∋", "owns": "∋",
  "subset": "⊂", "subseteq": "⊆", "supset": "⊃", "supseteq": "⊇",
  "nsubseteq": "⊈", "nsupseteq": "⊉", "subsetneq": "⊊", "supsetneq": "⊋",
  "cup": "∪", "cap": "∩", "emptyset": "∅", "varnothing": "∅",
  "forall": "∀", "exists": "∃", "nexists": "∄",
  "neg": "¬", "lnot": "¬", "land": "∧", "wedge": "∧", "lor": "∨", "vee": "∨",
  "setminus": "∖", "sqcap": "⊓", "sqcup": "⊔",
  "therefore": "∴", "because": "∵",

  // misc symbols & physics constants
  "degree": "°", "textdegree": "°", "celsius": "°C",
  "angle": "∠", "measuredangle": "∡", "sphericalangle": "∢",
  "triangle": "△", "square": "□", "prime": "′", "backprime": "‵",
  "hbar": "ℏ", "hslash": "ℏ", "ell": "ℓ", "Re": "ℜ", "Im": "ℑ",
  "aleph": "ℵ", "wp": "℘",
  "cdots": "⋯", "ldots": "…", "dots": "…", "dotsc": "…", "dotsb": "⋯", "dotsm": "⋯", "dotsi": "⋯", "dotso": "…",
  "vdots": "⋮", "ddots": "⋱",
  "langle": "⟨", "rangle": "⟩", "lceil": "⌈", "rceil": "⌉", "lfloor": "⌊", "rfloor": "⌋",
  "lvert": "|", "rvert": "|", "vert": "|", "lVert": "‖", "rVert": "‖", "Vert": "‖",
  "lbrace": "{", "rbrace": "}",
  "checkmark": "✓", "AA": "Å", "angstrom": "Å", "S": "§", "copyright": "©",
  "top": "⊤", "bot": "⊥", "ohm": "Ω", "micro": "µ",

  // spacing
  "quad": "  ", "qquad": "    ", "space": " ", "enspace": " ",
  "thinspace": " ", "medspace": " ", "thickspace": " "
};

export const CONTROL_SYMBOLS: Record<string, string> = {
  ",": " ",
  ";": " ",
  ":": " ",
  ">": " ",
  "!": "",
  " ": " ",
  "\\": " ",
  "{": "{",
  "}": "}",
  "%": "%",
  "$": "$",
  "&": "&",
  "#": "#",
  "_": "_",
  "|": "‖"
};

export const SUPERSCRIPTS: Record<string, string> = {
  // digits
  "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
  "7": "⁷", "8": "⁸", "9": "⁹",
  // identity for already-superscript digits & signs
  "⁰": "⁰", "¹": "¹", "²": "²", "³": "³", "⁴": "⁴", "⁵": "⁵", "⁶": "⁶",
  "⁷": "⁷", "⁸": "⁸", "⁹": "⁹", "⁺": "⁺", "⁻": "⁻",
  // signs & operators
  "+": "⁺", "-": "⁻", "−": "⁻", "=": "⁼",
  "(": "⁽", ")": "⁾", "*": "*", "∗": "*", ".": "·", ",": ",",
  "′": "′", "'": "′", "°": "°", "∘": "°", " ": "",
  // Latin lowercase
  "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ", "g": "ᵍ",
  "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ",
  "o": "ᵒ", "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ",
  "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
  // Latin uppercase
  "A": "ᴬ", "B": "ᴮ", "C": "ᶜ", "D": "ᴰ", "E": "ᴱ", "G": "ᴳ", "H": "ᴴ",
  "I": "ᴵ", "J": "ᴶ", "K": "ᴷ", "L": "ᴸ", "M": "ᴹ", "N": "ᴺ", "O": "ᴼ",
  "P": "ᴾ", "R": "ᴿ", "T": "ᵀ", "U": "ᵁ", "V": "ⱽ", "W": "ᵂ",
  // Greek
  "α": "ᵅ", "β": "ᵝ", "γ": "ᵞ", "δ": "ᵟ", "θ": "ᶿ", "φ": "ᵠ", "χ": "ᵡ"
};

export const SUBSCRIPTS: Record<string, string> = {
  // digits
  "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆",
  "7": "₇", "8": "₈", "9": "₉",
  // identity for already-subscript digits & signs
  "₀": "₀", "₁": "₁", "₂": "₂", "₃": "₃", "₄": "₄", "₅": "₅", "₆": "₆",
  "₇": "₇", "₈": "₈", "₉": "₉", "₊": "₊", "₋": "₋",
  // signs & operators
  "+": "₊", "-": "₋", "−": "₋", "=": "₌",
  "(": "₍", ")": "₎", ",": ",", ".": ".", "/": "/", "∞": "∞", " ": "",
  // Latin lowercase
  "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ", "l": "ₗ",
  "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ",
  "u": "ᵤ", "v": "ᵥ", "x": "ₓ",
  // Greek
  "β": "ᵦ", "γ": "ᵧ", "ρ": "ᵨ", "φ": "ᵩ", "χ": "ᵪ"
};

export const BLACKBOARD: Record<string, string> = {
  "R": "ℝ", "N": "ℕ", "Z": "ℤ", "Q": "ℚ", "C": "ℂ", "P": "ℙ", "H": "ℍ",
  "E": "𝔼", "1": "𝟙", "F": "𝔽", "K": "𝕂", "D": "𝔻", "B": "𝔹"
};

export const ACCENTS: Record<string, string> = {
  "vec": "\u20d7", "hat": "\u0302", "widehat": "\u0302", "bar": "\u0304",
  "overline": "\u0305", "dot": "\u0307", "ddot": "\u0308", "dddot": "\u20db",
  "tilde": "\u0303", "widetilde": "\u0303", "underline": "\u0332",
  "acute": "\u0301", "grave": "\u0300", "check": "\u030c", "breve": "\u0306",
  "overrightarrow": "\u20d7", "cancel": "\u0338"
};

export const REGIONAL_INDICATORS: Record<string, string> = {
  "A": "🇦", "B": "🇧", "C": "🇨", "D": "🇩", "E": "🇪", "F": "🇫",
  "G": "🇬", "H": "🇭", "I": "🇮", "J": "🇯", "K": "🇰", "L": "🇱",
  "M": "🇲", "N": "🇳", "O": "🇴", "P": "🇵", "Q": "🇶", "R": "🇷",
  "S": "🇸", "T": "🇹", "U": "🇺", "V": "🇻", "W": "🇼", "X": "🇽",
  "Y": "🇾", "Z": "🇿"
};

export const VULGAR_FRACTIONS: Record<string, string> = {
  "1/2": "½", "1/3": "⅓", "2/3": "⅔", "1/4": "¼", "3/4": "¾",
  "1/5": "⅕", "2/5": "⅖", "3/5": "⅗", "4/5": "⅘", "1/6": "⅙",
  "5/6": "⅚", "1/7": "⅐", "1/8": "⅛", "3/8": "⅜", "5/8": "⅝",
  "7/8": "⅞", "1/9": "⅑", "1/10": "⅒"
};

export const MATRIX_DELIMS: Record<string, [string, string]> = {
  "matrix": ["[", "]"], "smallmatrix": ["[", "]"], "pmatrix": ["(", ")"],
  "bmatrix": ["[", "]"], "Bmatrix": ["{", "}"], "vmatrix": ["|", "|"],
  "Vmatrix": ["‖", "‖"]
};

export const FUNCTIONS: ReadonlySet<string> = new Set([
  "sin", "cos", "tan", "cot", "sec", "csc", "sinh", "cosh", "tanh", "coth",
  "arcsin", "arccos", "arctan", "arccot", "arcsec", "arccsc",
  "log", "ln", "lg", "exp", "lim", "liminf", "limsup", "max", "min", "sup", "inf",
  "det", "dim", "ker", "gcd", "lcm", "deg", "arg", "Pr", "hom", "tr", "operatorname"
]);

export const IGNORED: ReadonlySet<string> = new Set([
  "left", "right", "middle", "big", "Big", "bigg", "Bigg", "bigl", "bigr",
  "Bigl", "Bigr", "biggl", "biggr", "displaystyle", "textstyle",
  "scriptstyle", "limits", "nolimits", "nonumber", "notag", "centering",
  "rm", "bf", "it", "mathstrut", "strut"
]);

export const IGNORED_WITH_ARG: ReadonlySet<string> = new Set([
  "color", "label", "tag", "hspace", "vspace", "phantom", "hphantom", "vphantom"
]);
