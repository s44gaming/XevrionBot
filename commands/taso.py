"""Levellijärjestelmän /taso-komento."""
import discord
from discord import app_commands
from discord.ext import commands
import database


def _xp_for_next_level(level: int) -> int:
    """XP määrä seuraavaan tasoon (nykyisen tason jälkeen)."""
    return 100 * (level + 1)


def _xp_progress_in_level(xp: int) -> tuple[int, int, int]:
    """Palauttaa (current_in_level, needed_for_level, level)."""
    level = database._xp_to_level(xp)
    xp_at_level_start = 100 * level * (level + 1) // 2 if level > 0 else 0
    xp_needed = _xp_for_next_level(level)
    current = xp - xp_at_level_start
    return current, xp_needed, level


class TasoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="level", description="Show level and XP")
    @app_commands.describe(user="User (optional, defaults to you)")
    async def level(self, interaction: discord.Interaction, user: discord.Member | None = None):
        if not interaction.guild:
            return await interaction.response.send_message("Use in a server.", ephemeral=True)
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "taso")
        if not enabled:
            return await interaction.response.send_message(
                "⚠️ Level system is disabled on this server.",
                ephemeral=True,
            )
        target = user or (interaction.user if isinstance(interaction.user, discord.Member) else None)
        if not target:
            return await interaction.response.send_message("User not found.", ephemeral=True)
        xp, level = database.get_user_xp(str(interaction.guild_id), str(target.id))
        current, needed, _ = _xp_progress_in_level(xp)
        bar_len = 10
        filled = int(bar_len * current / needed) if needed else bar_len
        bar = "█" * filled + "░" * (bar_len - filled)
        embed = discord.Embed(
            title=f"Level: {target.display_name}",
            description=f"**Level {level}** • {xp} XP\n`{bar}` {current}/{needed} XP to next",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Keep chatting to earn more XP!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show level top 10")
    async def leaderboard(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Use in a server.", ephemeral=True)
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "tasonboard")
        if not enabled:
            return await interaction.response.send_message(
                "⚠️ Level system is disabled on this server.",
                ephemeral=True,
            )
        rows = database.get_leaderboard(str(interaction.guild_id), 10)
        if not rows:
            return await interaction.response.send_message(
                "No XP data yet. Start chatting!",
                ephemeral=True,
            )
        lines = []
        for i, (uid, xp, lvl) in enumerate(rows, 1):
            user = interaction.guild.get_member(int(uid))
            name = user.display_name if user else f"<@{uid}>"
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"`{i}.`")
            lines.append(f"{medal} **{name}** — Level {lvl} ({xp} XP)")
        embed = discord.Embed(
            title="Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TasoCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
