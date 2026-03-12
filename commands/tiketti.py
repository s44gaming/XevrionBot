"""
Tikettijärjestelmä. Staff-rooli, kategoria, kanava, tiketin aiheet ja transcript-kanava määritetään web-dashboardista.
Kuvien mukaan: embed "Tukitiketti", ohje "Valitse tiketin aihe alta", pudotusvalikko aiheilla (otsikko, kuvaus, emoji).
"""
import discord
from datetime import datetime
from discord import app_commands
from discord.ext import commands
import database


def _error(msg: str) -> discord.Embed:
    return discord.Embed(color=discord.Color.red(), description=f"❌ {msg}")


def _slug(s: str, max_len: int = 20) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "" for c in s)[:max_len] or "tiketti"
    return safe.lower()


class TicketTopicSelect(discord.ui.Select):
    """Pudotusvalikko: Valitse tiketin aihe."""
    def __init__(self, bot, topics: list | None = None):
        if topics is None:
            topics = []
        options = []
        for i, t in enumerate((topics or [])[:25]):  # Discord max 25
            label = (t.get("label") or "Tiketti")[:100]
            desc = (t.get("description") or "")[:100]
            emoji = (t.get("emoji") or "").strip()
            opt = discord.SelectOption(label=label, value=str(i), description=desc or None)
            if emoji:
                try:
                    opt.emoji = emoji
                except Exception:
                    pass
            options.append(opt)
        if not options:
            options = [discord.SelectOption(label="Tiketti", value="0", description="Avaa tiketti")]
        super().__init__(
            custom_id="ticket_topic_select",
            placeholder="Valitse tiketin aihe",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.bot = bot
        self._topics = topics or []

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Tikettejä voi avata vain palvelimella.", ephemeral=True
            )
        if not await self.bot.is_feature_enabled(interaction.guild_id, "tiketti"):
            return await interaction.response.send_message(
                "Tikettijärjestelmä on poissa käytöstä.", ephemeral=True
            )
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        ch_id = settings.get("channel_id")
        cat_id = settings.get("category_id")
        role_id = settings.get("staff_role_id")
        if not ch_id or not cat_id or not role_id:
            return await interaction.response.send_message(
                "Tiketti-asetukset puuttuvat. Aseta web-dashboardista rooli, kategoria ja kanava.",
                ephemeral=True
            )
        if str(interaction.channel_id) != str(ch_id):
            return await interaction.response.send_message(
                f"Avaa tiketti kanavalla <#{ch_id}>.", ephemeral=True
            )

        topics = settings.get("ticket_topics") or self._topics
        if not topics:
            return await interaction.response.send_message(
                "Tiketin aiheita ei ole määritelty. Lisää aiheet web-dashboardista.", ephemeral=True
            )
        idx = int(self.values[0])
        if idx < 0 or idx >= len(topics):
            return await interaction.response.send_message("Virheellinen valinta.", ephemeral=True)
        topic = topics[idx]
        topic_label = topic.get("label") or "Tiketti"
        topic_desc = topic.get("description") or ""

        await interaction.response.defer(ephemeral=True)

        category = interaction.guild.get_channel(int(cat_id))
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send(
                "Tiketin kategoriaa ei löydy.", ephemeral=True
            )
        staff_role = interaction.guild.get_role(int(role_id))
        if not staff_role:
            return await interaction.followup.send(
                "Staff-roolia ei löydy.", ephemeral=True
            )

        safe_name = _slug(interaction.user.display_name, 12) or "user"
        topic_slug = _slug(topic_label, 15)
        name = f"tiketti-{topic_slug}-{safe_name}-{interaction.user.id % 10000}"
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        topic_role_id = topic.get("role_id")
        if topic_role_id:
            topic_role = interaction.guild.get_role(int(topic_role_id))
            if topic_role:
                overwrites[topic_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        try:
            channel = await interaction.guild.create_text_channel(
                name=name,
                category=category,
                overwrites=overwrites,
            )
        except discord.Forbidden:
            return await interaction.followup.send("Ei oikeuksia luoda kanavia.", ephemeral=True)

        embed = discord.Embed(
            title="Tiketti avattu",
            description=f"Tervetuloa {interaction.user.mention}!\n\n**Aihe:** {topic_label}\n{topic_desc}\n\nKuvatko ongelma tai kysymyksesi alle. Staff vastaa pian.",
            color=discord.Color.green(),
        )
        close_view = TicketCloseView(self.bot)
        await channel.send(content=interaction.user.mention, embed=embed, view=close_view)
        await interaction.followup.send(f"Tiketti avattu: {channel.mention}", ephemeral=True)
        # Päivitä paneeli uudella näkymällä jotta valinta ei jää aktiiviseksi
        try:
            fresh_view = TicketOpenView(self.bot, guild_id=interaction.guild_id)
            await interaction.message.edit(view=fresh_view)
        except discord.Forbidden:
            pass


class TicketOpenButton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.primary, label="Avaa tiketti", custom_id="ticket_open")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(
                "Tikettejä voi avata vain palvelimella.", ephemeral=True
            )
        if not await self.bot.is_feature_enabled(interaction.guild_id, "tiketti"):
            return await interaction.response.send_message(
                "Tikettijärjestelmä on poissa käytöstä.", ephemeral=True
            )
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        ch_id = settings.get("channel_id")
        cat_id = settings.get("category_id")
        role_id = settings.get("staff_role_id")
        if not ch_id or not cat_id or not role_id:
            return await interaction.response.send_message(
                "Tiketti-asetukset puuttuvat. Aseta web-dashboardista rooli, kategoria ja kanava.",
                ephemeral=True
            )
        ch_str = str(ch_id)
        if str(interaction.channel_id) != ch_str:
            return await interaction.response.send_message(
                f"Avaa tiketti kanavalla <#{ch_str}>.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        category = interaction.guild.get_channel(int(cat_id))
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send(
                "Tiketin kategoriaa ei löydy.", ephemeral=True
            )

        staff_role = interaction.guild.get_role(int(role_id))
        if not staff_role:
            return await interaction.followup.send(
                "Staff-roolia ei löydy.", ephemeral=True
            )

        safe_name = "".join(c if c.isalnum() or c in "-_" else "" for c in interaction.user.display_name)[:12] or "user"
        name = f"tiketti-{safe_name}-{interaction.user.id % 10000}"
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        try:
            channel = await interaction.guild.create_text_channel(
                name=name,
                category=category,
                overwrites=overwrites,
            )
        except discord.Forbidden:
            return await interaction.followup.send("Ei oikeuksia luoda kanavia.", ephemeral=True)

        embed = discord.Embed(
            title="Tiketti avattu",
            description=f"Tervetuloa {interaction.user.mention}! Kuvatko ongelma tai kysymyksesi alle.\nStaff vastaa pian.",
            color=discord.Color.green(),
        )
        close_view = TicketCloseView(self.bot)
        await channel.send(content=interaction.user.mention, embed=embed, view=close_view)
        await interaction.followup.send(f"Tiketti avattu: {channel.mention}", ephemeral=True)


class TicketOpenView(discord.ui.View):
    """Näyttää joko pudotusvalikon (aiheet) tai yhden nappulan (ei aiheita)."""
    def __init__(self, bot, guild_id: int | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        if guild_id is not None:
            settings = bot.get_ticket_settings(guild_id)
            topics = settings.get("ticket_topics") or []
            if topics:
                self.add_item(TicketTopicSelect(bot, topics))
                return
        self.add_item(TicketOpenButton(bot))


def _format_msg(msg: discord.Message) -> str:
    ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
    author = msg.author.display_name or str(msg.author)
    content = (msg.content or "").strip()
    lines = [f"[{ts}] {author}: {content}"]
    for a in msg.attachments:
        lines.append(f"  (liite: {a.url})")
    for e in msg.embeds:
        lines.append(f"  (embed: {e.title or 'ei otsikkoa'})")
    return "\n".join(lines)


class TicketCloseButton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.danger, label="Sulje tiketti", custom_id="ticket_close")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild or not isinstance(interaction.channel, discord.TextChannel):
            return
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        role_id = settings.get("staff_role_id")
        if not role_id:
            return await interaction.response.send_message("Staff-roolia ei määritetty.", ephemeral=True)
        staff_role = interaction.guild.get_role(int(role_id))
        if not staff_role or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message("Et voi sulkea tätä tiketin.", ephemeral=True)
        if staff_role not in interaction.user.roles and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Vain staff voi sulkea tiketin.", ephemeral=True)
        await interaction.response.send_message("Tiketti suljetaan...", ephemeral=True)

        transcript_ch_id = settings.get("transcript_channel_id")
        if transcript_ch_id:
            try:
                transcript_ch = await self.bot.fetch_channel(int(transcript_ch_id))
                if isinstance(transcript_ch, discord.TextChannel):
                    lines = [f"=== Tiketti suljettu: #{interaction.channel.name} ===",
                             f"Sulkenut: {interaction.user.display_name} ({interaction.user.id})",
                             f"Aika: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
                             ""]
                    async for msg in interaction.channel.history(limit=500, oldest_first=True):
                        lines.append(_format_msg(msg))
                    text = "\n".join(lines)
                    from io import BytesIO
                    buf = BytesIO(text.encode("utf-8"))
                    buf.seek(0)
                    await transcript_ch.send(
                        content=f"📋 Transcript: {interaction.channel.name}",
                        file=discord.File(buf, filename=f"transcript-{interaction.channel.name}.txt"),
                    )
            except (discord.Forbidden, discord.NotFound, ValueError):
                pass

        try:
            await interaction.channel.delete(reason=f"Tiketti suljettu: {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send("Ei oikeuksia poistaa kanavaa.", ephemeral=True)


class TicketCloseView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketCloseButton(bot))


class TikettiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="tiketti_paneeli", description="Lähettää tiketti-paneelin webissä valitulle kanavalle")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Vain palvelimella.", ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Vain ylläpitäjät voivat käyttää.", ephemeral=True)
        if not await self.bot.is_feature_enabled(interaction.guild_id, "tiketti"):
            return await interaction.response.send_message(
                "Tikettijärjestelmä on poissa käytöstä (web-dashboard).", ephemeral=True
            )
        settings = self.bot.get_ticket_settings(interaction.guild_id)
        ch_id = settings.get("channel_id")
        if not ch_id or not settings.get("category_id") or not settings.get("staff_role_id"):
            return await interaction.response.send_message(
                "Aseta web-dashboardista: staff-rooli, kategoria ja kanava.",
                ephemeral=True
            )

        try:
            target_channel = await self.bot.fetch_channel(int(ch_id))
        except (discord.NotFound, discord.Forbidden):
            return await interaction.response.send_message(
                "Tiketti-kanavaa ei löydy. Tarkista web-asetukset.",
                ephemeral=True
            )
        if not isinstance(target_channel, discord.TextChannel):
            return await interaction.response.send_message(
                "Valittu kanava ei ole tekstikanava.",
                ephemeral=True
            )

        panel_title = settings.get("panel_title") or "Tukitiketti"
        panel_description = settings.get("panel_description") or "Valitse tiketin aihe alta."
        embed = discord.Embed(
            title=panel_title,
            description=panel_description,
            color=discord.Color.blue(),
        )
        view = TicketOpenView(self.bot, guild_id=interaction.guild_id)
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"Tiketti-paneeli lähetetty kanavalle {target_channel.mention}.",
            ephemeral=True
        )


class TicketOpenViewWithSelect(discord.ui.View):
    """Pysyvä näkymä vain Selectille (custom_id), jotta vanhat paneelit toimivat uudelleenkäynnistyksen jälkeen."""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TicketTopicSelect(bot, []))


async def setup(bot):
    bot.add_view(TicketOpenView(bot))
    bot.add_view(TicketOpenViewWithSelect(bot))
    bot.add_view(TicketCloseView(bot))
    await bot.add_cog(TikettiCog(bot))

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
