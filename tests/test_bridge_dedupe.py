import unittest

import bridge as bridge_module
from bridge import BRIDGE_TEXT_PREFIX, Bridge, FrameType, _DedupeCache
from events import EventBus


class _Settings:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, fallback=None):
        return self._values.get(key, fallback)


class BridgeDedupeTests(unittest.TestCase):
    def test_dedupe_cache_expires_entries_after_ttl(self):
        original_time = bridge_module.time.time
        now = [100.0]
        bridge_module.time.time = lambda: now[0]
        try:
            cache = _DedupeCache(ttl=10.0)
            self.assertFalse(cache.seen("abc"))
            self.assertTrue(cache.seen("abc"))
            now[0] = 111.0
            self.assertFalse(cache.seen("abc"))
        finally:
            bridge_module.time.time = original_time

    def test_bridge_marked_channel_text_is_not_rebroadcast(self):
        bus = EventBus()
        br = Bridge(bus, _Settings())
        br._running = True  # pylint: disable=protected-access
        sent = []
        br._broadcast_async = lambda ftype, payload: sent.append((ftype, payload))  # pylint: disable=protected-access

        br._on_local_channel(sender="local", text=f"{BRIDGE_TEXT_PREFIX}[remote] msg")  # pylint: disable=protected-access
        br._on_local_channel(sender=f"{BRIDGE_TEXT_PREFIX}remote", text="msg")  # pylint: disable=protected-access
        self.assertEqual(sent, [])

        br._on_local_channel(sender="local", text="plain msg")  # pylint: disable=protected-access
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0], FrameType.CHANNEL_MSG)
        self.assertEqual(sent[0][1]["text"], "plain msg")


if __name__ == "__main__":
    unittest.main()
