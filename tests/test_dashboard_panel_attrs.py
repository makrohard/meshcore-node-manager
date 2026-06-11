import inspect
import unittest

import dashboard


class DashboardPanelAttributeTests(unittest.TestCase):
    def test_panel_does_not_overwrite_tk_widget_path(self):
        source = inspect.getsource(dashboard._Panel.__init__)  # pylint: disable=protected-access
        self.assertNotIn("self._w =", source)
        self.assertNotIn("self._h =", source)
        self.assertIn("self._canvas_width", source)
        self.assertIn("self._canvas_height", source)


if __name__ == "__main__":
    unittest.main()
