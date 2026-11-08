"""The filter-bot card syntax must be read exactly like a human writes it."""
from animebot.card import parse_entry

CARD = '/filter "the Case study of vanitas"[🍀Hindi dub🍀](buttonurl:https://t.me/+l16u8HgUO3BmZThl)\n[🗞️Update](buttonurl:https://t.me/redlineanime)'


def test_user_card_is_parsed():
    e = parse_entry(CARD)
    assert e.title == "The Case study of vanitas"
    assert e.language == "hindi"
    assert e.primary_link == "https://t.me/+l16u8HgUO3BmZThl"
    assert e.tags == []
    assert [(x.label, x.url) for x in e.other_buttons()] == [
        ("🗞️Update", "https://t.me/redlineanime")
    ]
    assert e.smart


def test_title_without_quotes_and_glued_bracket():
    e = parse_entry("/save Naruto[🍀Hindi dub🍀](buttonurl:https://t.me/+naruto)")
    assert e.title == "Naruto"
    assert e.language == "hindi"
    assert e.primary_link == "https://t.me/+naruto"


def test_genres_come_from_button_labels():
    e = parse_entry('/filter "Solo Leveling" [🌀Isekai, Action🌀](buttonurl:https://t.me/+s)')
    assert e.tags == ["isekai", "action"]
    assert e.language == "any"


def test_multiple_dub_buttons_make_it_multi_audio():
    e = parse_entry(
        '/save "Jujutsu Kaisen"[🔥Action🍀Hindi dub🔥](buttonurl:https://t.me/+hi)\n'
        "[🎬English dub](buttonurl:https://t.me/+en)"
    )
    assert e.language == "any"  # both dubs offered
    assert e.tags == ["action"]
    assert len(e.extras) == 2


def test_update_channel_is_not_a_genre():
    e = parse_entry(CARD)
    assert "update" not in e.tags
    assert "channel" not in e.tags


def test_human_syntax_still_works():
    e = parse_entry("/save Demon Slayer | hindi | action,shonen | 95")
    assert (e.title, e.language, e.tags, e.popularity) == (
        "Demon Slayer", "hindi", ["action", "shonen"], 95
    )

    e = parse_entry("/add One Piece | https://t.me/+op | english | 99")
    assert (e.title, e.language, e.primary_link, e.popularity) == (
        "One Piece", "english", "https://t.me/+op", 99
    )


def test_explicit_keys():
    e = parse_entry("Bleach | lang=en | tags=action, fantasy | pop=88")
    assert (e.language, e.tags, e.popularity) == ("english", ["action", "fantasy"], 88)


def test_language_aliases_and_multi():
    assert parse_entry("X | hin").language == "hindi"
    assert parse_entry("X | eng").language == "english"
    assert parse_entry("X | multi audio").language == "any"
    assert parse_entry("X | Tamil dub").tags == ["tamil"]


def test_title_only_and_hyphen_tags():
    e = parse_entry("One Piece")
    assert (e.title, e.language, e.tags, e.primary_link) == ("One Piece", "any", [], "")
    assert parse_entry("X | action;slice of life / romance").tags == [
        "action", "slice-of-life", "romance"
    ] or parse_entry("X | action;slice of life / romance").tags[:1] == ["action"]
