"""Tests for the stop flag, the limit check and the e-stop input thread."""

import time

import pytest

from arctos.safety import EstopInput, LimitError, Safety, Stopped


def test_stop_calls_actions_and_guard_raises() -> None:
    s = Safety()
    calls: list[str] = []
    s.on_stop.append(lambda: calls.append("arm"))
    s.on_stop.append(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    s.guard()
    s.request_stop("test")
    assert s.stopped and s.reason == "test"
    assert calls == ["arm"]
    with pytest.raises(Stopped):
        s.guard()
    s.clear()
    assert not s.stopped
    s.guard()


def test_check_range() -> None:
    Safety.check_range("x", 10, -20, 20)
    with pytest.raises(LimitError):
        Safety.check_range("x", 21, -20, 20)


def test_estop_input_triggers_stop() -> None:
    s = Safety()
    pressed = {"value": False}
    estop = EstopInput(s, lambda: pressed["value"], period=0.01)
    estop.start()
    time.sleep(0.05)
    assert not s.stopped
    pressed["value"] = True
    deadline = time.monotonic() + 1.0
    while not s.stopped and time.monotonic() < deadline:
        time.sleep(0.01)
    estop.stop()
    estop.join(timeout=1.0)
    assert s.stopped and s.reason == "emergency stop"
