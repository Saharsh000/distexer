/**
 * Minimal discord.js trivia bot using distexer.
 *
 *   npm i discord.js distexer
 *   npm i mathjax-full @resvg/resvg-js   # optional: offline formula images
 *   DISCORD_TOKEN=... npx tsx examples/bot.ts
 */
import { Client, Events, GatewayIntentBits, REST, Routes, SlashCommandBuilder } from "discord.js";
import { createQuestionEmbed, formatMessage } from "distexer";

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

const commands = [
  new SlashCommandBuilder().setName("question").setDescription("Random STEM question"),
  new SlashCommandBuilder()
    .setName("tex")
    .setDescription("Pretty-print text containing LaTeX")
    .addStringOption((o) => o.setName("text").setDescription("e.g. $E = mc^2$").setRequired(true)),
].map((c) => c.toJSON());

client.once(Events.ClientReady, async (c) => {
  await new REST().setToken(process.env.DISCORD_TOKEN!).put(Routes.applicationCommands(c.user.id), { body: commands });
  console.log(`Ready as ${c.user.tag}`);
});

client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === "question") {
    await interaction.deferReply();
    const msg = await createQuestionEmbed({
      title: "Algebra • Quadratics",
      question: String.raw`For $ax^2 + bx + c = 0$: $$x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$ The larger root of $x^2 - 5x + 6 = 0$ is:`,
      options: ["$2$", "$3$", "$5$", "$6$"],
      theme: "solid_dark",
    });
    await interaction.editReply({ embeds: msg.embeds, files: msg.files });
  }

  if (interaction.commandName === "tex") {
    await interaction.reply(formatMessage(interaction.options.getString("text", true)));
  }
});

client.login(process.env.DISCORD_TOKEN);
