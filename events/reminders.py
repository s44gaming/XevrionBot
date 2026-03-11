"""Muistutukset – taustatehtävä tarkistaa vuoronumerot ja lähettää muistutukset."""
import time
import asyncio
import discord
import database


async def _reminder_loop(bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            now = time.time()
            for r in database.get_due_reminders(now):
                try:
                    channel = await bot.fetch_channel(r["channel_id"])
                    if not isinstance(channel, discord.TextChannel):
                        continue
                    user = await bot.fetch_user(int(r["user_id"]))
                    msg = (r.get("message") or "Muistutus!")[:500]
                    await channel.send(f"{user.mention} **Muistutus:** {msg}")
                except (discord.NotFound, discord.Forbidden):
                    pass
                database.delete_reminder(r["id"])
        except Exception:
            pass
        await asyncio.sleep(10)


async def setup(bot):
    asyncio.create_task(_reminder_loop(bot))
