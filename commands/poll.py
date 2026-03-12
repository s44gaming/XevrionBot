"""
Äänestys-komento – luo äänestyksen kanavalle. Kytkettävissä web-dashboardista.
"""
import discord
from discord import app_commands
from discord.ext import commands


class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Create a poll (1–10 options)")
    @app_commands.describe(
        question="Poll question",
        options="Options separated by comma (e.g. Yes,No,Maybe)",
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        question: str,
        options: str,
    ):
        if not await self.bot.is_feature_enabled(interaction.guild_id, "poll"):
            await interaction.response.send_message(
                "⚠️ Poll is disabled on this server. Enable it in web dashboard.",
                ephemeral=True,
            )
            return
        opts = [x.strip() for x in options.split(",") if x.strip()]
        if len(opts) < 2:
            await interaction.response.send_message(
                "Give at least two options separated by comma.",
                ephemeral=True,
            )
            return
        if len(opts) > 10:
            await interaction.response.send_message("Maximum 10 options.", ephemeral=True)
            return
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = [f"{emojis[i]} {opts[i]}" for i in range(len(opts))]
        embed = discord.Embed(
            title=f"📊 {question[:256]}",
            description="\n".join(lines),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Poll by: {interaction.user}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(opts)):
            await msg.add_reaction(emojis[i])


async def setup(bot):
    await bot.add_cog(PollCog(bot))
