from __future__ import annotations

import unittest

from descendants_timeline.layout.marriage_node_placement import (
    MarriageNodePlacement,
)


class MarriageNodePlacementTests(unittest.TestCase):
    def test_minimal_marriage_node_placement_can_be_created(self) -> None:
        placement = MarriageNodePlacement(
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

    def test_family_id_must_be_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "family_id must be a non-empty string",
        ):
            MarriageNodePlacement(
                family_id="",
                descendant_person_id="I1",
                spouse_person_id="I2",
                x=100.0,
                y=15.0,
                descendant_row_index=0,
                spouse_row_index=1,
            )
    def test_descendant_person_id_must_be_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "descendant_person_id must be a non-empty string",
        ):
            MarriageNodePlacement(
                family_id="F1",
                descendant_person_id="",
                spouse_person_id="I2",
                x=100.0,
                y=15.0,
                descendant_row_index=0,
                spouse_row_index=1,
            )

    def test_spouse_person_id_must_be_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "spouse_person_id must be a non-empty string",
        ):
            MarriageNodePlacement(
                family_id="F1",
                descendant_person_id="I1",
                spouse_person_id="",
                x=100.0,
                y=15.0,
                descendant_row_index=0,
                spouse_row_index=1,
            )

    def test_x_must_be_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "x must be a number",
        ):
            MarriageNodePlacement(
                family_id="F1",
                descendant_person_id="I1",
                spouse_person_id="I2",
                x="100.0",
                y=15.0,
                descendant_row_index=0,
                spouse_row_index=1,
            )
    def test_y_must_be_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "y must be a number",
        ):
            MarriageNodePlacement(
                family_id="F1",
                descendant_person_id="I1",
                spouse_person_id="I2",
                x=100.0,
                y="15.0",
                descendant_row_index=0,
                spouse_row_index=1,
            )
    def test_descendant_row_index_must_be_non_negative(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "descendant_row_index must be a non-negative integer",
        ):
            MarriageNodePlacement(
                family_id="F1",
                descendant_person_id="I1",
                spouse_person_id="I2",
                x=100.0,
                y=15.0,
                descendant_row_index=-1,
                spouse_row_index=1,
            )
    def test_spouse_row_index_must_be_non_negative(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "spouse_row_index must be a non-negative integer",
        ):
            MarriageNodePlacement(
                family_id="F1",
                descendant_person_id="I1",
                spouse_person_id="I2",
                x=100.0,
                y=15.0,
                descendant_row_index=0,
                spouse_row_index=-1,
            )
if __name__ == "__main__":
    unittest.main()