from __future__ import annotations

import pytest_asyncio

from animebot.db import Database


@pytest_asyncio.fixture
async def db(tmp_path):
    database = await Database(str(tmp_path / "test.db")).connect()
    try:
        yield database
    finally:
        await database.close()
