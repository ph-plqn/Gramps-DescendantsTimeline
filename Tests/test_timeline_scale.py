from __future__ import annotations

import unittest

from datetime import date

from descendants_timeline.layout.timeline_scale import TimelineScale


class TimelineScaleTests(unittest.TestCase):
    def test_date_to_x_uses_ordinal_day(self) -> None:
        scale = TimelineScale()

        value = date(1900, 1, 1)

        self.assertEqual(
            scale.date_to_x(value),
            float(value.toordinal()),
        )
    def test_date_to_x_preserves_day_distance(self) -> None:
        scale = TimelineScale()

        first = date(1900, 1, 1)
        second = date(1900, 1, 11)

        self.assertEqual(
            scale.date_to_x(second) - scale.date_to_x(first),
            10.0,
        )
    def test_x_to_date_restores_original_date(self) -> None:
        scale = TimelineScale()

        original = date(1900, 1, 1)

        x = scale.date_to_x(original)

        self.assertEqual(
            scale.x_to_date(x),
            original,
        )
 
if __name__ == "__main__":
    unittest.main()