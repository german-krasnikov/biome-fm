from biome_fm.plastic._users import parse_users, parse_groups
from biome_fm.plastic._models import UserInfo, GroupInfo


def test_parse_users_empty():
    assert parse_users("") == []


def test_parse_users_line():
    result = parse_users("alice|alice@example.com\n")
    assert result[0] == UserInfo("alice", "alice@example.com")


def test_parse_users_no_email():
    result = parse_users("bob\n")
    assert result[0] == UserInfo("bob", "")


def test_parse_groups_line():
    result = parse_groups("devs|alice,bob\n")
    assert result[0] == GroupInfo("devs", ("alice", "bob"))


def test_parse_groups_empty_members():
    result = parse_groups("empty|\n")
    assert result[0] == GroupInfo("empty", ())
