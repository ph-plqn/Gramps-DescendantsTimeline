from __future__ import annotations

import unittest

from descendants_timeline.layout.person_placement import PersonPlacement
from descendants_timeline.traversal.descendance_traversal import (
    TraversalRole,
)


class PersonPlacementTests(unittest.TestCase):
    def test_minimal_person_placement_can_be_created(self) -> None:
        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=None,
            x_end=None,
            y=10.0,
        )

        self.assertEqual(placement.person_id, "I1")
        self.assertEqual(placement.row_index, 0)
        self.assertEqual(placement.generation, 1)
        self.assertIs(placement.role, TraversalRole.ROOT)
        self.assertIsNone(placement.family_id)
        self.assertIsNone(placement.spouse_of_person_id)
        self.assertIsNone(placement.x_start)
        self.assertIsNone(placement.x_end)
        self.assertEqual(placement.y, 10.0)
    def test_x_start_kind_can_be_representative(self) -> None:
        from descendants_timeline.layout.person_placement import PositionKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=100.0,
            x_end=None,
            y=10.0,
            x_start_kind=PositionKind.REPRESENTATIVE,
        )

        self.assertIs(placement.x_start_kind, PositionKind.REPRESENTATIVE)

    def test_x_start_kind_can_be_domain_display(self) -> None:
        from descendants_timeline.layout.person_placement import PositionKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=100.0,
            x_end=None,
            y=10.0,
            x_start_kind=PositionKind.DOMAIN_DISPLAY,
        )

        self.assertIs(placement.x_start_kind, PositionKind.DOMAIN_DISPLAY)

    def test_x_end_kind_can_be_representative(self) -> None:
        from descendants_timeline.layout.person_placement import PositionKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=None,
            x_end=200.0,
            y=10.0,
            x_end_kind=PositionKind.REPRESENTATIVE,
        )

        self.assertIs(placement.x_end_kind, PositionKind.REPRESENTATIVE)

    def test_life_bar_kind_can_be_normal(self) -> None:
        from descendants_timeline.layout.person_placement import LifeBarKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=100.0,
            x_end=200.0,
            y=10.0,
            life_bar_kind=LifeBarKind.NORMAL,
        )

        self.assertIs(placement.life_bar_kind, LifeBarKind.NORMAL)

    def test_normal_life_bar_preserves_temporal_coordinates(self) -> None:
        from descendants_timeline.layout.person_placement import LifeBarKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=100.0,
            x_end=200.0,
            y=10.0,
            life_bar_kind=LifeBarKind.NORMAL,
        )

        self.assertEqual(placement.bar_x_start, 100.0)
        self.assertEqual(placement.bar_x_end, 200.0)
        self.assertEqual(placement.x_start, 100.0)
        self.assertEqual(placement.x_end, 200.0)

    def test_reversed_life_bar_starts_at_x_start(self) -> None:
        from descendants_timeline.layout.person_placement import LifeBarKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=200.0,
            x_end=100.0,
            y=10.0,
            life_bar_kind=LifeBarKind.REVERSED,
        )

        self.assertEqual(placement.bar_x_start, 200.0)
        self.assertEqual(placement.x_start, 200.0)
        self.assertEqual(placement.x_end, 100.0)

    def test_reversed_life_bar_uses_short_visual_length(self) -> None:
        from descendants_timeline.layout.person_placement import LifeBarKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=200.0,
            x_end=100.0,
            y=10.0,
            life_bar_kind=LifeBarKind.REVERSED,
            short_bar_length=1825.0,
        )

        self.assertEqual(placement.bar_x_end, 2025.0)
        self.assertEqual(placement.x_start, 200.0)
        self.assertEqual(placement.x_end, 100.0)

    def test_zero_length_life_bar_uses_short_visual_length(self) -> None:
        from descendants_timeline.layout.person_placement import LifeBarKind

        placement = PersonPlacement(
            person_id="I1",
            row_index=0,
            generation=1,
            role=TraversalRole.ROOT,
            family_id=None,
            spouse_of_person_id=None,
            x_start=200.0,
            x_end=200.0,
            y=10.0,
            life_bar_kind=LifeBarKind.ZERO_LENGTH,
            short_bar_length=1825.0,
        )

        self.assertEqual(placement.bar_x_start, 200.0)
        self.assertEqual(placement.bar_x_end, 2025.0)
        self.assertEqual(placement.x_start, 200.0)
        self.assertEqual(placement.x_end, 200.0)

    def test_person_id_must_be_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "person_id must be a non-empty string",
        ):
            PersonPlacement(
                person_id="",
                row_index=0,
                generation=1,
                role=TraversalRole.ROOT,
                family_id=None,
                spouse_of_person_id=None,
                x_start=None,
                x_end=None,
                y=10.0,
            )
    def test_row_index_must_be_non_negative(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "row_index must be a non-negative integer",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=-1,
                generation=1,
                role=TraversalRole.ROOT,
                family_id=None,
                spouse_of_person_id=None,
                x_start=None,
                x_end=None,
                y=10.0,
            )

    def test_generation_must_be_positive(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "generation must be a positive integer",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=0,
                generation=0,
                role=TraversalRole.ROOT,
                family_id=None,
                spouse_of_person_id=None,
                x_start=None,
                x_end=None,
                y=10.0,
            )

    def test_role_must_be_traversal_role(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "role must be a TraversalRole",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=0,
                generation=1,
                role="ROOT",
                family_id=None,
                spouse_of_person_id=None,
                x_start=None,
                x_end=None,
                y=10.0,
            )

    def test_family_id_must_be_none_or_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "family_id must be None or a non-empty string",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=0,
                generation=1,
                role=TraversalRole.DESCENDANT,
                family_id="",
                spouse_of_person_id=None,
                x_start=None,
                x_end=None,
                y=10.0,
            )

    def test_spouse_of_person_id_must_be_none_or_non_empty_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "spouse_of_person_id must be None or a non-empty string",
        ):
            PersonPlacement(
                person_id="I2",
                row_index=1,
                generation=1,
                role=TraversalRole.SPOUSE,
                family_id="F1",
                spouse_of_person_id="",
                x_start=None,
                x_end=None,
                y=20.0,
            )
    def test_y_must_be_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "y must be a number",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=0,
                generation=1,
                role=TraversalRole.ROOT,
                family_id=None,
                spouse_of_person_id=None,
                x_start=None,
                x_end=None,
                y="10.0",
            )

    def test_x_start_must_be_none_or_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "x_start must be None or a number",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=0,
                generation=1,
                role=TraversalRole.ROOT,
                family_id=None,
                spouse_of_person_id=None,
                x_start="100.0",
                x_end=None,
                y=10.0,
            )

    def test_x_end_must_be_none_or_numeric(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "x_end must be None or a number",
        ):
            PersonPlacement(
                person_id="I1",
                row_index=0,
                generation=1,
                role=TraversalRole.ROOT,
                family_id=None,
                spouse_of_person_id=None,
                x_start=None,
                x_end="200.0",
                y=10.0,
            )

if __name__ == "__main__":
    unittest.main()