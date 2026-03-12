"""
Userinfo-komento – näytä käyttäjän tiedot.
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone


class UserinfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Show user details")
    @app_commands.describe(user="User (optional)")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member | None = None):
        if not interaction.guild:
            await interaction.response.send_message("Use in a server.", ephemeral=True)
            return
        if not await self.bot.is_feature_enabled(interaction.guild_id, "userinfo"):
            await interaction.response.send_message(
                "⚠️ This command is disabled. Enable in web dashboard.",
                ephemeral=True,
            )
            return
        member = user or (interaction.user if isinstance(interaction.user, discord.Member) else None)
        if not member:
            await interaction.response.send_message("User not found.", ephemeral=True)
            return
        roles = [r.mention for r in member.roles if r != interaction.guild.default_role][:15]
        roles_str = ", ".join(roles) if roles else "–"
        if len(roles) == 15:
            roles_str += "..."
        join_str = member.joined_at.strftime("%d.%m.%Y %H:%M") if member.joined_at else "–"
        created_str = member.created_at.strftime("%d.%m.%Y %H:%M")
        embed = discord.Embed(
            title=str(member),
            color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Nickname", value=member.display_name, inline=True)
        embed.add_field(name="Joined", value=join_str, inline=True)
        embed.add_field(name="Account created", value=created_str, inline=True)
        embed.add_field(name="Roles", value=roles_str[:1024] or "–", inline=False)
        if member.voice and member.voice.channel:
            embed.add_field(name="Voice channel", value=member.voice.channel.mention, inline=True)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(UserinfoCog(bot))
