"""AFK – kun käyttäjä mainitaan ja on AFK, vastataan. Kun palaa, tyhjennetään AFK."""
import discord
import database


async def setup(bot):
    async def on_message(message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if not await bot.is_feature_enabled(message.guild.id, "afk"):
            return
        settings = bot.get_afk_settings(message.guild.id)
        if not settings.get("enabled", True):
            return
        # Jos lähettäjä palasi – poista AFK
        if database.clear_afk(str(message.guild.id), str(message.author.id)):
            try:
                await message.reply("Tervetuloa takaisin! Poistin AFK-tilasi.")
            except discord.Forbidden:
                pass
            return
        # Tarkista mainitut käyttäjät
        for member in message.mentions:
            if member.bot:
                continue
            afk_data = database.get_afk(str(message.guild.id), str(member.id))
            if afk_data:
                try:
                    await message.reply(
                        f"**{member.display_name}** on AFK: {afk_data.get('reason', 'AFK')}",
                        mention_author=False,
                    )
                except discord.Forbidden:
                    pass
                break

    bot.add_listener(on_message, "on_message")
