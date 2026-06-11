import unittest

from analytics import haversine_km, link_label, link_quality, per_contact_reliability
from radio import Contact, Message


class AnalyticsTests(unittest.TestCase):
    def test_haversine_zero_distance(self):
        self.assertAlmostEqual(haversine_km(48.0, 11.0, 48.0, 11.0), 0.0)

    def test_link_quality_and_label(self):
        contact = Contact(key="k", name="n", rssi=-60, snr=10)
        self.assertAlmostEqual(link_quality(contact), 1.0)
        self.assertEqual(link_label(link_quality(contact)), "Excellent")

    def test_per_contact_reliability_counts_direct_tx_only(self):
        messages = [
            Message(1, "tx", "direct", "A", "x", status="delivered"),
            Message(2, "tx", "direct", "A", "x", status="timeout"),
            Message(3, "rx", "direct", "A", "x", status="received"),
            Message(4, "tx", "channel", "channel", "x", status="sent"),
        ]

        reliability = per_contact_reliability(messages)
        self.assertEqual(reliability["A"]["sent"], 2)
        self.assertEqual(reliability["A"]["delivered"], 1)
        self.assertEqual(reliability["A"]["timeout"], 1)
        self.assertEqual(reliability["A"]["rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
