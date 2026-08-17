from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from descendants_timeline.model.child_ref import ChildRef, ChildRelation
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)


def make_event_ref(event_id: str = "E0100") -> FamilyEventRef:
    return FamilyEventRef(
        event_id=event_id,
        semantic_role=FamilyRoleSemantic.FAMILY,
        source_role="Family",
    )


def make_child_ref(person_id: str = "I0100") -> ChildRef:
    return ChildRef(
        person_id=person_id,
        relation_to_parent1=ChildRelation.BIRTH,
        relation_to_parent2=ChildRelation.BIRTH,
    )


class FamilyTests(unittest.TestCase):
    def test_valid_family_with_two_parents(self) -> None:
        family = Family("F0001", "I0001", "I0002", (make_event_ref(),), (make_child_ref(),))
        self.assertEqual(family.family_id, "F0001")
        self.assertEqual(family.parent1_id, "I0001")
        self.assertEqual(family.parent2_id, "I0002")

    def test_family_with_only_parent1_is_valid(self) -> None:
        family = Family("F0002", "I0003", None, (), (make_child_ref("I0101"),))
        self.assertEqual(family.parent1_id, "I0003")
        self.assertIsNone(family.parent2_id)

    def test_family_with_only_parent2_is_valid(self) -> None:
        family = Family("F0003", None, "I0004", (), (make_child_ref("I0102"),))
        self.assertIsNone(family.parent1_id)
        self.assertEqual(family.parent2_id, "I0004")

    def test_family_without_children_is_valid(self) -> None:
        family = Family("F0004", "I0005", "I0006", (), ())
        self.assertEqual(family.child_refs, ())

    def test_family_without_events_is_valid(self) -> None:
        family = Family("F0005", "I0007", "I0008", (), (make_child_ref("I0103"),))
        self.assertEqual(family.event_refs, ())

    def test_rejects_empty_family_id(self) -> None:
        with self.assertRaises(ValueError):
            Family("", "I0001", "I0002", (), ())

    def test_rejects_blank_family_id(self) -> None:
        with self.assertRaises(ValueError):
            Family("   ", "I0001", "I0002", (), ())

    def test_rejects_empty_parent1_id(self) -> None:
        with self.assertRaises(ValueError):
            Family("F0006", "", "I0002", (), ())

    def test_rejects_empty_parent2_id(self) -> None:
        with self.assertRaises(ValueError):
            Family("F0007", "I0001", "   ", (), ())

    def test_rejects_non_string_parent_id(self) -> None:
        with self.assertRaises(TypeError):
            Family("F0008", 123, "I0002", (), ())  # type: ignore[arg-type]

    def test_rejects_event_refs_as_list(self) -> None:
        with self.assertRaises(TypeError):
            Family("F0009", "I0001", "I0002", [make_event_ref()], ())  # type: ignore[arg-type]

    def test_rejects_invalid_object_in_event_refs(self) -> None:
        with self.assertRaises(TypeError):
            Family("F0010", "I0001", "I0002", ("E0100",), ())  # type: ignore[arg-type]

    def test_rejects_child_refs_as_list(self) -> None:
        with self.assertRaises(TypeError):
            Family("F0011", "I0001", "I0002", (), [make_child_ref()])  # type: ignore[arg-type]

    def test_rejects_invalid_object_in_child_refs(self) -> None:
        with self.assertRaises(TypeError):
            Family("F0012", "I0001", "I0002", (), ("I0100",))  # type: ignore[arg-type]

    def test_event_order_is_preserved(self) -> None:
        first = make_event_ref("E0200")
        second = make_event_ref("E0100")
        family = Family("F0013", "I0001", "I0002", (first, second), ())
        self.assertEqual(family.event_refs, (first, second))

    def test_child_order_is_preserved(self) -> None:
        first = make_child_ref("I0200")
        second = make_child_ref("I0100")
        family = Family("F0014", "I0001", "I0002", (), (first, second))
        self.assertEqual(family.child_refs, (first, second))

    def test_parent_positions_are_preserved(self) -> None:
        family = Family("F0015", "I0099", "I0001", (), ())
        self.assertEqual(family.parent1_id, "I0099")
        self.assertEqual(family.parent2_id, "I0001")

    def test_family_is_immutable(self) -> None:
        family = Family("F0016", "I0001", "I0002", (), ())
        with self.assertRaises(FrozenInstanceError):
            family.parent1_id = "I0099"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
