"""Ehdotusjärjestelmä – /ehdotus lähettää ehdotuksen kanavalle."""
import discord
from discord import app_commands
from discord.ext import commands


class EhdotusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggestion", description="Send a suggestion to staff")
    @app_commands.describe(suggestion="Your suggestion")
    async def suggestion(self, interaction: discord.Interaction, suggestion: str):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "ehdotus"):
            await interaction.response.send_message(
                "⚠️ Suggestion system is disabled.",
                ephemeral=True,
            )
            return
        settings = self.bot.get_suggestion_settings(interaction.guild_id)
        if not settings.get("enabled") or not settings.get("channel_id"):
            await interaction.response.send_message(
                "⚠️ Suggestion channel not set. Ask admin to configure it.",
                ephemeral=True,
            )
            return
        try:
            channel = await self.bot.fetch_channel(settings["channel_id"])
        except (discord.NotFound, discord.Forbidden):
            await interaction.response.send_message(
                "⚠️ Suggestion channel not found.",
                ephemeral=True,
            )
            return
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "⚠️ Invalid channel.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="💡 New suggestion",
            description=(suggestion or "")[:2000] or "_Empty_",
            color=discord.Color.blue(),
        )
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"ID: {interaction.user.id}")
        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Your suggestion has been sent to <#{channel.id}>!",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(EhdotusCog(bot))
