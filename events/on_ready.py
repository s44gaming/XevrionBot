async def setup(bot):
    async def on_ready_handler():
        print(f"Botti kirjautunut: {bot.user} ({bot.user.id})")
        print(f"Palvelimia: {len(bot.guilds)}")

    bot.add_listener(on_ready_handler, "on_ready")
