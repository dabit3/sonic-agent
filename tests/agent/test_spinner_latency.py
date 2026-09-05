import io
import threading

import pytest

from agent.display import KawaiiSpinner


@pytest.mark.parametrize("tty", [False, True])
def test_spinner_stop_wakes_animation_without_waiting_for_a_frame(monkeypatch, tty):
    import agent.display as display

    started = threading.Event()
    release_sleep = threading.Event()
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        release_sleep.wait(2)

    monkeypatch.setattr(display.time, "sleep", sleep)
    monkeypatch.setattr(display, "_get_skin", lambda: None)
    monkeypatch.setattr(KawaiiSpinner, "_is_tty", property(lambda self: tty))
    monkeypatch.setattr(KawaiiSpinner, "_is_patch_stdout_proxy", lambda self: False)
    spinner = KawaiiSpinner("working", print_fn=lambda _: started.set())
    try:
        for _ in range(2):
            started.clear()
            spinner.start()
            assert started.wait(2)
            spinner.stop()
            assert not spinner.thread.is_alive()
            assert not sleeps
    finally:
        release_sleep.set()
        spinner.stop()


def test_spinner_preserves_non_terminal_status_output():
    output = io.StringIO()
    spinner = KawaiiSpinner("working")
    spinner._out = output
    with spinner:
        pass
    spinner.stop("finished")
    assert "[tool] working" in output.getvalue()
    assert "[done] finished" in output.getvalue()
