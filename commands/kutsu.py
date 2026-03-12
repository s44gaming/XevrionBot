import discord
from discord import app_commands
from discord.ext import commands
from config import BOT_APPLY_URL, DISCORD_CLIENT_ID


class KutsuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="invite", description="Link to add bot to your server")
    async def kutsu(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "kutsu")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ This command is disabled on this server.",
                ephemeral=True
            )
            return
        url = (BOT_APPLY_URL or "").strip()
        if not url and (client_id := (DISCORD_CLIENT_ID or "").strip()):
            url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&scope=bot%20applications.commands"
        if not url:
            await interaction.response.send_message(
                "🔗 Bot invite link is not configured (DISCORD_CLIENT_ID missing). Admin can add BOT_APPLY_URL in dev portal.",
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"🔗 **Add bot to your server:**\n{url}",
            ephemeral=True
        )

    @app_commands.command(name="sendinvite", description="Create server invite link and send to channel")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        max_uses="How many times the link can be used (0 = unlimited)",
        expires_hours="Hours until link expires (0 = never)"
    )
    async def send_invite(
        self,
        interaction: discord.Interaction,
        max_uses: app_commands.Range[int, 0, 100] = 0,
        expires_hours: app_commands.Range[int, 0, 168] = 24,
    ):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "kutsuviesti")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ This command is disabled on this server.",
                ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "⚠️ This command can only be used in a server.",
                ephemeral=True
            )
            return

        if not isinstance(interaction.channel, discord.abc.GuildChannel):
            await interaction.response.send_message(
                "⚠️ This command can only be used in a server channel.",
                ephemeral=True
            )
            return

        # Varmistus: kutsu luodaan aina tälle palvelimelle (interaction.channel kuuluu interaction.guildiin)
        try:
            invite = await interaction.channel.create_invite(
                max_uses=max_uses if max_uses > 0 else 0,
                max_age=expires_hours * 3600 if expires_hours > 0 else 0,
                temporary=False,
            )
            url = str(invite)
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ I don't have permission to create invites for this channel.",
                ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"⚠️ Failed to create invite: {e}",
                ephemeral=True
            )
            return

        server_name = interaction.guild.name or "This server"
        await interaction.response.send_message("✅ Invite created and sent to channel.", ephemeral=True)
        await interaction.channel.send(
            f"🔗 **{server_name} – server invite:** {url}\n"
            f"_{invite.max_uses if invite.max_uses else 'Unlimited'} uses • "
            f"{'Never expires' if invite.max_age == 0 else f'Expires in {expires_hours}h'}_"
        )


async def setup(bot):
    await bot.add_cog(KutsuCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
