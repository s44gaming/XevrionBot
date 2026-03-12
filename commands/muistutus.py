"""Muistutusjärjestelmä – /muistutus muistuttaa myöhemmin."""
import re
import time
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import database


def _parse_duration(s: str) -> int | None:
    """Palauttaa sekunnit tai None. Esim: 5m, 1h, 30s, 1h30m."""
    s = (s or "").strip().lower()
    if not s:
        return None
    total = 0
    for m in re.finditer(r"(\d+)\s*(s|m|h|d|min|sec|minute|hour|day|minuutti|tunti|päivä)", s):
        n = int(m.group(1))
        u = m.group(2)
        if u in ("s", "sec"):
            total += n
        elif u in ("m", "min", "minute", "minuutti"):
            total += n * 60
        elif u in ("h", "hour", "tunti"):
            total += n * 3600
        elif u in ("d", "day", "päivä"):
            total += n * 86400
    return total if total > 0 else None


class MuistutusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_reminder: dict[tuple[int, int], float] = {}

    @app_commands.command(name="reminder", description="Set a reminder")
    @app_commands.describe(
        duration="Duration, e.g. 5m, 1h, 30s, 1h30m",
        message="What to remind (optional)"
    )
    async def reminder(
        self,
        interaction: discord.Interaction,
        duration: str,
        message: str = "Reminder!",
    ):
        if not interaction.guild:
            await interaction.response.send_message("Cannot use in DMs.", ephemeral=True)
            return
        if not await self.bot.is_feature_enabled(interaction.guild_id, "muistutus"):
            await interaction.response.send_message(
                "⚠️ Reminder is disabled.",
                ephemeral=True,
            )
            return
        settings = self.bot.get_reminder_settings(interaction.guild_id)
        if not settings.get("enabled", True):
            await interaction.response.send_message(
                "⚠️ Reminder is disabled on this server.",
                ephemeral=True,
            )
            return
        sec = _parse_duration(duration)
        if not sec or sec < 10:
            await interaction.response.send_message(
                "❌ Use format e.g. 5m, 1h, 30s. Minimum 10 seconds.",
                ephemeral=True,
            )
            return
        if sec > 86400 * 7:  # max 7 päivää
            await interaction.response.send_message(
                "❌ Maximum 7 days.",
                ephemeral=True,
            )
            return
        max_per = settings.get("max_per_user", 5)
        count = database.count_user_reminders(str(interaction.guild_id), str(interaction.user.id))
        if count >= max_per:
            await interaction.response.send_message(
                f"❌ You already have {count} active reminders (max {max_per}).",
                ephemeral=True,
            )
            return
        cooldown = settings.get("cooldown_sec", 60)
        key = (interaction.guild_id, interaction.user.id)
        now = time.time()
        if (now - self._last_reminder.get(key, 0)) < cooldown:
            await interaction.response.send_message(
                f"❌ Wait {cooldown} seconds before next reminder.",
                ephemeral=True,
            )
            return
        self._last_reminder[key] = now
        fire_at = now + sec
        rid = database.add_reminder(
            str(interaction.guild_id),
            str(interaction.user.id),
            str(interaction.channel_id),
            (message or "Reminder!")[:500],
            fire_at,
        )
        mins = sec // 60
        secs = sec % 60
        time_str = f"{mins} min" if mins else f"{secs} s"
        await interaction.response.send_message(
            f"✅ Reminder set! I'll remind you in {time_str}: **{(message or 'Reminder!')[:100]}**",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(MuistutusCog(bot))
