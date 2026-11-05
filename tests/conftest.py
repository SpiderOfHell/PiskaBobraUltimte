from __future__ import annotations

import pytest


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeTimer:
    def __init__(self, interval, function, args=()) -> None:
        self.interval = interval
        self.function = function
        self.args = args
        self.started = False
        self.cancelled = False
        self.daemon = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if self.started and not self.cancelled:
            self.function(*self.args)


@pytest.fixture
def fake_timing():
    clock = FakeClock()
    timers: list[FakeTimer] = []

    def timer_factory(interval, function, args=()):
        timer = FakeTimer(interval, function, args)
        timers.append(timer)
        return timer

    return clock, timer_factory, timers
