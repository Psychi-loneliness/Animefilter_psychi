from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_add_and_reuse_filter_tags(db):
    await db.upsert_filter("action", "Action")
    first = await db.add_anime("Demon Slayer", "https://t.me/+a", "hindi", tags=["action"])
    second = await db.add_anime("Jujutsu Kaisen", "https://t.me/+b", "hindi", tags=["action"])
    assert first != second
    items = await db.anime_by_filter("action")
    assert {i["title"] for i in items} == {"Demon Slayer", "Jujutsu Kaisen"}
    card = await db.get_anime(first)
    assert card["filters"] == ["action"]


@pytest.mark.asyncio
async def test_upsert_same_title_language_updates_instead_of_duplicating(db):
    a = await db.add_anime("One Piece", "https://t.me/+old", "hindi")
    b = await db.add_anime("One Piece", "https://t.me/+new", "hindi")
    assert a == b
    assert await db.count_anime() == 1
    assert (await db.get_anime(a))["link"] == "https://t.me/+new"


@pytest.mark.asyncio
async def test_same_title_different_language_is_separate(db):
    await db.add_anime("Naruto", "https://t.me/+hi", "hindi")
    await db.add_anime("Naruto", "https://t.me/+en", "english")
    assert await db.count_anime() == 2


@pytest.mark.asyncio
async def test_latest_and_popular_ordering(db):
    await db.add_anime("Old popular", "l1", popularity=95)
    await db.add_anime("New quiet", "l2", popularity=5)
    latest = await db.anime_by_filter("latest")
    assert latest[0]["title"] == "New quiet"
    popular = await db.anime_by_filter("popular")
    assert popular[0]["title"] == "Old popular"


@pytest.mark.asyncio
async def test_search_language_filter(db):
    await db.add_anime("Demon Slayer", "l1", "hindi")
    await db.add_anime("Demon Slayer", "l2", "english")
    await db.add_anime("Demon School", "l3", "any")

    hindi = await db.search("demon", "hindi")
    assert {r["language"] for r in hindi} == {"hindi", "any"}
    english = await db.search("demon", "english")
    assert {r["language"] for r in english} == {"english", "any"}
    exact_first = await db.search("Demon Slayer", "hindi")
    assert exact_first[0]["title"] == "Demon Slayer"


@pytest.mark.asyncio
async def test_search_is_case_insensitive_and_empty_query(db):
    await db.add_anime("Blue Lock", "l1", "hindi")
    assert len(await db.search("BLUE", "hindi")) == 1
    assert await db.search("", "hindi") == []


@pytest.mark.asyncio
async def test_group_links_and_fallback(db):
    await db.set_group("menu", "https://t.me/+default", "Main")
    await db.set_group("action", "https://t.me/+action", "Action GC")
    assert (await db.get_group("action"))["link"] == "https://t.me/+action"
    assert (await db.get_group("missing")) is None
    # re-saving replaces the link but keeps the title
    await db.set_group("action", "https://t.me/+action2")
    row = await db.get_group("action")
    assert row["link"] == "https://t.me/+action2"
    assert row["title"] == "Action GC"


@pytest.mark.asyncio
async def test_joined_users_and_stats(db):
    await db.mark_joined(10, "action")
    await db.mark_joined(10, "menu")
    await db.mark_joined(11, "menu")
    assert sorted(await db.joined_users()) == [10, 11]
    assert await db.joined_users(["action"]) == [10]
    stats = await db.stats()
    assert stats["users"] == 2


@pytest.mark.asyncio
async def test_settings_roundtrip(db):
    assert await db.get_setting("auto_menu", "1") == "1"
    await db.set_setting("auto_menu", "0")
    assert await db.get_setting("auto_menu", "1") == "0"


@pytest.mark.asyncio
async def test_delete_anime_cascades_filter_rows(db):
    await db.upsert_filter("action", "Action")
    anime_id = await db.add_anime("X", "l", tags=["action"])
    await db.delete_anime(anime_id)
    assert await db.anime_by_filter("action") == []
