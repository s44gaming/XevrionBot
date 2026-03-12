"""
Reaction roles – reagoi emojilla viestiin ja saat roolin.
Web-dashboardista määritellään: viestin ID, kanava, emoji, rooli.
"""
import discord


async def setup(bot):
    async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
        if payload.user_id == bot.user.id or not payload.guild_id:
            return
        settings = bot.get_reaction_roles_settings(payload.guild_id)
        if not settings.get("enabled"):
            return
        emoji_str = str(payload.emoji)
        for r in settings.get("roles", []):
            if (
                str(r.get("message_id")) == str(payload.message_id)
                and str(r.get("channel_id")) == str(payload.channel_id)
                and str(r.get("emoji")) == emoji_str
            ):
                guild = bot.get_guild(payload.guild_id)
                if not guild:
                    return
                member = guild.get_member(payload.user_id)
                role = guild.get_role(int(r.get("role_id", 0)))
                if member and role and role < guild.me.top_role:
                    try:
                        await member.add_roles(role, reason="Reaction role")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                break

    async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
        if payload.user_id == bot.user.id or not payload.guild_id:
            return
        settings = bot.get_reaction_roles_settings(payload.guild_id)
        if not settings.get("enabled"):
            return
        emoji_str = str(payload.emoji)
        for r in settings.get("roles", []):
            if (
                str(r.get("message_id")) == str(payload.message_id)
                and str(r.get("channel_id")) == str(payload.channel_id)
                and str(r.get("emoji")) == emoji_str
            ):
                guild = bot.get_guild(payload.guild_id)
                if not guild:
                    return
                member = guild.get_member(payload.user_id)
                role = guild.get_role(int(r.get("role_id", 0)))
                if member and role:
                    try:
                        await member.remove_roles(role, reason="Reaction role removed")
                    except (discord.Forbidden, discord.HTTPException):
                        pass
                break

    bot.add_listener(on_raw_reaction_add, "on_raw_reaction_add")
    bot.add_listener(on_raw_reaction_remove, "on_raw_reaction_remove")
