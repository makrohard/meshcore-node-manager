import unittest
from types import SimpleNamespace

from events import EventBus
from radio import Contact, NodeRadio


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


    def test_received_direct_payload_resolves_pubkey_prefix_from_contacts(self):
        radio = NodeRadio(EventBus())
        radio.upsert_contact(Contact(
            key="abcdef1234567890",
            name="CHEMobile",
            raw={"public_key": "abcdef1234567890fedcba"},
        ))

        self.assertEqual(
            radio._split_received_payload({
                "type": "PRIV",
                "pubkey_prefix": "abcdef123456",
                "text": "message",
                "hops": 3,
            }),
            ("CHEMobile", "message", 3),
        )

    def test_received_direct_payload_falls_back_to_pubkey_prefix(self):
        radio = NodeRadio(EventBus())

        self.assertEqual(
            radio._split_received_payload({
                "type": "PRIV",
                "pubkey_prefix": "abcdef123456",
                "text": "message",
            }),
            ("abcdef123456", "message", None),
        )



if __name__ == "__main__":
    unittest.main()
