"""Start-up helpers: bring a wiped library back automatically.

Free hosts (Render free plan, many others) throw away the disk when the service
restarts or redeploys. The admin's last ``/backup`` file lives safely in Telegram,
so if ``AUTO_RESTORE_FILE_ID`` is set we can pull it back on boot without the
admin doing anything.
"""
from __future__ import annotations

import logging

from .db import Database

log = logging.getLogger(__name__)


async def auto_restore_if_empty(bot, db: Database, file_id: str = "") -> bool:
    """Restore from a Telegram file when the database has no titles.

    Returns ``True`` when a restore happened.
    """
    file_id = (file_id or "").strip()
    if not file_id:
        return False
    if await db.count_anime() > 0:
        return False
    try:
        file = await bot.get_file(file_id)
        raw = bytes(await file.download_as_bytearray())
        await db.restore(raw)
    except Exception:  # noqa: BLE001 - a bad id must never stop the bot
        log.warning("AUTO_RESTORE_FILE_ID could not be used", exc_info=True)
        return False
    log.info("auto-restored %s titles from Telegram backup", await db.count_anime())
    return True
