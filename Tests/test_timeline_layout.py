from __future__ import annotations

import unittest

from descendants_timeline.layout.divorce_node_placement import (
    DivorceNodePlacement,
)
from descendants_timeline.layout.timeline_layout import TimelineLayout


class TimelineLayoutTests(unittest.TestCase):
    def test_timeline_layout_stores_branch_reference_placements(self) -> None:
        from descendants_timeline.layout.branch_reference_placement import (
            BranchReferencePlacement,
        )

        reference = BranchReferencePlacement(
            family_id="F1",
            descendant_row_index=3,
            spouse_row_index=4,
            referenced_row_index=1,
            visual_rank=5,
            y=170.0,
        )
        layout = TimelineLayout(
            person_placements=(),
            marriage_node_placements=(),
            remarriage_segment_placements=(),
            branch_reference_placements=(reference,),
        )

        self.assertEqual(layout.branch_reference_placements, (reference,))

    def test_empty_timeline_layout_can_be_created(self) -> None:
        layout = TimelineLayout(
            person_placements=(),
            marriage_node_placements=(),
            remarriage_segment_placements=(),
        )

        self.assertEqual(layout.person_placements, ())
        self.assertEqual(layout.marriage_node_placements, ())
        self.assertEqual(layout.remarriage_segment_placements, ())

    def test_divorce_node_placements_can_be_provided(self) -> None:
        divorce = DivorceNodePlacement(
            family_id="F1",
            descendant_person_id="I1",
            spouse_person_id="I2",
            x=100.0,
            y=15.0,
            descendant_row_index=0,
            spouse_row_index=1,
        )
        layout = TimelineLayout(
            person_placements=(),
            marriage_node_placements=(),
            remarriage_segment_placements=(),
            diagnostic_placements=(),
            divorce_node_placements=(divorce,),
        )

        self.assertEqual(layout.divorce_node_placements, (divorce,))

    def test_diagnostic_placements_default_to_empty_tuple(self) -> None:
        layout = TimelineLayout(
            person_placements=(),
            marriage_node_placements=(),
            remarriage_segment_placements=(),
        )

        self.assertEqual(layout.diagnostic_placements, ())

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