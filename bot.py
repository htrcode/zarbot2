"""invoice_bot entry point.

    Edit the "EDIT THESE" block in config.py (token + channel ids), then: python bot.py
    (Environment variables still work and override config.py if you set them.)
"""

from __future__ import annotations

import logging
import sys

import discord
from discord import app_commands
from discord.ext import commands

import config
import ui

log = logging.getLogger("invoice_bot")

EXTENSIONS = (
    "cogs.invoices",
    "cogs.finance",
)


class InvoiceTree(app_commands.CommandTree):
    """Command tree that always answers the user when a command fails."""

    async def on_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CommandNotFound):
            # Discord still lists a command this bot no longer has (stale registration).
            title = "Outdated command"
            body = (
                "That command no longer exists. Type `/` and pick one of the "
                "current commands (`/invoice`, `/sale`, `/expense`, `/statement`). "
                "If you still see old ones, restart Discord (Ctrl+R) to refresh the list."
            )
        elif isinstance(error, app_commands.MissingPermissions):
            title, body = "No permission", "You do not have permission to use that command."
        else:
            log.error("Command %r failed", getattr(interaction.command, "name", None), exc_info=error)
            title = "Something went wrong"
            body = f"`{type(error).__name__}` — the error was logged. Please try again."

        view = ui.notice(title, body, error=True)
        try:
            if interaction.response.is_done():
                await interaction.followup.send(view=view, ephemeral=True)
            else:
                await interaction.response.send_message(view=view, ephemeral=True)
        except discord.HTTPException:
            pass


class InvoiceBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            help_command=None,
            tree_cls=InvoiceTree,
        )
        self._cleaned_guilds = False

    async def setup_hook(self) -> None:
        # The "Mark as paid" button lives on invoices posted in the past,
        # so it is registered globally rather than per-message.
        self.add_dynamic_items(ui.MarkPaidButton)
        ui.set_tagline(config.BRAND_TAGLINE)

        for extension in EXTENSIONS:
            await self.load_extension(extension)

        await self._sync_commands()

    async def _sync_commands(self) -> None:
        """Publish this bot's commands and remove every stale one.

        A bot token keeps whatever commands any earlier version registered
        (global *and* per-server). Those no longer exist in the code, so
        Discord shows them but they fail with "Application command not found".
        Syncing an empty set over them removes them.
        """
        names = sorted(c.qualified_name for c in self.tree.walk_commands())
        guild_id = config.GUILD_ID

        if guild_id:
            guild = discord.Object(id=guild_id)
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
            except discord.HTTPException as exc:
                print(
                    f"WARNING: could not sync to GUILD_ID {guild_id} ({exc}); "
                    "falling back to global commands. Is the bot in that server?"
                )
            else:
                # Commands now live in the server; wipe the global copies/stale ones.
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                print(f"Synced {len(synced)} commands to server {guild_id}: {', '.join(names)}")
                return

        synced = await self.tree.sync()
        print(f"Synced {len(synced)} global commands: {', '.join(names)}")

    async def _clear_stale_guild_commands(self) -> None:
        """Remove old per-server commands left in every other server."""
        keep = config.GUILD_ID
        for guild in self.guilds:
            if keep and guild.id == keep:
                continue
            try:
                # Nothing is registered for this guild in the tree, so this
                # sends an empty list and deletes whatever was left there.
                await self.tree.sync(guild=guild)
            except discord.HTTPException as exc:
                print(f"Could not clean commands in {guild.name} ({guild.id}): {exc}")

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} ({self.user.id})")
        if not self._cleaned_guilds:
            self._cleaned_guilds = True
            await self._clear_stale_guild_commands()
        if config.INVOICE_CHANNEL_ID is None:
            print("WARNING: INVOICE_CHANNEL_ID is not set — new invoices have nowhere to go.")
        else:
            print(f"Invoices go to channel {config.INVOICE_CHANNEL_ID}")
        if config.STATEMENTS_CHANNEL_ID is None:
            print(
                "WARNING: STATEMENTS_CHANNEL_ID is not set — sales/expense statements "
                "have nowhere to go."
            )
        else:
            print(f"Statements go to channel {config.STATEMENTS_CHANNEL_ID}")


def main() -> None:
    if not config.TOKEN:
        sys.exit(
            "No bot token set. Open invoice_bot/config.py and paste your token into "
            "BOT_TOKEN (or set DISCORD_BOT_TOKEN on the panel)."
        )
    bot = InvoiceBot()
    bot.run(config.TOKEN, root_logger=True)


if __name__ == "__main__":
    main()
