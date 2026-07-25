from biome_fm.plastic._acl import parse_acl
from biome_fm.plastic._models import AclEntry


def test_parse_acl_empty():
    assert parse_acl("") == []


def test_parse_acl_line():
    result = parse_acl("alice|user|ReadWrite\n")
    assert result[0] == AclEntry("alice", "user", "ReadWrite")
