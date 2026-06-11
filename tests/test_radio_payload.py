import unittest
from types import SimpleNamespace

from radio import NodeRadio


class NodeRadioPayloadTests(unittest.TestCase):
    def test_split_string_payload_with_sender_prefix(self):
        sender, text, hops = NodeRadio._split_payload("CHEMobile: Hello world!")

        self.assertEqual(sender, "CHEMobile")
        self.assertEqual(text, "Hello world!")
        self.assertIsNone(hops)

    def test_split_string_payload_without_sender_keeps_unknown(self):
        sender, text, hops = NodeRadio._split_payload("Hello world!")

        self.assertEqual(sender, "?")
        self.assertEqual(text, "Hello world!")
        self.assertIsNone(hops)

    def test_split_dict_payload_still_prefers_sender_prefix(self):
        payload = {
            "sender_prefix": "CHEMobile",
            "sender": "ignored",
            "text": "Hello world!",
            "hops": 2,
        }

        self.assertEqual(
            NodeRadio._split_payload(payload),
            ("CHEMobile", "Hello world!", 2),
        )

    def test_split_object_payload_uses_attributes(self):
        payload = SimpleNamespace(
            sender="CHEMobile",
            text="Hello world!",
            hops=1,
        )

        self.assertEqual(
            NodeRadio._split_payload(payload),
            ("CHEMobile", "Hello world!", 1),
        )


if __name__ == "__main__":
    unittest.main()
