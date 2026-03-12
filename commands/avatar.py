"""
Avatar-komento – näytä käyttäjän profiilikuva.
"""
import discord
from discord import app_commands
from discord.ext import commands


class AvatarCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Show user's profile picture")
    @app_commands.describe(user="User (optional, defaults to you)")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member | discord.User | None = None):
        if interaction.guild_id and not await self.bot.is_feature_enabled(interaction.guild_id, "avatar"):
            await interaction.response.send_message(
                "⚠️ This command is disabled. Enable in web dashboard.",
                ephemeral=True,
            )
            return
        user = user or interaction.user
        avatar_url = user.display_avatar.replace(size=1024).url
        embed = discord.Embed(
            title=f"Avatar: {user.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_image(url=avatar_url)
        embed.add_field(name="Download", value=f"[PNG]({user.display_avatar.replace(format='png', size=1024).url}) | [JPG]({user.display_avatar.replace(format='jpg', size=1024).url}) | [WEBP]({user.display_avatar.replace(format='webp', size=1024).url})", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(AvatarCog(bot))
