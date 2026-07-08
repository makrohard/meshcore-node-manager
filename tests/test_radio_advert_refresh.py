import unittest
from unittest.mock import Mock

from events import EventBus
from radio import NodeRadio, _MC_OK


class _Handle:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class _Task:
    def __init__(self):
        self.done_cbs = []

    def add_done_callback(self, cb):
        self.done_cbs.append(cb)


class _FakeLoop:
    """Minimal stand-in for the radio asyncio loop (no real thread)."""

    def __init__(self, running=True):
        self.running = running
        self.scheduled = []   # list of (delay, callback, handle)
        self.tasks = []       # coroutines/objects handed to create_task

    def is_running(self):
        return self.running

    def call_later(self, delay, cb):
        h = _Handle()
        self.scheduled.append((delay, cb, h))
        return h

    def create_task(self, coro):
        self.tasks.append(coro)
        return _Task()


class _Event:
    def __init__(self, type_):
        self.type = type_
        self.payload = None
        self.attributes = {}


def _armed_radio():
    """A NodeRadio wired to a fake loop, online, with a stubbed _load_contacts."""
    radio = NodeRadio(EventBus())
    radio._loop = _FakeLoop()
    radio._online = True
    radio._mc = object()
    radio._load_contacts = Mock(name="_load_contacts")
    return radio


class AdvertContactRefreshTests(unittest.TestCase):
    def test_bursts_coalesce_into_single_refresh(self):
        radio = _armed_radio()

        # Three adverts in quick succession (a re-flood burst).
        radio._schedule_contacts_refresh()
        radio._schedule_contacts_refresh()
        radio._schedule_contacts_refresh()

        loop = radio._loop
        # Each call reschedules: 3 timers created, first two cancelled, last live.
        self.assertEqual(len(loop.scheduled), 3)
        self.assertTrue(loop.scheduled[0][2].cancelled)
        self.assertTrue(loop.scheduled[1][2].cancelled)
        self.assertFalse(loop.scheduled[2][2].cancelled)
        self.assertIs(radio._contact_refresh_handle, loop.scheduled[2][2])

        # Fire only the surviving (last) timer.
        loop.scheduled[2][1]()

        # Exactly one fetch, scheduled on the loop (not via _submit).
        self.assertEqual(radio._load_contacts.call_count, 1)
        self.assertEqual(len(loop.tasks), 1)
        self.assertIsNone(radio._contact_refresh_handle)

    def test_no_blocking_submit_or_public_refresh_used(self):
        radio = _armed_radio()
        radio._submit = Mock(name="_submit")
        radio.refresh_contacts = Mock(name="refresh_contacts")

        radio._schedule_contacts_refresh()
        radio._loop.scheduled[-1][1]()   # fire the timer

        # The advert path must never take the cross-loop blocking route.
        radio._submit.assert_not_called()
        radio.refresh_contacts.assert_not_called()

    def test_disconnect_cancels_pending_refresh(self):
        radio = _armed_radio()
        radio._schedule_contacts_refresh()
        handle = radio._contact_refresh_handle
        self.assertIsNotNone(handle)

        radio._cancel_contacts_refresh()

        self.assertTrue(handle.cancelled)
        self.assertIsNone(radio._contact_refresh_handle)

    def test_fire_after_teardown_does_not_touch_stale_mc(self):
        radio = _armed_radio()
        radio._schedule_contacts_refresh()
        fire = radio._loop.scheduled[-1][1]

        # Simulate disconnect teardown before the timer fires.
        radio._online = False
        radio._mc = None

        fire()

        radio._load_contacts.assert_not_called()
        self.assertEqual(len(radio._loop.tasks), 0)

    def test_schedule_noop_when_loop_absent(self):
        radio = NodeRadio(EventBus())
        radio._loop = None
        # Must not raise even with no loop.
        radio._schedule_contacts_refresh()
        self.assertIsNone(radio._contact_refresh_handle)

    def test_refresh_done_callback_reports_errors(self):
        radio = _armed_radio()
        logged = []
        radio._emit_log = lambda msg, level="info": logged.append((msg, level))

        failing = Mock()
        failing.exception.return_value = RuntimeError("boom")
        radio._contacts_refresh_done(failing)

        self.assertTrue(any("boom" in m for m, _ in logged))

    @unittest.skipUnless(_MC_OK, "meshcore lib not installed")
    def test_on_mc_event_routes_advert_to_scheduler(self):
        radio = NodeRadio(EventBus())
        radio._advert_events = ("ADV_SENTINEL",)
        radio._schedule_contacts_refresh = Mock(name="_schedule_contacts_refresh")

        radio._on_mc_event(_Event("ADV_SENTINEL"))

        radio._schedule_contacts_refresh.assert_called_once()


if __name__ == "__main__":
    unittest.main()
