import discord
from discord import app_commands
from discord.ext import commands
from config import BOT_APPLY_URL, DISCORD_CLIENT_ID


class KutsuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kutsu", description="Linkki lisätä botti omaan palvelimeen")
    async def kutsu(self, interaction: discord.Interaction):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "kutsu")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella.",
                ephemeral=True
            )
            return
        url = (BOT_APPLY_URL or "").strip()
        if not url and (client_id := (DISCORD_CLIENT_ID or "").strip()):
            url = f"https://discord.com/api/oauth2/authorize?client_id={client_id}&scope=bot%20applications.commands"
        if not url:
            await interaction.response.send_message(
                "🔗 Botin kutsulinkkiä ei ole asetettu eikä sitä voi luoda (DISCORD_CLIENT_ID puuttuu). Ylläpitäjä voi lisätä BOT_APPLY_URL:n kehittäjäportaalista.",
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            f"🔗 **Lisää botti omaan palvelimeen:**\n{url}",
            ephemeral=True
        )

    @app_commands.command(name="lähetäkutsu", description="Luo palvelimelle uuden kutsulinkin ja lähettää sen kanavalle")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(
        max_käyttöä="Kuinka monta kertaa linkkiä voi käyttää (0 = rajaton)",
        vanhenee_tunneissa="Kuinka monessa tunnissa linkki vanhenee (0 = ei vanhene)"
    )
    async def laheta_kutsu(
        self,
        interaction: discord.Interaction,
        max_käyttöä: app_commands.Range[int, 0, 100] = 0,
        vanhenee_tunneissa: app_commands.Range[int, 0, 168] = 24,
    ):
        enabled = await self.bot.is_feature_enabled(interaction.guild_id, "kutsuviesti")
        if not enabled:
            await interaction.response.send_message(
                "⚠️ Tämä komento on poistettu käytöstä tällä palvelimella.",
                ephemeral=True
            )
            return

        if not interaction.guild:
            await interaction.response.send_message(
                "⚠️ Tätä komentoa voi käyttää vain palvelimen sisällä.",
                ephemeral=True
            )
            return

        if not isinstance(interaction.channel, discord.abc.GuildChannel):
            await interaction.response.send_message(
                "⚠️ Tätä komentoa voi käyttää vain palvelimen kanavalla.",
                ephemeral=True
            )
            return

        # Varmistus: kutsu luodaan aina tälle palvelimelle (interaction.channel kuuluu interaction.guildiin)
        try:
            invite = await interaction.channel.create_invite(
                max_uses=max_käyttöä if max_käyttöä > 0 else 0,
                max_age=vanhenee_tunneissa * 3600 if vanhenee_tunneissa > 0 else 0,
                temporary=False,
            )
            url = str(invite)
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ Minulla ei ole oikeuksia luoda kutsulinkkejä tälle kanavalle. Tarkista, että botti voi luoda kutsu-linkkejä.",
                ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"⚠️ Kutsulinkin luonti epäonnistui: {e}",
                ephemeral=True
            )
            return

        palvelin_nimi = interaction.guild.name or "Tämä palvelin"
        await interaction.response.send_message("✅ Kutsulinkki luotu ja lähetetty kanavalle.", ephemeral=True)
        await interaction.channel.send(
            f"🔗 **{palvelin_nimi} – palvelimen kutsu:** {url}\n"
            f"_{invite.max_uses if invite.max_uses else 'Rajaton'} käyttökertaa • "
            f"{'Ei vanhenemista' if invite.max_age == 0 else f'Vanhenee {vanhenee_tunneissa}h kuluttua'}_"
        )


async def setup(bot):
    await bot.add_cog(KutsuCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
