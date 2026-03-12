"""
FiveM-palvelimen tila. Asetukset web-dashboardista (host + port).
"""
import discord
from discord import app_commands
from discord.ext import commands
import fivem_status


class FivemCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fivem", description="Show FiveM server status (settings from web)")
    @app_commands.describe(send_to_channel="Send status to configured channel (requires manage server)")
    async def fivem(self, interaction: discord.Interaction, send_to_channel: bool = False):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "fivem")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ FiveM status is disabled on this server. Enable in web dashboard.",
                ephemeral=True
            )
            return
        settings = self.bot.get_fivem_settings(interaction.guild_id)
        host, port = settings.get("host", ""), settings.get("port", "30120")
        if not host:
            await interaction.response.send_message(
                "❌ FiveM server not configured. Set host and port in web dashboard.",
                ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        result = fivem_status.fetch_fivem_status(host, port)
        if result is None:
            await interaction.followup.send("❌ Could not fetch server info.", ephemeral=True)
            return
        if not result.get("online"):
            await interaction.followup.send(
                f"❌ **FiveM server** ({host}:{port})\n{result.get('error', 'No connection.')}",
                ephemeral=True
            )
            return
        hostname = result.get("hostname", "FiveM")
        players = result.get("players", 0)
        max_p = result.get("max", 48)
        map_name = result.get("map", "–")
        embed = discord.Embed(
            title=f"🎮 {hostname}",
            description=f"**{host}:{port}**",
            color=discord.Color.green()
        )
        embed.add_field(name="Players", value=f"{players} / {max_p}", inline=True)
        embed.add_field(name="Map", value=map_name, inline=True)

        channel_id = settings.get("channel_id")
        if send_to_channel and channel_id and interaction.user.guild_permissions.manage_guild:
            channel = interaction.guild.get_channel(int(channel_id))
            if channel:
                try:
                    await channel.send(embed=embed)
                    await interaction.followup.send(f"✅ Status sent to {channel.mention}", ephemeral=True)
                except discord.Forbidden:
                    await interaction.followup.send("❌ No permission to send to that channel.", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            else:
                await interaction.followup.send("❌ Channel not found. Check web settings.", ephemeral=True)
        else:
            msg = "ℹ️ Set status channel in web dashboard (FiveM settings) to send there." if send_to_channel and not channel_id else None
            await interaction.followup.send(embed=embed, ephemeral=True)
            if msg:
                await interaction.followup.send(msg, ephemeral=True)


async def setup(bot):
    await bot.add_cog(FivemCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
