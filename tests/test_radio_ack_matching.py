import time
import unittest

from events import EventBus
from radio import Message, NodeRadio


class _Event:
    def __init__(self, payload=None, attributes=None):
        self.payload = payload
        self.attributes = attributes or {}


class NodeRadioAckMatchingTests(unittest.TestCase):
    def test_confirm_delivery_uses_ack_code_not_newest_pending(self):
        radio = NodeRadio(EventBus())
        old = Message(
            local_id=1,
            direction="tx",
            kind="direct",
            peer="alpha",
            text="first",
            ts_sent=time.time() - 1.0,
            status="sent",
            expected_ack="aa55",
        )
        new = Message(
            local_id=2,
            direction="tx",
            kind="direct",
            peer="bravo",
            text="second",
            ts_sent=time.time() - 0.1,
            status="sent",
            expected_ack="bb66",
        )
        with radio._msg_lock:  # pylint: disable=protected-access
            radio._pending[old.local_id] = old  # pylint: disable=protected-access
            radio._pending[new.local_id] = new  # pylint: disable=protected-access

        radio._confirm_delivery(_Event(attributes={"code": "aa55"}))  # pylint: disable=protected-access

        self.assertEqual(old.status, "delivered")
        self.assertEqual(new.status, "sent")
        with radio._msg_lock:  # pylint: disable=protected-access
            self.assertNotIn(old.local_id, radio._pending)  # pylint: disable=protected-access
            self.assertIn(new.local_id, radio._pending)  # pylint: disable=protected-access

    def test_unknown_coded_ack_does_not_fall_back_to_wrong_pending(self):
        radio = NodeRadio(EventBus())
        msg = Message(
            local_id=1,
            direction="tx",
            kind="direct",
            peer="alpha",
            text="hello",
            ts_sent=time.time() - 0.1,
            status="sent",
            expected_ack="aa55",
        )
        with radio._msg_lock:  # pylint: disable=protected-access
            radio._pending[msg.local_id] = msg  # pylint: disable=protected-access

        radio._confirm_delivery(_Event(attributes={"code": "bb66"}))  # pylint: disable=protected-access

        self.assertEqual(msg.status, "sent")
        with radio._msg_lock:  # pylint: disable=protected-access
            self.assertIn(msg.local_id, radio._pending)  # pylint: disable=protected-access

    def test_uncoded_ack_keeps_compatibility_fallback(self):
        radio = NodeRadio(EventBus())
        msg = Message(
            local_id=1,
            direction="tx",
            kind="direct",
            peer="alpha",
            text="hello",
            ts_sent=time.time() - 0.1,
            status="sent",
        )
        with radio._msg_lock:  # pylint: disable=protected-access
            radio._pending[msg.local_id] = msg  # pylint: disable=protected-access

        radio._confirm_delivery(_Event())  # pylint: disable=protected-access

        self.assertEqual(msg.status, "delivered")

    def test_msg_sent_advances_matching_pending_only(self):
        radio = NodeRadio(EventBus())
        first = Message(
            local_id=1,
            direction="tx",
            kind="direct",
            peer="alpha",
            text="first",
            ts_sent=time.time(),
            status="pending",
            expected_ack="aa55",
        )
        second = Message(
            local_id=2,
            direction="tx",
            kind="direct",
            peer="bravo",
            text="second",
            ts_sent=time.time(),
            status="pending",
            expected_ack="bb66",
        )
        with radio._msg_lock:  # pylint: disable=protected-access
            radio._pending[first.local_id] = first  # pylint: disable=protected-access
            radio._pending[second.local_id] = second  # pylint: disable=protected-access

        radio._advance_pending(_Event(payload={"expected_ack": bytes.fromhex("bb66")}))  # pylint: disable=protected-access

        self.assertEqual(first.status, "pending")
        self.assertEqual(second.status, "sent")


if __name__ == "__main__":
    unittest.main()
