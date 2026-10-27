"""Configuration for invoice_bot.

No .env file needed
-------------------
Fill in the values in the "EDIT THESE" block below (use the Pterodactyl file
manager to edit this file on the server). If you *do* set environment
variables / Startup variables on the panel, those take priority over the
values written here.

Channel routing
---------------
``INVOICE_CHANNEL_ID``
    Every *newly created invoice* is posted here and nowhere else.

``STATEMENTS_CHANNEL_ID``
    Payment-received notices, the sales statement and the professional
    expenses statement are all posted here.

Do not commit your real token to a public repository.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# ==========================================================================
# EDIT THESE
# ==========================================================================
BOT_TOKEN = ""  # paste your bot token between the quotes
INVOICE_CHANNEL_ID = 0  # channel id for new invoices (digits only)
STATEMENTS_CHANNEL_ID = 0  # channel id for payments + statements (digits only)
GUILD_ID = 0  # optional: your server id for instant slash-command updates, or 0
BRAND_TAGLINE = ""  # optional small line shown under the title of every card, e.g. "Hector Hosting"
UTC_OFFSET_HOURS = 5.5  # used for dates on statements (5.5 = India / IST)
# ==========================================================================


def _int(name: str, fallback: int) -> Optional[int]:
    """Environment variable first, then the value written above. 0/empty = unset."""
    raw = os.environ.get(name, "").strip()
    if raw:
        try:
            return int(raw) or None
        except ValueError:
            raise RuntimeError(f"{name} must be a channel/server id (digits only), got {raw!r}")
    return int(fallback) or None


#: Bot token.
TOKEN: str = (os.environ.get("DISCORD_BOT_TOKEN") or BOT_TOKEN).strip()

#: Where brand-new invoices are sent.
INVOICE_CHANNEL_ID: Optional[int] = _int("INVOICE_CHANNEL_ID", INVOICE_CHANNEL_ID)

#: Where payment received + sales/expenses statements are sent.
STATEMENTS_CHANNEL_ID: Optional[int] = _int("STATEMENTS_CHANNEL_ID", STATEMENTS_CHANNEL_ID)

#: Optional guild id for instant slash-command registration (falls back to global sync).
GUILD_ID: Optional[int] = _int("GUILD_ID", GUILD_ID)

#: Small line shown under every card title ("" = none).
BRAND_TAGLINE: str = (os.environ.get("BRAND_TAGLINE") or BRAND_TAGLINE).strip()

#: Hours offset from UTC for statement dates.
UTC_OFFSET_HOURS: float = float(os.environ.get("UTC_OFFSET_HOURS") or UTC_OFFSET_HOURS)

#: Where the JSON store lives.
DATA_FILE: Path = Path(
    os.environ.get("INVOICE_BOT_DATA") or Path(__file__).with_name("data.json")
)
