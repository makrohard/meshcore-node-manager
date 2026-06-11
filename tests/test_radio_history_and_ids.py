import threading
import unittest

from config import HISTORY_STORE_LIMIT
from events import EventBus
from radio import Message, NodeRadio


class NodeRadioHistoryAndIdTests(unittest.TestCase):
    def test_history_backing_store_is_bounded(self):
        radio = NodeRadio(EventBus())

        with radio._msg_lock:  # pylint: disable=protected-access
            for i in range(HISTORY_STORE_LIMIT + 25):
                radio._history.append(  # pylint: disable=protected-access
                    Message(
                        local_id=i,
                        direction="rx",
                        kind="channel",
                        peer="channel",
                        text=str(i),
                        ts_received=float(i),
                        status="received",
                    )
                )

        with radio._msg_lock:  # pylint: disable=protected-access
            self.assertEqual(len(radio._history), HISTORY_STORE_LIMIT)  # pylint: disable=protected-access

        hist = radio.message_history(limit=HISTORY_STORE_LIMIT + 100)
        self.assertEqual(len(hist), HISTORY_STORE_LIMIT)
        self.assertEqual(hist[0].local_id, 25)
        self.assertEqual(hist[-1].local_id, HISTORY_STORE_LIMIT + 24)

    def test_next_id_is_unique_under_threads(self):
        radio = NodeRadio(EventBus())
        ids = []
        out_lock = threading.Lock()

        def worker():
            local = [radio._next_id() for _ in range(500)]  # pylint: disable=protected-access
            with out_lock:
                ids.extend(local)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(ids), 10_000)
        self.assertEqual(len(set(ids)), len(ids))


if __name__ == "__main__":
    unittest.main()
