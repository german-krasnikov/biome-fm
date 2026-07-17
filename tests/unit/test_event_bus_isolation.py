"""I11: EventBus error isolation — bad handler must not block subsequent handlers."""
from dataclasses import dataclass

from biome_fm.event_bus import EventBus


@dataclass
class Ev:
    val: int


def test_bad_handler_does_not_block_next():
    bus = EventBus()
    results = []
    bus.subscribe(Ev, lambda e: 1 / 0)  # raises ZeroDivisionError
    bus.subscribe(Ev, lambda e: results.append(e.val))
    bus.publish(Ev(42))
    assert results == [42]


def test_good_path_unchanged():
    bus = EventBus()
    results = []
    bus.subscribe(Ev, lambda e: results.append(e.val))
    bus.publish(Ev(7))
    assert results == [7]
