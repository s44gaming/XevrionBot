"""
Starboard – viestit joissa tarpeeksi ⭐ reaktioita kopioidaan erikoiselle kanavalle.
"""
import discord

# Viesti ID -> starboard-viestin ID (että voidaan päivittää tähtimäärä)
_STARBOARD_MSG: dict[tuple[int, int], int] = {}
_CAP = 1000


def _track(msg_key: tuple[int, int], starboard_msg_id: int):
    global _STARBOARD_MSG
    if len(_STARBOARD_MSG) >= _CAP:
        _STARBOARD_MSG.clear()
    _STARBOARD_MSG[msg_key] = starboard_msg_id


def _get_tracked(msg_key: tuple[int, int]) -> int | None:
    return _STARBOARD_MSG.get(msg_key)


def _get_star_count(message: discord.Message) -> int:
    for r in message.reactions:
        if str(r.emoji) == "⭐":
            return r.count
    return 0


async def _refresh_starboard_embed(bot, channel: discord.TextChannel, msg: discord.Message, starboard_msg_id: int):
    try:
        starboard_msg = await channel.fetch_message(starboard_msg_id)
    except (discord.NotFound, discord.Forbidden):
        return
    count = _get_star_count(msg)
    embed = starboard_msg.embeds[0] if starboard_msg.embeds else discord.Embed()
    embed.set_footer(text=f"⭐ {count} | #{msg.channel.name if isinstance(msg.channel, discord.TextChannel) else 'DM'}")
    try:
        await starboard_msg.edit(embed=embed)
    except discord.Forbidden:
        pass


async def setup(bot):
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐" or not payload.guild_id:
            return
        settings = bot.get_starboard_settings(payload.guild_id)
        ch_id = settings.get("channel_id")
        min_stars = settings.get("min_stars", 3)
        if not ch_id:
            return
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except (discord.NotFound, discord.Forbidden):
            return
        if not isinstance(channel, discord.TextChannel) or payload.channel_id == int(ch_id):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return
        count = _get_star_count(message)
        if count < min_stars:
            return
        starboard_ch = await bot.fetch_channel(int(ch_id))
        if not isinstance(starboard_ch, discord.TextChannel):
            return
        msg_key = (payload.guild_id, payload.message_id)
        existing = _get_tracked(msg_key)
        if existing:
            await _refresh_starboard_embed(bot, starboard_ch, message, existing)
            return
        jump = message.jump_url
        embed = discord.Embed(
            description=(message.content or "")[:1900] or "_[Sisältö ei tekstimuodossa]_",
            color=discord.Color.gold(),
            timestamp=message.created_at,
        )
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url if message.author else None)
        embed.add_field(name="Lähde", value=f"[Siirry viestiin]({jump})", inline=False)
        embed.set_footer(text=f"⭐ {count} | #{channel.name}")
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        try:
            sent = await starboard_ch.send(embed=embed)
            _track(msg_key, sent.id)
        except discord.Forbidden:
            pass

    async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐" or not payload.guild_id:
            return
        settings = bot.get_starboard_settings(payload.guild_id)
        ch_id = settings.get("channel_id")
        if not ch_id:
            return
        msg_key = (payload.guild_id, payload.message_id)
        existing = _get_tracked(msg_key)
        if not existing:
            return
        try:
            channel = await bot.fetch_channel(payload.channel_id)
        except (discord.NotFound, discord.Forbidden):
            return
        if not isinstance(channel, discord.TextChannel):
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden):
            return
        starboard_ch = await bot.fetch_channel(int(ch_id))
        if not isinstance(starboard_ch, discord.TextChannel):
            return
        count = _get_star_count(message)
        min_stars = settings.get("min_stars", 3)
        if count < min_stars:
            try:
                msg = await starboard_ch.fetch_message(existing)
                await msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
            _STARBOARD_MSG.pop(msg_key, None)
        else:
            await _refresh_starboard_embed(bot, starboard_ch, message, existing)

    bot.add_listener(on_raw_reaction_add, "on_raw_reaction_add")
    bot.add_listener(on_raw_reaction_remove, "on_raw_reaction_remove")

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
