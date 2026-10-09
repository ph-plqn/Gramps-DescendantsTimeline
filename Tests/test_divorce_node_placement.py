from __future__ import annotations

import unittest

from descendants_timeline.layout.divorce_node_placement import (
    DivorceNodePlacement,
)


class DivorceNodePlacementTests(unittest.TestCase):
    def test_minimal_divorce_node_placement_can_be_created(self) -> None:
        placement = DivorceNodePlacement(
            family_id="F1",
            descendant_person_id="I1",
            spouse_person_id="I2",
            x=100.0,
            y=15.0,
            descendant_row_index=0,
            spouse_row_index=1,
        )

        self.assertEqual(placement.family_id, "F1")
        self.assertEqual(placement.descendant_person_id, "I1")
        self.assertEqual(placement.spouse_person_id, "I2")
        self.assertEqual(placement.x, 100.0)
        self.assertEqual(placement.y, 15.0)
        self.assertEqual(placement.descendant_row_index, 0)
        self.assertEqual(placement.spouse_row_index, 1)


if __name__ == "__main__":
    unittest.main()
