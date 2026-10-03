from __future__ import annotations

import unittest

from descendants_timeline.layout.timeline_layout import TimelineLayout


class TimelineLayoutTests(unittest.TestCase):
    def test_empty_timeline_layout_can_be_created(self) -> None:
        layout = TimelineLayout(
            person_placements=(),
            marriage_node_placements=(),
            remarriage_segment_placements=(),
        )

        self.assertEqual(layout.person_placements, ())
        self.assertEqual(layout.marriage_node_placements, ())
        self.assertEqual(layout.remarriage_segment_placements, ())

    def test_person_placements_must_be_tuple(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "person_placements must be a tuple",
        ):
            TimelineLayout(
                person_placements=[],
                marriage_node_placements=(),
                remarriage_segment_placements=(),
            )
    def test_person_placements_must_contain_person_placements(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "person_placements must contain only PersonPlacement objects",
        ):
            TimelineLayout(
                person_placements=("I1",),
                marriage_node_placements=(),
                remarriage_segment_placements=(),
            )
    def test_marriage_node_placements_must_be_tuple(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "marriage_node_placements must be a tuple",
        ):
            TimelineLayout(
                person_placements=(),
                marriage_node_placements=[],
                remarriage_segment_placements=(),
            )
    def test_marriage_node_placements_must_contain_marriage_node_placements(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "marriage_node_placements must contain only MarriageNodePlacement objects",
        ):
            TimelineLayout(
                person_placements=(),
                marriage_node_placements=("F1",),
                remarriage_segment_placements=(),
            )
    def test_remarriage_segment_placements_must_be_tuple(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "remarriage_segment_placements must be a tuple",
        ):
            TimelineLayout(
                person_placements=(),
                marriage_node_placements=(),
                remarriage_segment_placements=[],
            )
    def test_remarriage_segment_placements_must_contain_remarriage_segment_placements(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "remarriage_segment_placements must contain only "
            "RemarriageSegmentPlacement objects",
        ):
            TimelineLayout(
                person_placements=(),
                marriage_node_placements=(),
                remarriage_segment_placements=("I1",),
            )
if __name__ == "__main__":
    unittest.main()