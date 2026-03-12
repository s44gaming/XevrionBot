"""
Hauskat minipelit – jokainen kytkettävissä web-dashboardista.
"""
import random
import discord
from discord import app_commands
from discord.ext import commands


class MinipelitCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Flip a coin – heads or tails?")
    async def coinflip(self, interaction: discord.Interaction):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "kolikko"):
            await interaction.response.send_message(
                "⚠️ This minigame is disabled. Enable it in web dashboard.", ephemeral=True
            )
            return
        tulos = random.choice(("🪙 **Heads!**", "🪙 **Tails!**"))
        await interaction.response.send_message(tulos)

    @app_commands.command(name="dice", description="Roll dice (e.g. 1d6, 2d20)")
    @app_commands.describe(roll="E.g. 1d6, 2d6, 1d20 (default 1d6)")
    async def dice(self, interaction: discord.Interaction, roll: str = "1d6"):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "noppa"):
            await interaction.response.send_message(
                "⚠️ This minigame is disabled. Enable it in web dashboard.", ephemeral=True
            )
            return
        try:
            parts = roll.lower().replace("d", " ").split()
            if len(parts) != 2:
                raise ValueError("Use format 1d6 or 2d20")
            n, sivu = int(parts[0]), int(parts[1])
            if n < 1 or n > 10 or sivu < 2 or sivu > 100:
                raise ValueError("Count 1–10, sides 2–100")
            tulokset = [random.randint(1, sivu) for _ in range(n)]
            total = sum(tulokset)
            if n == 1:
                msg = f"🎲 Dice: **{tulokset[0]}** (d{sivu})"
            else:
                msg = f"🎲 Dice: {tulokset} → total **{total}** ({n}d{sivu})"
            await interaction.response.send_message(msg)
        except (ValueError, IndexError):
            await interaction.response.send_message(
                "Use format e.g. `1d6` or `2d20`. First number = count, second = sides.",
                ephemeral=True
            )

    @app_commands.command(name="8ball", description="Magic 8-ball answers your question")
    @app_commands.describe(question="Ask anything")
    async def ball8(self, interaction: discord.Interaction, question: str):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "8ball"):
            await interaction.response.send_message(
                "⚠️ This minigame is disabled. Enable it in web dashboard.", ephemeral=True
            )
            return
        answers = [
            "Yes, definitely!", "Yes!", "Looks like it.", "Probably.",
            "Can't say.", "Try again later.", "No comment.",
            "Doesn't look good.", "No.", "Definitely not.", "Don't count on it."
        ]
        answer = random.choice(answers)
        await interaction.response.send_message(f"🔮 **{question}**\n{answer}")

    @app_commands.command(name="rps", description="Rock, paper, scissors – vs bot")
    @app_commands.describe(choice="Your choice")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock 🪨", value="rock"),
        app_commands.Choice(name="Paper 📄", value="paper"),
        app_commands.Choice(name="Scissors ✂️", value="scissors"),
    ])
    async def rps(self, interaction: discord.Interaction, choice: app_commands.Choice[str]):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "kps"):
            await interaction.response.send_message(
                "⚠️ This minigame is disabled. Enable it in web dashboard.", ephemeral=True
            )
            return
        bot_choice = random.choice(("rock", "paper", "scissors"))
        emoji = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        you, bot = choice.value, bot_choice
        if you == bot:
            tulos = "🤝 Tie!"
        elif (you == "rock" and bot == "scissors") or (you == "paper" and bot == "rock") or (you == "scissors" and bot == "paper"):
            tulos = "🎉 You won!"
        else:
            tulos = "😅 Bot won!"
        await interaction.response.send_message(
            f"{emoji[you]} vs {emoji[bot]}\n{tulos}"
        )

    @app_commands.command(name="guess", description="Guess number 1–10 – bot picks the answer")
    @app_commands.describe(number="Your guess (1–10)")
    async def guess(self, interaction: discord.Interaction, number: int):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "arvaa"):
            await interaction.response.send_message(
                "⚠️ Tämä minipeli on poistettu käytöstä.", ephemeral=True
            )
            return
        if number < 1 or number > 10:
            await interaction.response.send_message("Number must be 1–10.", ephemeral=True)
            return
        correct = random.randint(1, 10)
        if number == correct:
            await interaction.response.send_message(f"🎉 Correct! I was thinking **{correct}**.")
        else:
            await interaction.response.send_message(f"😅 Wrong. I was thinking **{correct}**, you guessed {number}.")

    @app_commands.command(name="choose", description="Randomly pick one of the given options")
    @app_commands.describe(options="Comma-separated options, e.g. pizza,kebab,salad")
    async def choose(self, interaction: discord.Interaction, options: str):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "arpa"):
            await interaction.response.send_message(
                "⚠️ This minigame is disabled. Enable it in web dashboard.", ephemeral=True
            )
            return
        opts = [x.strip() for x in options.split(",") if x.strip()]
        if len(opts) < 2:
            await interaction.response.send_message(
                "Give at least two options separated by comma, e.g. `pizza, kebab, salad`.",
                ephemeral=True
            )
            return
        if len(opts) > 20:
            await interaction.response.send_message("Maximum 20 options.", ephemeral=True)
            return
        valittu = random.choice(opts)
        await interaction.response.send_message(f"🎱 **Choose:** {valittu}")

    @app_commands.command(name="roulette", description="Russian roulette – 1/6 chance bang")
    async def ruletti(self, interaction: discord.Interaction):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "ruletti"):
            await interaction.response.send_message(
                "⚠️ This minigame is disabled. Enable it in web dashboard.", ephemeral=True
            )
            return
        if random.randint(1, 6) == 1:
            await interaction.response.send_message("💥 **BANG!** 😵")
        else:
            await interaction.response.send_message("🔫 *click* ... safe round! 😮‍💨")


async def setup(bot):
    await bot.add_cog(MinipelitCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
