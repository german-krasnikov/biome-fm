from biome_fm.plastic._attributes import parse_attributes
from biome_fm.plastic._models import Attribute


def test_parse_attributes_empty():
    assert parse_attributes("", "cs:1") == []


def test_parse_attributes_line():
    result = parse_attributes("status=approved\npriority=high\n", "cs:1")
    assert len(result) == 2
    assert result[0] == Attribute("cs:1", "status", "approved")


def test_parse_attributes_equals_in_value():
    result = parse_attributes("cmd=a=b\n", "cs:1")
    assert result[0].value == "a=b"
