"""Arvontajärjestelmä – /arvonta valitsee voittajat."""
import random
import discord
from discord import app_commands
from discord.ext import commands


class ArvontaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="arvonta", description="Arvo voittajat viestistä (vaatii mod-oikeudet)")
    @app_commands.describe(
        määrä="Montako voittajaa arvotaan (1–20)",
        viestin_id="Viestin ID josta arvotaan (reagoijat mukaan)"
    )
    async def arvonta(
        self,
        interaction: discord.Interaction,
        määrä: app_commands.Range[int, 1, 20],
        viestin_id: str,
    ):
        if not interaction.guild:
            await interaction.response.send_message("Tätä ei voi käyttää DM:ssä.", ephemeral=True)
            return
        if not await self.bot.is_feature_enabled(interaction.guild_id, "arvonta"):
            await interaction.response.send_message(
                "⚠️ Arvonta on poistettu käytöstä.",
                ephemeral=True,
            )
            return
        if not self.bot.has_mod_permission(interaction.user):
            await interaction.response.send_message(
                "❌ Sinulla ei ole oikeuksia käyttää tätä komentoa.",
                ephemeral=True,
            )
            return
        settings = self.bot.get_giveaway_settings(interaction.guild_id)
        if not settings.get("enabled", True):
            await interaction.response.send_message(
                "⚠️ Arvonta on poistettu käytöstä tällä palvelimella.",
                ephemeral=True,
            )
            return
        try:
            msg_id = int(viestin_id.strip())
        except ValueError:
            await interaction.response.send_message(
                "❌ Virheellinen viestin ID.",
                ephemeral=True,
            )
            return
        try:
            message = await interaction.channel.fetch_message(msg_id)
        except discord.NotFound:
            await interaction.response.send_message(
                "❌ Viestiä ei löydy tältä kanavalta.",
                ephemeral=True,
            )
            return
        users = set()
        for reaction in message.reactions:
            async for user in reaction.users():
                if not user.bot and isinstance(user, discord.Member):
                    users.add(user)
        users = list(users)
        if len(users) < määrä:
            await interaction.response.send_message(
                f"❌ Vain {len(users)} reagoijaa. Tarvitaan vähintään {määrä}.",
                ephemeral=True,
            )
            return
        winners = random.sample(users, määrä)
        names = ", ".join(w.mention for w in winners)
        embed = discord.Embed(
            title="🎉 Arvonta valmis!",
            description=f"**{määrä}** voittajaa viestistä: {message.jump_url}\n\n**Voittajat:** {names}",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ArvontaCog(bot))
