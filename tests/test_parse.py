from animebot.handlers.admin import _parse_entry


def test_full_pipe_format():
    e = _parse_entry("Demon Slayer | https://t.me/+abc | hindi | action,shonen | 97")
    assert e == {
        "title": "Demon Slayer",
        "link": "https://t.me/+abc",
        "language": "hindi",
        "tags": ["action", "shonen"],
        "popularity": 97,
    }


def test_order_does_not_matter_and_link_can_be_skipped():
    e = _parse_entry("Solo Leveling | 90 | english | isekai | https://t.me/+s")
    assert e["language"] == "english"
    assert e["tags"] == ["isekai"]
    assert e["popularity"] == 90
    assert e["link"] == "https://t.me/+s"


def test_explicit_keys_and_language_aliases():
    e = _parse_entry("Bleach | lang=en | tags=action, fantasy | pop=88")
    assert (e["language"], e["tags"], e["popularity"]) == ("english", ["action", "fantasy"], 88)
    assert _parse_entry("X | hin")["language"] == "hindi"
    assert _parse_entry("X | multi")["language"] == "any"


def test_title_only():
    assert _parse_entry("One Piece") == {
        "title": "One Piece", "link": "", "language": "any", "tags": [], "popularity": 0
    }


def test_hyphenated_tags_multiple_separators():
    e = _parse_entry("X | action;slice of life / romance")
    assert e["tags"] == ["action", "slice-of-life", "romance"]
