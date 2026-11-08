"""SQLite storage for the anime filter bot.

Tables
------
anime        one row per anime title (with the "filter bot" movie link)
filters      free-form filter tags (genre / language / quality / "latest" ...)
anime_filter many-to-many between anime and filters
groups       join links keyed by filter slug (one link can serve many filters)
joined       which user joined through which link (so we can DM them updates)
"""
from __future__ import annotations

import json
import time
from typing import Any, Iterable, Sequence

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS anime (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    language    TEXT NOT NULL DEFAULT 'any',      -- hindi | english | any
    link        TEXT NOT NULL DEFAULT '',         -- link given by the filter bot
    poster      TEXT NOT NULL DEFAULT '',         -- Telegram file_id of the anime logo
    extras      TEXT NOT NULL DEFAULT '[]',       -- JSON [[label, url], …] extra card buttons
    release_tag TEXT NOT NULL DEFAULT 'latest',   -- latest | popular | normal
    popularity  INTEGER NOT NULL DEFAULT 0,
    added_at    INTEGER NOT NULL,
    UNIQUE (title, language)
);

CREATE TABLE IF NOT EXISTS filters (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS anime_filter (
    anime_id  INTEGER NOT NULL REFERENCES anime(id) ON DELETE CASCADE,
    filter_id INTEGER NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
    PRIMARY KEY (anime_id, filter_id)
);

CREATE TABLE IF NOT EXISTS groups (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    slug      TEXT NOT NULL UNIQUE,               -- filter slug OR "menu"
    title     TEXT NOT NULL DEFAULT '',
    link      TEXT NOT NULL,
    added_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS joined (
    user_id  INTEGER NOT NULL,
    slug     TEXT NOT NULL,
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, slug)
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_anime_tag ON anime(release_tag, popularity);
"""


def now() -> int:
    return int(time.time())


class Database:
    """Small async wrapper around one SQLite connection.

    A single connection keeps things simple for a community bot; SQLite serialises
    the writes and every operation here is short.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    # ------------------------------------------------------------------ setup
    async def connect(self) -> "Database":
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.executescript(SCHEMA)
        await self._migrate()
        await self._conn.commit()
        return self

    async def _migrate(self) -> None:
        """Add columns that appeared after the first release."""
        cur = await self.conn.execute("PRAGMA table_info(anime)")
        columns = {row["name"] for row in await cur.fetchall()}
        await cur.close()
        for name, ddl in (
            ("poster", "ALTER TABLE anime ADD COLUMN poster TEXT NOT NULL DEFAULT ''"),
            ("extras", "ALTER TABLE anime ADD COLUMN extras TEXT NOT NULL DEFAULT '[]'"),
        ):
            if name not in columns:
                await self.conn.execute(ddl)

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database.connect() was not awaited")
        return self._conn

    async def _fetchall(self, sql: str, params: Sequence[Any] = ()) -> list[aiosqlite.Row]:
        cur = await self.conn.execute(sql, params)
        rows = await cur.fetchall()
        await cur.close()
        return list(rows)

    async def _fetchone(self, sql: str, params: Sequence[Any] = ()) -> aiosqlite.Row | None:
        cur = await self.conn.execute(sql, params)
        row = await cur.fetchone()
        await cur.close()
        return row

    async def _exec(self, sql: str, params: Sequence[Any] = ()) -> int:
        cur = await self.conn.execute(sql, params)
        await self.conn.commit()
        rowid = cur.lastrowid or 0
        await cur.close()
        return rowid

    # ------------------------------------------------------------------ anime
    async def upsert_filter(self, slug: str, name: str) -> None:
        await self._exec(
            "INSERT INTO filters (slug, name) VALUES (?, ?) "
            "ON CONFLICT(slug) DO UPDATE SET name=excluded.name",
            (slug, name),
        )

    async def _filter_ids(self, slugs: Iterable[str]) -> list[int]:
        ids: list[int] = []
        for slug in slugs:
            row = await self._fetchone("SELECT id FROM filters WHERE slug = ?", (slug,))
            if row is not None:
                ids.append(int(row["id"]))
        return ids

    async def add_anime(
        self,
        title: str,
        link: str = "",
        language: str = "any",
        release_tag: str = "latest",
        popularity: int = 0,
        tags: Sequence[str] = (),
        poster: str = "",
        extras: Sequence[Sequence[str]] = (),
    ) -> int:
        """Insert a title, or refresh it when the same title+language exists.

        Empty ``link`` / ``poster`` keep whatever was stored before, so a poster
        can be added later without wiping the group link (and vice versa).
        """
        existing = await self._fetchone(
            "SELECT id, link, poster, extras FROM anime "
            "WHERE lower(title) = lower(?) AND language = ?",
            (title, language),
        )
        extras_json = json.dumps([list(e) for e in extras], ensure_ascii=False)
        if existing is None:
            anime_id = await self._exec(
                "INSERT INTO anime (title, language, link, poster, extras, release_tag, popularity, added_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, language, link, poster, extras_json, release_tag, popularity, now()),
            )
        else:
            anime_id = int(existing["id"])
            await self._exec(
                "UPDATE anime SET title = ?, link = ?, poster = ?, extras = ?, "
                "release_tag = ?, popularity = ? WHERE id = ?",
                (
                    title,
                    link or existing["link"],
                    poster or existing["poster"],
                    extras_json if extras else (existing["extras"] or "[]"),
                    release_tag,
                    popularity,
                    anime_id,
                ),
            )
        for fid in await self._filter_ids(tags):
            await self._exec(
                "INSERT OR IGNORE INTO anime_filter (anime_id, filter_id) VALUES (?, ?)",
                (anime_id, fid),
            )
        return anime_id

    async def set_poster(self, anime_id: int, poster: str) -> None:
        await self._exec("UPDATE anime SET poster = ? WHERE id = ?", (poster, anime_id))

    async def delete_anime(self, anime_id: int) -> None:
        await self._exec("DELETE FROM anime WHERE id = ?", (anime_id,))

    async def get_anime(self, anime_id: int) -> dict[str, Any] | None:
        row = await self._fetchone("SELECT * FROM anime WHERE id = ?", (anime_id,))
        if row is None:
            return None
        data = dict(row)
        try:
            data["extras"] = [list(e) for e in json.loads(data.get("extras") or "[]")]
        except (ValueError, TypeError):
            data["extras"] = []
        data["filters"] = [r["slug"] for r in await self._fetchall(
            "SELECT f.slug FROM filters f JOIN anime_filter af ON af.filter_id = f.id "
            "WHERE af.anime_id = ? ORDER BY f.name", (anime_id,))]
        return data

    async def anime_by_filter(self, slug: str, limit: int = 20) -> list[dict[str, Any]]:
        """Newest / most popular titles tagged with ``slug`` (``latest``, ``popular`` ...)."""
        if slug == "latest":
            rows = await self._fetchall(
                "SELECT * FROM anime ORDER BY added_at DESC, id DESC LIMIT ?", (limit,))
        elif slug == "popular":
            rows = await self._fetchall(
                "SELECT * FROM anime ORDER BY popularity DESC, added_at DESC LIMIT ?", (limit,))
        else:
            rows = await self._fetchall(
                "SELECT a.* FROM anime a "
                "JOIN anime_filter af ON af.anime_id = a.id "
                "JOIN filters f ON f.id = af.filter_id "
                "WHERE f.slug = ? ORDER BY a.added_at DESC, a.id DESC LIMIT ?",
                (slug, limit),
            )
        return [dict(r) for r in rows]

    async def count_by_filter(self, slug: str) -> int:
        if slug == "latest":
            row = await self._fetchone("SELECT COUNT(*) AS c FROM anime")
        elif slug == "popular":
            row = await self._fetchone("SELECT COUNT(*) AS c FROM anime")
        else:
            row = await self._fetchone(
                "SELECT COUNT(*) AS c FROM anime a "
                "JOIN anime_filter af ON af.anime_id = a.id "
                "JOIN filters f ON f.id = af.filter_id WHERE f.slug = ?",
                (slug,),
            )
        return int(row["c"]) if row else 0

    async def search(self, query: str, language: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.strip()
        if not q:
            return []
        like = f"%{q}%"
        params: list[Any] = [like]
        lang_sql = ""
        if language in ("hindi", "english"):
            lang_sql = " AND language IN (?, 'any')"
            params.append(language)
        params.extend([q, limit])  # ORDER BY exact-match placeholder, then LIMIT
        rows = await self._fetchall(
            "SELECT * FROM anime WHERE title LIKE ? "
            + lang_sql
            + " ORDER BY CASE WHEN lower(title) = lower(?) THEN 0 ELSE 1 END, popularity DESC, added_at DESC LIMIT ?",
            params,
        )
        return [dict(r) for r in rows]

    async def count_anime(self) -> int:
        row = await self._fetchone("SELECT COUNT(*) AS c FROM anime")
        return int(row["c"]) if row else 0

    # ----------------------------------------------------------------- groups
    async def set_group(self, slug: str, link: str, title: str = "") -> None:
        await self._exec(
            "INSERT INTO groups (slug, title, link, added_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(slug) DO UPDATE SET link=excluded.link, "
            "title=CASE WHEN excluded.title = '' THEN groups.title ELSE excluded.title END",
            (slug, title, link, now()),
        )

    async def get_group(self, slug: str) -> dict[str, Any] | None:
        if slug == "menu":
            row = await self._fetchone(
                "SELECT g.* FROM groups g WHERE g.slug = 'menu'")
        else:
            row = await self._fetchone(
                "SELECT g.* FROM groups g WHERE g.slug = ?", (slug,))
        return dict(row) if row else None

    async def group_links(self, slugs: Sequence[str]) -> list[dict[str, Any]]:
        """Return one group link per slug, falling back to the ``menu`` group link."""
        out: list[dict[str, Any]] = []
        for slug in slugs:
            for candidate in (slug, "menu"):
                row = await self._fetchone("SELECT * FROM groups WHERE slug = ?", (candidate,))
                if row is not None:
                    out.append(dict(row) | {"for": slug})
                    break
        return out

    async def list_groups(self) -> list[dict[str, Any]]:
        return [dict(r) for r in await self._fetchall("SELECT * FROM groups ORDER BY slug")]

    async def delete_group(self, slug: str) -> None:
        await self._exec("DELETE FROM groups WHERE slug = ?", (slug,))

    # ----------------------------------------------------------------- joined
    async def mark_joined(self, user_id: int, slug: str) -> None:
        await self._exec(
            "INSERT OR REPLACE INTO joined (user_id, slug, joined_at) VALUES (?, ?, ?)",
            (user_id, slug, now()),
        )

    async def joined_users(self, slugs: Sequence[str] | None = None) -> list[int]:
        if slugs:
            marks = ",".join("?" for _ in slugs)
            rows = await self._fetchall(
                f"SELECT DISTINCT user_id FROM joined WHERE slug IN ({marks})", tuple(slugs))
        else:
            rows = await self._fetchall("SELECT DISTINCT user_id FROM joined")
        return [int(r["user_id"]) for r in rows]

    async def stats(self) -> dict[str, int]:
        anime = await self.count_anime()
        groups = await self._fetchone("SELECT COUNT(*) AS c FROM groups")
        users = await self._fetchone("SELECT COUNT(DISTINCT user_id) AS c FROM joined")
        return {
            "anime": anime,
            "groups": int(groups["c"]) if groups else 0,
            "users": int(users["c"]) if users else 0,
        }

    # --------------------------------------------------------------- settings
    async def set_setting(self, key: str, value: str) -> None:
        await self._exec(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    async def get_setting(self, key: str, default: str = "") -> str:
        row = await self._fetchone("SELECT value FROM settings WHERE key = ?", (key,))
        return str(row["value"]) if row else default
