import unittest

from bridge import Bridge


class _Settings:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, fallback=None):
        return self._values.get(key, fallback)


class BridgeBindHostTests(unittest.TestCase):
    def test_bridge_default_host_is_localhost(self):
        bridge = Bridge(None, _Settings())
        self.assertEqual(bridge._settings.get("bridge_host", "127.0.0.1"), "127.0.0.1")

    def test_bridge_accepts_explicit_all_interfaces_host(self):
        bridge = Bridge(None, _Settings({"bridge_host": "0.0.0.0"}))
        self.assertEqual(bridge._settings.get("bridge_host", "127.0.0.1"), "0.0.0.0")


if __name__ == "__main__":
    unittest.main()
