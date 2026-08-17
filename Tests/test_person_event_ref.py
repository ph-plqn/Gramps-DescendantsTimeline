from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
    PersonEventRef,
)


class PersonEventRefTests(unittest.TestCase):
    def test_valid_principal_role(self) -> None:
        ref = PersonEventRef(
            event_id="E0001",
            semantic_role=EventRoleSemantic.PRINCIPAL,
            source_role="Principal",
        )
        self.assertEqual(ref.event_id, "E0001")
        self.assertIs(ref.semantic_role, EventRoleSemantic.PRINCIPAL)
        self.assertEqual(ref.source_role, "Principal")

    def test_valid_witness_role(self) -> None:
        ref = PersonEventRef(
            event_id="E0002",
            semantic_role=EventRoleSemantic.WITNESS,
            source_role="Témoin",
        )
        self.assertIs(ref.semantic_role, EventRoleSemantic.WITNESS)

    def test_custom_role_is_preserved_with_unknown_semantic(self) -> None:
        ref = PersonEventRef(
            event_id="E0003",
            semantic_role=EventRoleSemantic.UNKNOWN,
            source_role="Parrain militaire",
        )
        self.assertEqual(ref.source_role, "Parrain militaire")

    def test_rejects_empty_event_id(self) -> None:
        with self.assertRaises(ValueError):
            PersonEventRef("", EventRoleSemantic.PRINCIPAL, "Principal")

    def test_rejects_blank_event_id(self) -> None:
        with self.assertRaises(ValueError):
            PersonEventRef("   ", EventRoleSemantic.PRINCIPAL, "Principal")

    def test_rejects_semantic_role_as_plain_string(self) -> None:
        with self.assertRaises(TypeError):
            PersonEventRef("E0004", "PRINCIPAL", "Principal")  # type: ignore[arg-type]

    def test_rejects_empty_source_role(self) -> None:
        with self.assertRaises(ValueError):
            PersonEventRef("E0005", EventRoleSemantic.PRINCIPAL, "")

    def test_rejects_blank_source_role(self) -> None:
        with self.assertRaises(ValueError):
            PersonEventRef("E0006", EventRoleSemantic.PRINCIPAL, "   ")

    def test_person_event_ref_is_immutable(self) -> None:
        ref = PersonEventRef(
            event_id="E0007",
            semantic_role=EventRoleSemantic.INFORMANT,
            source_role="Déclarant",
        )
        with self.assertRaises(FrozenInstanceError):
            ref.source_role = "Principal"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
