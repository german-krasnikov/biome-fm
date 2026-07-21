"""F438: Unicode filename normalization — NFC for cross-platform consistency.
F400: Natural/version sort for filenames.
"""
import unicodedata
from biome_fm.utils.encoding import normalize_filename
from biome_fm.models.directory_model import _nat_key

NFC_CAFE = unicodedata.normalize("NFC", "café")  # U+00E9
NFD_CAFE = unicodedata.normalize("NFD", "café")  # e + combining accent


def test_nfc_and_nfd_normalize_equal():
    assert normalize_filename(NFC_CAFE) == normalize_filename(NFD_CAFE)


def test_empty_string():
    assert normalize_filename("") == ""


def test_ascii_noop():
    assert normalize_filename("hello.txt") == "hello.txt"


def test_already_nfc():
    assert normalize_filename(NFC_CAFE) == NFC_CAFE


# F400 — natural sort key tests
def test_nat_key_img10_gt_img2():
    assert _nat_key("IMG_10") > _nat_key("IMG_2")


def test_nat_key_img_sequence():
    names = ["IMG_10", "IMG_2", "IMG_1"]
    assert sorted(names, key=_nat_key) == ["IMG_1", "IMG_2", "IMG_10"]


def test_nat_key_multi_numeric():
    assert _nat_key("file_1_v2") < _nat_key("file_1_v10")


def test_nat_key_pure_string_fallback():
    assert _nat_key("abc") < _nat_key("xyz")


def test_nat_key_empty():
    assert _nat_key("") == [""]


def test_nat_key_case_insensitive():
    assert _nat_key("IMG_1") == _nat_key("img_1")
