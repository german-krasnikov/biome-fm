"""F237 — Quick-connect bar integration tests."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from biome_fm.views.quick_connect_bar import QuickConnectBar


@pytest.fixture
def bar(qtbot):
    b = QuickConnectBar()
    qtbot.addWidget(b)
    b.show()
    return b


class TestQuickConnectBar:
    def test_set_profiles_populates_combo(self, bar):
        profiles = [
            ("My SFTP", "sftp://user@host/"),
            ("S3 Bucket", "s3://my-bucket/"),
        ]
        bar.set_profiles(profiles)
        assert bar._combo.count() == 2
        assert bar._combo.itemText(0) == "My SFTP"
        assert bar._combo.itemText(1) == "S3 Bucket"

    def test_set_profiles_clears_previous(self, bar):
        bar.set_profiles([("A", "sftp://a/"), ("B", "sftp://b/")])
        bar.set_profiles([("C", "sftp://c/")])
        assert bar._combo.count() == 1
        assert bar._combo.itemText(0) == "C"

    def test_connect_emits_uri_of_selected(self, qtbot, bar):
        profiles = [
            ("My SFTP", "sftp://user@host/"),
            ("S3 Bucket", "s3://my-bucket/"),
        ]
        bar.set_profiles(profiles)
        bar._combo.setCurrentIndex(0)

        received: list[str] = []
        bar.connect_requested.connect(received.append)

        with qtbot.waitSignal(bar.connect_requested, timeout=1000):
            bar._btn.click()

        assert received == ["sftp://user@host/"]

    def test_connect_emits_second_profile_uri(self, qtbot, bar):
        profiles = [
            ("My SFTP", "sftp://user@host/"),
            ("S3 Bucket", "s3://my-bucket/"),
        ]
        bar.set_profiles(profiles)
        bar._combo.setCurrentIndex(1)

        received: list[str] = []
        bar.connect_requested.connect(received.append)

        with qtbot.waitSignal(bar.connect_requested, timeout=1000):
            bar._btn.click()

        assert received == ["s3://my-bucket/"]

    def test_no_profiles_button_still_exists(self, bar):
        assert bar._btn is not None
