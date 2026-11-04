"""Minimal STEM trivia bot using distexer + discord.py.

    pip install "distexer[all]"
    export DISCORD_TOKEN=...      # never hard-code your token
    python examples/trivia_bot.py

Then type /question in your server.
"""

import os
import random

import discord
from discord import app_commands

import distexer

QUESTIONS = [
    {
        "title": "Algebra • Quadratics",
        "question": r"The roots of $ax^2 + bx + c = 0$ are given by $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$ "
                    r"For $x^2 - 5x + 6 = 0$, the larger root is:",
        "options": ["$2$", "$3$", "$5$", "$6$"],
        "answer": "B",
    },
    {
        "title": "Chemistry • Equilibrium",
        "question": r"Consider (i) $\ce{N2 + 3H2 <=> 2NH3}$, $\Delta H < 0$ (ii) $\ce{H2 + I2 <=> 2HI}$ "
                    r"(iii) $\ce{PCl5 <=> PCl3 + Cl2}$. Which equilibrium is unaffected by pressure?",
        "options": ["(i)", "(ii)", "(iii)", "None"],
        "answer": "B",
    },
    {
        "title": "Physics • Units",
        "question": "Match List-I with List-II. List-I (P) Force (Q) Energy (R) Power (S) Pressure "
                    "List-II (1) Watt (2) Pascal (3) Newton (4) Joule",
        "options": ["P-3, Q-4, R-1, S-2", "P-4, Q-3, R-2, S-1", "P-3, Q-1, R-4, S-2", "P-1, Q-2, R-3, S-4"],
        "q_type": "match",
        "answer": "A",
    },
    {
        "title": "Physics • Assertion & Reason",
        "question": r"Assertion (A): The de Broglie wavelength is $\lambda = \frac{h}{p}$. "
                    r"Reason (R): Matter shows wave-particle duality.",
        "options": ["Both true, R explains A", "Both true, R doesn't explain A", "A true, R false", "A false, R true"],
        "answer": "A",
    },
]


class TriviaBot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()


bot = TriviaBot()


@bot.tree.command(name="question", description="Get a random STEM question")
async def question(interaction: discord.Interaction) -> None:
    q = random.choice(QUESTIONS)
    await interaction.response.defer()  # rendering may take a moment the first time
    embed, file = await distexer.acreate_question_embed(
        title=q["title"],
        question=q["question"],
        options=q["options"],
        q_type=q.get("q_type", "single"),
        theme="solid_dark",  # readable in both light & dark mode
    )
    kwargs = {"embed": embed}
    if file is not None:
        kwargs["file"] = file
    await interaction.followup.send(**kwargs)


@bot.tree.command(name="tex", description="Pretty-print any text containing LaTeX")
@app_commands.describe(text="e.g. The $\\alpha$-particle has $E = mc^2$")
async def tex(interaction: discord.Interaction, text: str) -> None:
    await interaction.response.send_message(distexer.format_message(text))


@bot.tree.command(name="render", description="Render a LaTeX formula as an image")
async def render(interaction: discord.Interaction, formula: str) -> None:
    await interaction.response.defer()
    try:
        file = await distexer.arender_formula(formula, theme="solid_dark")
    except distexer.RenderError:
        await interaction.followup.send(distexer.latex_to_unicode(formula))
        return
    await interaction.followup.send(file=file)


if __name__ == "__main__":
    bot.run(os.environ["DISCORD_TOKEN"])
