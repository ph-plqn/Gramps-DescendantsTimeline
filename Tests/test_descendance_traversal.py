from __future__ import annotations

import unittest

from descendants_timeline.model.child_ref import ChildRef, ChildRelation
from descendants_timeline.model.family import Family
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.traversal.descendance_traversal import (
    DescendanceMode,
    DescendanceTraversal,
    FamilyTraversalState,
    TraversalOptions,
    TraversalRole,
)


def person(
    person_id: str,
    family_ids: tuple[str, ...] = (),
    parent_family_ids: tuple[str, ...] = (),
) -> Person:
    return Person(
        person_id=person_id,
        display_name=person_id,
        gender=PersonGender.UNKNOWN,
        event_refs=(),
        parent_family_ids=parent_family_ids,
        family_ids=family_ids,
    )


def family(
    family_id: str,
    parent1_id: str | None,
    parent2_id: str | None,
    children: tuple[ChildRef, ...] = (),
) -> Family:
    return Family(
        family_id=family_id,
        parent1_id=parent1_id,
        parent2_id=parent2_id,
        event_refs=(),
        child_refs=children,
    )


class DescendanceTraversalTests(unittest.TestCase):
    def test_simple_dfs_preserves_family_and_child_order(self) -> None:
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "I3": person("I3", parent_family_ids=("F1",)),
            "I4": person("I4", parent_family_ids=("F1",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef("I4", ChildRelation.BIRTH, ChildRelation.BIRTH),
                    ChildRef("I3", ChildRelation.BIRTH, ChildRelation.BIRTH),
                ),
            )
        }
        data = RawGenealogyData(people, families, {}, "I1")

        result = DescendanceTraversal().traverse(data, "I1")

        self.assertEqual(
            [row.person_id for row in result.rows],
            ["I1", "I2", "I4", "I3"],
        )
        self.assertEqual(result.rows[0].role, TraversalRole.ROOT)
        self.assertEqual(result.rows[1].role, TraversalRole.SPOUSE)

    def test_biological_only_excludes_adopted_and_sponsored(self) -> None:
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "IB": person("IB", parent_family_ids=("F1",)),
            "IA": person("IA", parent_family_ids=("F1",)),
            "IS": person("IS", parent_family_ids=("F1",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef("IB", ChildRelation.BIRTH, ChildRelation.BIRTH),
                    ChildRef("IA", ChildRelation.ADOPTED, ChildRelation.ADOPTED),
                    ChildRef("IS", ChildRelation.SPONSORED, ChildRelation.SPONSORED),
                ),
            )
        }
        data = RawGenealogyData(people, families, {}, "I1")

        result = DescendanceTraversal().traverse(data, "I1")

        self.assertEqual(
            [row.person_id for row in result.rows],
            ["I1", "I2", "IB"],
        )

    def test_extended_includes_birth_adopted_and_sponsored(self) -> None:
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "IB": person("IB", parent_family_ids=("F1",)),
            "IA": person("IA", parent_family_ids=("F1",)),
            "IS": person("IS", parent_family_ids=("F1",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef("IB", ChildRelation.BIRTH, ChildRelation.BIRTH),
                    ChildRef("IA", ChildRelation.ADOPTED, ChildRelation.ADOPTED),
                    ChildRef("IS", ChildRelation.SPONSORED, ChildRelation.SPONSORED),
                ),
            )
        }
        data = RawGenealogyData(people, families, {}, "I1")

        result = DescendanceTraversal().traverse(
            data,
            "I1",
            TraversalOptions(DescendanceMode.EXTENDED),
        )

        self.assertEqual(
            [row.person_id for row in result.rows],
            ["I1", "I2", "IB", "IA", "IS"],
        )

    def test_relation_is_evaluated_against_current_parent(self) -> None:
        # L'enfant est biologique pour I2 mais pas pour I1.
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "IC": person("IC", parent_family_ids=("F1",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef(
                        "IC",
                        ChildRelation.ADOPTED,
                        ChildRelation.BIRTH,
                    ),
                ),
            )
        }
        data = RawGenealogyData(people, families, {}, "I1")

        from_i1 = DescendanceTraversal().traverse(data, "I1")
        from_i2 = DescendanceTraversal().traverse(data, "I2")

        self.assertEqual([r.person_id for r in from_i1.rows], ["I1", "I2"])
        self.assertEqual([r.person_id for r in from_i2.rows], ["I2", "I1", "IC"])

    def test_generation_belongs_to_occurrence_not_person(self) -> None:
        # I4 apparaît d'abord comme conjoint d'I3 à génération 2,
        # puis comme enfant d'I5 à génération 3.
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "I3": person("I3", ("F2",), ("F1",)),
            "I5": person("I5", ("F3",), ("F1",)),
            "I4": person("I4", ("F2",), ("F3",)),
            "I6": person("I6", ("F3",)),
        }

        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef(
                        "I3",
                        ChildRelation.BIRTH,
                        ChildRelation.BIRTH,
                    ),
                    ChildRef(
                        "I5",
                        ChildRelation.BIRTH,
                        ChildRelation.BIRTH,
                    ),
                ),
            ),

            # I4 apparaît ici comme conjoint d'I3 :
            # occurrence de génération 2.
            "F2": family(
                "F2",
                "I3",
                "I4",
            ),

            # I4 est aussi enfant d'I5 :
            # occurrence de génération 3.
            "F3": family(
                "F3",
                "I5",
                "I6",
                (
                    ChildRef(
                        "I4",
                        ChildRelation.BIRTH,
                        ChildRelation.BIRTH,
                    ),
                ),
            ),
        }

        data = RawGenealogyData(
            people,
            families,
            {},
            "I1",
        )

        result = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        occurrences_i4 = [
            row
            for row in result.rows
            if row.person_id == "I4"
        ]

        generations = [
            row.generation
            for row in occurrences_i4
        ]

        self.assertIn(2, generations)
        self.assertIn(3, generations)

    def test_already_described_family_keeps_spouse_and_reference(self) -> None:
        # I3 et I4 sont tous deux descendants de la racine et forment F2.
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "I3": person("I3", ("F2",), ("F1",)),
            "I4": person("I4", ("F2",), ("F1",)),
            "I5": person("I5", parent_family_ids=("F2",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef("I3", ChildRelation.BIRTH, ChildRelation.BIRTH),
                    ChildRef("I4", ChildRelation.BIRTH, ChildRelation.BIRTH),
                ),
            ),
            "F2": family(
                "F2",
                "I3",
                "I4",
                (ChildRef("I5", ChildRelation.BIRTH, ChildRelation.BIRTH),),
            ),
        }
        data = RawGenealogyData(people, families, {}, "I1")

        result = DescendanceTraversal().traverse(data, "I1")

        f2_occurrences = [
            occ for occ in result.family_occurrences if occ.family_id == "F2"
        ]
        self.assertEqual(len(f2_occurrences), 2)

        first, second = f2_occurrences
        self.assertEqual(first.state, FamilyTraversalState.EXPLORED)
        self.assertEqual(second.state, FamilyTraversalState.ALREADY_DESCRIBED)
        self.assertEqual(second.referenced_row_index, first.descendant_row_index)
        self.assertEqual(second.spouse_person_id, "I3")

        # I5 n'est développé qu'une fois.
        self.assertEqual(
            [r.person_id for r in result.rows].count("I5"),
            1,
        )

    def test_already_described_family_does_not_block_new_remarriage(self) -> None:
        # I4 a F2 (déjà rencontrée via I3) puis F3 avec I6.
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", ("F1",)),
            "I3": person("I3", ("F2",), ("F1",)),
            "I4": person("I4", ("F2", "F3"), ("F1",)),
            "I5": person("I5", parent_family_ids=("F2",)),
            "I6": person("I6", ("F3",)),
            "I7": person("I7", parent_family_ids=("F3",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                "I2",
                (
                    ChildRef("I3", ChildRelation.BIRTH, ChildRelation.BIRTH),
                    ChildRef("I4", ChildRelation.BIRTH, ChildRelation.BIRTH),
                ),
            ),
            "F2": family(
                "F2",
                "I3",
                "I4",
                (ChildRef("I5", ChildRelation.BIRTH, ChildRelation.BIRTH),),
            ),
            "F3": family(
                "F3",
                "I4",
                "I6",
                (ChildRef("I7", ChildRelation.BIRTH, ChildRelation.BIRTH),),
            ),
        }
        data = RawGenealogyData(people, families, {}, "I1")

        result = DescendanceTraversal().traverse(data, "I1")

        f3_occurrences = [
            occ for occ in result.family_occurrences if occ.family_id == "F3"
        ]
        self.assertEqual(len(f3_occurrences), 1)
        self.assertEqual(f3_occurrences[0].state, FamilyTraversalState.EXPLORED)

        # Le second mariage et sa descendance sont bien présents.
        self.assertIn("I6", [r.person_id for r in result.rows])
        self.assertIn("I7", [r.person_id for r in result.rows])

    def test_single_parent_family_is_supported(self) -> None:
        people = {
            "I1": person("I1", ("F1",)),
            "I2": person("I2", parent_family_ids=("F1",)),
        }
        families = {
            "F1": family(
                "F1",
                "I1",
                None,
                (ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),),
            )
        }
        data = RawGenealogyData(people, families, {}, "I1")

        result = DescendanceTraversal().traverse(data, "I1")

        self.assertEqual([r.person_id for r in result.rows], ["I1", "I2"])
        self.assertIsNone(result.family_occurrences[0].spouse_person_id)
        self.assertIsNone(result.family_occurrences[0].spouse_row_index)


if __name__ == "__main__":
    unittest.main()
