from __future__ import annotations

import unittest

from descendants_timeline.layout.remarriage_segment_placement import (
    RemarriageSegmentPlacement,
)


class RemarriageSegmentPlacementTests(unittest.TestCase):
    def test_minimal_remarriage_segment_placement_can_be_created(self) -> None:
        placement = RemarriageSegmentPlacement(
            person_id="I1",
            x=100.0,
            y_start=10.0,
            y_end=20.0,
        )

        self.assertEqual(placement.person_id, "I1")
        self.assertEqual(placement.x, 100.0)
        self.assertEqual(placement.y_start, 10.0)
        self.assertEqual(placement.y_end, 20.0)

    def test_person_id_must_be_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "person_id must be a non-empty string",
        ):
            RemarriageSegmentPlacement(
                person_id="",
                x=100.0,
                y_start=10.0,
                y_end=20.0,
            )
    def test_x_must_be_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "x must be a number",
        ):
            RemarriageSegmentPlacement(
                person_id="I1",
                x="100.0",
                y_start=10.0,
                y_end=20.0,
            )
    def test_y_start_must_be_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "y_start must be a number",
        ):
            RemarriageSegmentPlacement(
                person_id="I1",
                x=100.0,
                y_start="10.0",
                y_end=20.0,
            )
    def test_y_end_must_be_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "y_end must be a number",
        ):
            RemarriageSegmentPlacement(
                person_id="I1",
                x=100.0,
                y_start=10.0,
                y_end="20.0",
            )
    def test_y_start_must_not_be_greater_than_y_end(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "y_start must not be greater than y_end",
        ):
            RemarriageSegmentPlacement(
                person_id="I1",
                x=100.0,
                y_start=20.0,
                y_end=10.0,
            )
if __name__ == "__main__":
    unittest.main()