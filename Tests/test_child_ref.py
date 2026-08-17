from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from descendants_timeline.model.child_ref import ChildRef, ChildRelation


class ChildRefTests(unittest.TestCase):
    def test_valid_biological_child_for_both_parents(self) -> None:
        ref = ChildRef(
            person_id="I0001",
            relation_to_parent1=ChildRelation.BIRTH,
            relation_to_parent2=ChildRelation.BIRTH,
        )
        self.assertEqual(ref.person_id, "I0001")
        self.assertIs(ref.relation_to_parent1, ChildRelation.BIRTH)
        self.assertIs(ref.relation_to_parent2, ChildRelation.BIRTH)

    def test_relations_are_independent_for_each_parent(self) -> None:
        ref = ChildRef(
            person_id="I0002",
            relation_to_parent1=ChildRelation.SPONSORED,
            relation_to_parent2=ChildRelation.NONE,
        )
        self.assertIs(ref.relation_to_parent1, ChildRelation.SPONSORED)
        self.assertIs(ref.relation_to_parent2, ChildRelation.NONE)

    def test_adopted_relation_is_preserved(self) -> None:
        ref = ChildRef(
            person_id="I0003",
            relation_to_parent1=ChildRelation.ADOPTED,
            relation_to_parent2=ChildRelation.ADOPTED,
        )
        self.assertIs(ref.relation_to_parent1, ChildRelation.ADOPTED)
        self.assertIs(ref.relation_to_parent2, ChildRelation.ADOPTED)

    def test_unknown_relation_is_valid_data(self) -> None:
        ref = ChildRef(
            person_id="I0004",
            relation_to_parent1=ChildRelation.UNKNOWN,
            relation_to_parent2=ChildRelation.BIRTH,
        )
        self.assertIs(ref.relation_to_parent1, ChildRelation.UNKNOWN)

    def test_rejects_empty_person_id(self) -> None:
        with self.assertRaises(ValueError):
            ChildRef("", ChildRelation.BIRTH, ChildRelation.BIRTH)

    def test_rejects_blank_person_id(self) -> None:
        with self.assertRaises(ValueError):
            ChildRef("   ", ChildRelation.BIRTH, ChildRelation.BIRTH)

    def test_rejects_parent1_relation_as_plain_string(self) -> None:
        with self.assertRaises(TypeError):
            ChildRef("I0005", "BIRTH", ChildRelation.BIRTH)  # type: ignore[arg-type]

    def test_rejects_parent2_relation_as_plain_string(self) -> None:
        with self.assertRaises(TypeError):
            ChildRef("I0006", ChildRelation.BIRTH, "BIRTH")  # type: ignore[arg-type]

    def test_child_ref_is_immutable(self) -> None:
        ref = ChildRef(
            person_id="I0007",
            relation_to_parent1=ChildRelation.BIRTH,
            relation_to_parent2=ChildRelation.BIRTH,
        )
        with self.assertRaises(FrozenInstanceError):
            ref.relation_to_parent1 = ChildRelation.ADOPTED  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
