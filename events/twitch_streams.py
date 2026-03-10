"""Twitch stream -ilmoitukset: taustatehtävä pollaa Twitch API ja lähettää Discord-viestin kun stream alkaa."""
import asyncio
import database
import discord
import twitch_streams as twitch_api

POLL_INTERVAL = 120  # sekuntia
_state: dict[tuple[str, str], bool] = {}  # (guild_id, user_login) -> was_online


def _gather_streamers_by_guild(bot) -> dict[str, list[tuple[str, int]]]:
    """Kerää kaikki guild_id -> [(user_login, channel_id), ...] joilla on streamereitä ja kanava."""
    result = {}
    for guild in bot.guilds:
        gid = str(guild.id)
        if not database.is_feature_enabled(gid, "twitch"):
            continue
        settings = database.get_twitch_settings(gid)
        streamers = settings.get("streamers") or []
        channel_id = settings.get("channel_id")
        if not streamers or not channel_id:
            continue
        try:
            ch_id = int(channel_id)
            for login in streamers:
                if login:
                    result.setdefault(gid, []).append((login, ch_id))
        except (ValueError, TypeError):
            pass
    return result


async def _poll_and_notify(bot):
    """Pollaa Twitch API ja lähettää ilmoitukset uusista streameistä."""
    if not twitch_api.is_twitch_configured():
        return
    by_guild = _gather_streamers_by_guild(bot)
    all_logins = list({login for items in by_guild.values() for login, _ in items})
    if not all_logins:
        return
    live = twitch_api.fetch_live_streams(all_logins)
    live_by_login = {s["user_login"].lower(): s for s in live}

    for gid, items in by_guild.items():
        for user_login, channel_id in items:
            key = (gid, user_login.lower())
            is_live = user_login.lower() in live_by_login
            was_live = _state.get(key, False)
            _state[key] = is_live
            if is_live and not was_live:
                s = live_by_login.get(user_login.lower(), {})
                await _send_stream_embed(bot, channel_id, s)


async def _send_stream_embed(bot, channel_id: int, stream_data: dict):
    """Lähettää Discord-embedin streamista."""
    try:
        channel = bot.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return
        user_name = stream_data.get("user_name", "Unknown")
        title = stream_data.get("title") or f"{user_name} on nyt livessä!"
        game = stream_data.get("game_name") or ""
        thumbnail = (stream_data.get("thumbnail_url") or "").replace("{width}", "1280").replace("{height}", "720")
        url = f"https://www.twitch.tv/{stream_data.get('user_login', user_name)}"
        viewer_count = stream_data.get("viewer_count", 0)

        embed = discord.Embed(
            title=title[:256],
            url=url,
            color=0x9146FF,
            description=f"**{user_name}** aloitti striimin!"
        )
        if game:
            embed.add_field(name="Peli", value=game, inline=True)
        embed.add_field(name="Katsojia", value=str(viewer_count), inline=True)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.set_author(name=user_name, url=url, icon_url=None)

        await channel.send(embed=embed)
    except Exception:
        pass


async def _twitch_loop(bot):
    """Pääsilmukka: pollaa säännöllisesti."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await _poll_and_notify(bot)
        except Exception:
            pass
        await asyncio.sleep(POLL_INTERVAL)


async def setup(bot):
    asyncio.create_task(_twitch_loop(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
