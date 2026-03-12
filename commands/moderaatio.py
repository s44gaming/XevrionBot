"""
Moderaatiokomennot.
Moderaattoriroolit + toimintojen kytkimet + logikanava hallitaan web-dashboardista (palvelinkohtaisesti).
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone

import database
from logs import send_guild_log


def _error(msg: str) -> discord.Embed:
    return discord.Embed(color=discord.Color.red(), description=f"❌ {msg}")


def _ok(msg: str) -> discord.Embed:
    return discord.Embed(color=discord.Color.green(), description=f"✅ {msg}")


class ModeraatioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _check_mod(self, interaction: discord.Interaction, action: str) -> bool:
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False
        if not self.bot.has_mod_permission(interaction.user):
            await interaction.response.send_message(embed=_error("You don't have mod permissions."), ephemeral=True)
            return False
        if not self.bot.is_mod_action_enabled(interaction.guild_id, action):
            await interaction.response.send_message(
                embed=_error("Action disabled on this server (web dashboard)."),
                ephemeral=True,
            )
            return False
        return True

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="Member to kick", reason="Reason (optional)")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = ""):
        if not await self._check_mod(interaction, "kick"):
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=_error("Cannot kick member with same/higher role."), ephemeral=True)
            return
        try:
            await member.kick(reason=reason or f"Mod: {interaction.user}")
            await interaction.response.send_message(embed=_ok(f"Kicked: {member}"))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderation: Kick",
                f"**Target:** {member} (`{member.id}`)\n**Mod:** {interaction.user}\n**Reason:** {reason or 'No reason'}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("No permission to kick."), ephemeral=True)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="Member to ban", reason="Reason (optional)", delete_days="Delete messages (0–7 days)")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "", delete_days: int = 0):
        if not await self._check_mod(interaction, "ban"):
            return
        if member.top_role >= interaction.user.top_role and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=_error("Cannot ban member with same/higher role."), ephemeral=True)
            return
        days = max(0, min(7, delete_days))
        delete_seconds = days * 86400 if days else 0
        try:
            await member.ban(reason=reason or f"Mod: {interaction.user}", delete_message_seconds=delete_seconds)
            await interaction.response.send_message(embed=_ok(f"Banned: {member}"))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderation: Ban",
                f"**Target:** {member} (`{member.id}`)\n**Mod:** {interaction.user}\n**Reason:** {reason or 'No reason'}\n**Delete messages:** {days} days",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("No permission to ban."), ephemeral=True)

    @app_commands.command(name="mute", description="Timeout a member")
    @app_commands.describe(member="Member to mute", minutes="Duration in minutes (1–40320)", reason="Reason (optional)")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, minutes: int = 60, reason: str = ""):
        if not await self._check_mod(interaction, "mute"):
            return
        duration = max(1, min(40320, minutes))
        until = datetime.now(timezone.utc) + timedelta(minutes=duration)
        try:
            await member.timeout(until, reason=reason or f"Mod: {interaction.user}")
            await interaction.response.send_message(embed=_ok(f"Muted {member} for {duration} min."))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderation: Mute",
                f"**Target:** {member} (`{member.id}`)\n**Mod:** {interaction.user}\n**Duration:** {duration} min\n**Reason:** {reason or 'No reason'}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("No permission to mute."), ephemeral=True)

    @app_commands.command(name="unmute", description="Remove member's timeout")
    @app_commands.describe(member="Member to unmute")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not await self._check_mod(interaction, "unmute"):
            return
        try:
            await member.timeout(None, reason=f"Mod: {interaction.user}")
            await interaction.response.send_message(embed=_ok(f"Unmuted: {member}"))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderation: Unmute",
                f"**Target:** {member} (`{member.id}`)\n**Mod:** {interaction.user}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("No permission to unmute."), ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(member="Member", reason="Reason (optional)")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = ""):
        if not await self._check_mod(interaction, "warn"):
            return
        database.add_warn(str(interaction.guild_id), str(member.id), str(interaction.user.id), reason)
        total = len(database.get_user_warns(str(interaction.guild_id), str(member.id)))
        await interaction.response.send_message(embed=_ok(f"Warned: {member}. Total warnings: {total}"))
        await send_guild_log(
            self.bot,
            interaction.guild,
            "mod_actions",
            "Moderation: Warn",
            f"**Target:** {member} (`{member.id}`)\n**Mod:** {interaction.user}\n**Reason:** {reason or 'No reason'}\n**Warnings:** {total}",
            color=discord.Color.orange(),
        )

    @app_commands.command(name="warnings", description="Show member's warnings")
    @app_commands.describe(member="Member")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        if not await self._check_mod(interaction, "warn"):
            return
        warns = database.get_user_warns(str(interaction.guild_id), str(member.id))
        if not warns:
            await interaction.response.send_message(embed=discord.Embed(color=discord.Color.blue(), description=f"{member} has no warnings."))
            return
        lines = []
        for i, w in enumerate(warns[:10], 1):
            ts = (w.get("created_at") or "")[:16] or "—"
            lines.append(f"**{i}.** {ts} – {w.get('reason','')[:80]}")
        embed = discord.Embed(
            title=f"Warnings: {member}",
            description="\n".join(lines) + (f"\n\n_+{len(warns)-10} more_" if len(warns) > 10 else ""),
            color=discord.Color.orange(),
        )
        embed.set_footer(text=f"Total {len(warns)} warnings")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearwarns", description="Clear all warnings from member")
    @app_commands.describe(member="Member")
    async def clearwarns(self, interaction: discord.Interaction, member: discord.Member):
        if not await self._check_mod(interaction, "warn"):
            return
        n = database.clear_warns(str(interaction.guild_id), str(member.id))
        await interaction.response.send_message(embed=_ok(f"Cleared {n} warnings from {member}."))
        if n:
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderation: Clear warns",
                f"**Target:** {member} (`{member.id}`)\n**Mod:** {interaction.user}\n**Cleared:** {n} warnings",
                color=discord.Color.orange(),
            )

    @app_commands.command(name="slowmode", description="Set channel slowmode (seconds between messages)")
    @app_commands.describe(seconds="Delay in seconds (0 = off, max 21600)", reason="Reason (optional)")
    async def slowmode(self, interaction: discord.Interaction, seconds: int = 0, reason: str = ""):
        if not await self._check_mod(interaction, "slowmode"):
            return
        delay = max(0, min(21600, seconds))
        try:
            await interaction.channel.edit(slowmode_delay=delay, reason=reason or f"Mod: {interaction.user}")
            if delay:
                msg = f"Slowmode set: {delay}s per message."
            else:
                msg = "Slowmode disabled."
            await interaction.response.send_message(embed=_ok(msg))
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderaatio: Slowmode",
                f"**Mod:** {interaction.user}\n**Channel:** <#{interaction.channel.id}>\n**Delay:** {delay}s\n**Reason:** {reason or 'No reason'}",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("No permission to edit channel."), ephemeral=True)

    @app_commands.command(name="say", description="Send message as bot (mod)")
    @app_commands.describe(message="Message to send")
    async def say(self, interaction: discord.Interaction, message: str):
        if not await self._check_mod(interaction, "say"):
            return
        msg = (message or "")[:2000]
        if not msg:
            await interaction.response.send_message(embed=_error("Enter a message."), ephemeral=True)
            return
        await interaction.response.send_message("✅ Message sent.", ephemeral=True)
        await interaction.channel.send(msg)
        await send_guild_log(
            self.bot,
            interaction.guild,
            "mod_actions",
            "Moderaatio: Say",
            f"**Mod:** {interaction.user}\n**Channel:** <#{interaction.channel.id}>\n**Message:** {msg[:300]}{'…' if len(msg) > 300 else ''}",
            color=discord.Color.blue(),
        )

    @app_commands.command(name="clear", description="Delete messages from channel")
    @app_commands.describe(amount="Number of messages to delete (1–100)", member="Filter by member (optional)")
    async def purge(self, interaction: discord.Interaction, amount: int, member: discord.Member | None = None):
        if not await self._check_mod(interaction, "purge"):
            return
        amt = max(1, min(100, amount))

        def check(m: discord.Message) -> bool:
            return (m.author.id == member.id) if member else True

        try:
            deleted = await interaction.channel.purge(limit=amt, check=check)
            await interaction.response.send_message(embed=_ok(f"Deleted {len(deleted)} messages."), ephemeral=True)
            await send_guild_log(
                self.bot,
                interaction.guild,
                "mod_actions",
                "Moderation: Clear",
                f"**Mod:** {interaction.user}\n**Channel:** <#{interaction.channel.id}>\n**Deleted:** {len(deleted)} messages",
                color=discord.Color.orange(),
            )
        except discord.Forbidden:
            await interaction.response.send_message(embed=_error("No permission to delete messages."), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ModeraatioCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg