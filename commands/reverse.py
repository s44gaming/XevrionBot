"""
Reverse-komento – kääntää tekstin takaperin.
"""
import discord
from discord import app_commands
from discord.ext import commands


class ReverseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reverse", description="Reverse text backwards")
    @app_commands.describe(text="Text to reverse")
    async def reverse(self, interaction: discord.Interaction, text: str):
        if interaction.guild_id and not await self.bot.is_feature_enabled(interaction.guild_id, "reverse"):
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä. Ota se käyttöön web-dashboardista.",
                ephemeral=True,
            )
            return
        text = (text or "")[:500]
        if not text:
            await interaction.response.send_message("Enter text to reverse.", ephemeral=True)
            return
        reversed_text = text[::-1]
        await interaction.response.send_message(f"**Reversed:** {reversed_text}")


async def setup(bot):
    await bot.add_cog(ReverseCog(bot))
