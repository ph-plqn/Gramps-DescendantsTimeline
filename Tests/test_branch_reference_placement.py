from __future__ import annotations

import unittest

from descendants_timeline.layout.branch_reference_placement import (
    BranchReferencePlacement,
)


class BranchReferencePlacementTests(unittest.TestCase):
    def test_minimal_branch_reference_placement_can_be_created(self) -> None:
        placement = BranchReferencePlacement(
            family_id="F1",
            descendant_row_index=3,
            spouse_row_index=4,
            referenced_row_index=1,
            visual_rank=5,
            y=170.0,
        )

        self.assertEqual(placement.family_id, "F1")
        self.assertEqual(placement.descendant_row_index, 3)
        self.assertEqual(placement.spouse_row_index, 4)
        self.assertEqual(placement.referenced_row_index, 1)
        self.assertEqual(placement.visual_rank, 5)
        self.assertEqual(placement.y, 170.0)

    def test_branch_reference_placement_stores_horizontal_center(self) -> None:
        placement = BranchReferencePlacement(
            family_id="F1",
            descendant_row_index=3,
            spouse_row_index=4,
            referenced_row_index=1,
            visual_rank=5,
            y=170.0,
            x=250.0,
        )

        self.assertEqual(placement.x, 250.0)


if __name__ == "__main__":
    unittest.main()
