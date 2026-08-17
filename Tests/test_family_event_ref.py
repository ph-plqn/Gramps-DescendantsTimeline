from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)


class FamilyEventRefTests(unittest.TestCase):
    def test_valid_family_role(self) -> None:
        ref = FamilyEventRef(
            event_id="E0100",
            semantic_role=FamilyRoleSemantic.FAMILY,
            source_role="Family",
        )

        self.assertEqual(ref.event_id, "E0100")
        self.assertIs(ref.semantic_role, FamilyRoleSemantic.FAMILY)
        self.assertEqual(ref.source_role, "Family")

    def test_custom_role_is_preserved_with_unknown_semantic(self) -> None:
        ref = FamilyEventRef(
            event_id="E0101",
            semantic_role=FamilyRoleSemantic.UNKNOWN,
            source_role="Rôle familial personnalisé",
        )

        self.assertIs(ref.semantic_role, FamilyRoleSemantic.UNKNOWN)
        self.assertEqual(ref.source_role, "Rôle familial personnalisé")

    def test_rejects_empty_event_id(self) -> None:
        with self.assertRaises(ValueError):
            FamilyEventRef(
                event_id="",
                semantic_role=FamilyRoleSemantic.FAMILY,
                source_role="Family",
            )

    def test_rejects_blank_event_id(self) -> None:
        with self.assertRaises(ValueError):
            FamilyEventRef(
                event_id="   ",
                semantic_role=FamilyRoleSemantic.FAMILY,
                source_role="Family",
            )

    def test_rejects_semantic_role_as_plain_string(self) -> None:
        with self.assertRaises(TypeError):
            FamilyEventRef(
                event_id="E0102",
                semantic_role="FAMILY",  # type: ignore[arg-type]
                source_role="Family",
            )

    def test_rejects_empty_source_role(self) -> None:
        with self.assertRaises(ValueError):
            FamilyEventRef(
                event_id="E0103",
                semantic_role=FamilyRoleSemantic.FAMILY,
                source_role="",
            )

    def test_rejects_blank_source_role(self) -> None:
        with self.assertRaises(ValueError):
            FamilyEventRef(
                event_id="E0104",
                semantic_role=FamilyRoleSemantic.FAMILY,
                source_role="   ",
            )

    def test_family_event_ref_is_immutable(self) -> None:
        ref = FamilyEventRef(
            event_id="E0105",
            semantic_role=FamilyRoleSemantic.FAMILY,
            source_role="Family",
        )

        with self.assertRaises(FrozenInstanceError):
            ref.source_role = "Autre rôle"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
