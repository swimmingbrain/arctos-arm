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
