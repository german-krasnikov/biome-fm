from biome_fm.presenters.leader_handler import LeaderHandler


def test_register_sequence():
    h = LeaderHandler()
    h.register("sf", lambda: None)
    assert "sf" in h._bindings


def test_feed_completes_sequence():
    triggered = []
    h = LeaderHandler()
    h.register("sf", lambda: triggered.append(1))
    h.feed("s")
    assert h.feed("f") == "triggered"
    assert triggered == [1]


def test_feed_partial_no_trigger():
    h = LeaderHandler()
    h.register("sf", lambda: None)
    assert h.feed("s") == "pending"
    assert h._buffer == "s"


def test_timeout_resets():
    h = LeaderHandler()
    h.register("sf", lambda: None)
    h.feed("s")
    h.reset()
    assert h._buffer == ""


def test_unknown_key_resets():
    h = LeaderHandler()
    h.register("sf", lambda: None)
    h.feed("s")
    assert h.feed("x") == "reset"
    assert h._buffer == ""


def test_available_after_prefix():
    h = LeaderHandler()
    h.register("sf", lambda: None)
    h.register("sg", lambda: None)
    h.feed("s")
    avail = h.available()
    assert ("f", "sf") in avail
    assert ("g", "sg") in avail
