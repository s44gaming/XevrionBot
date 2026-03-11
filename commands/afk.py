"""AFK-järjestelmä – /afk asettaa AFK-tilan."""
import discord
from discord import app_commands
from discord.ext import commands
import database


class AfkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="afk", description="Aseta itsesi AFK-tilaan")
    @app_commands.describe(syy="Miksi olet poissa (valinnainen)")
    async def afk(self, interaction: discord.Interaction, syy: str = "AFK"):
        if not interaction.guild:
            await interaction.response.send_message("Tätä ei voi käyttää DM:ssä.", ephemeral=True)
            return
        if not (await self.bot.is_feature_enabled(interaction.guild_id, "afk")):
            await interaction.response.send_message(
                "⚠️ AFK on poistettu käytöstä.",
                ephemeral=True,
            )
            return
        settings = self.bot.get_afk_settings(interaction.guild_id)
        if not settings.get("enabled", True):
            await interaction.response.send_message(
                "⚠️ AFK on poistettu käytöstä tällä palvelimella.",
                ephemeral=True,
            )
            return
        reason = (syy or "AFK")[:200]
        database.set_afk(str(interaction.guild_id), str(interaction.user.id), reason)
        await interaction.response.send_message(
            f"✅ Olet nyt AFK-tilassa: **{reason}**",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(AfkCog(bot))
