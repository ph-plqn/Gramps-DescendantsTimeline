"""Tests unitaires de TemporalTarget."""

from dataclasses import FrozenInstanceError
import unittest

from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)


class TestTemporalTarget(unittest.TestCase):
    """Tests du modèle de cible temporelle."""

    def test_valid_person_birth_target(self) -> None:
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I_VICTOR",
            semantic=TargetSemantic.BIRTH,
        )

        self.assertEqual(target.owner_type, TemporalOwnerType.PERSON)
        self.assertEqual(target.owner_id, "I_VICTOR")
        self.assertEqual(target.semantic, TargetSemantic.BIRTH)

    def test_valid_person_death_target(self) -> None:
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I_VICTOR",
            semantic=TargetSemantic.DEATH,
        )

        self.assertEqual(target.owner_type, TemporalOwnerType.PERSON)
        self.assertEqual(target.owner_id, "I_VICTOR")
        self.assertEqual(target.semantic, TargetSemantic.DEATH)

    def test_valid_family_marriage_target(self) -> None:
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F0020",
            semantic=TargetSemantic.MARRIAGE,
        )

        self.assertEqual(target.owner_type, TemporalOwnerType.FAMILY)
        self.assertEqual(target.owner_id, "F0020")
        self.assertEqual(target.semantic, TargetSemantic.MARRIAGE)

    def test_target_is_immutable(self) -> None:
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I_VICTOR",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(FrozenInstanceError):
            target.owner_id = "I_OTHER"

    def test_owner_type_must_be_temporal_owner_type(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTarget(
                owner_type="PERSON",
                owner_id="I_VICTOR",
                semantic=TargetSemantic.BIRTH,
            )

    def test_owner_id_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="",
                semantic=TargetSemantic.BIRTH,
            )

    def test_owner_id_must_not_be_blank(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="   ",
                semantic=TargetSemantic.BIRTH,
            )

    def test_semantic_must_be_target_semantic(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I_VICTOR",
                semantic="BIRTH",
            )

    def test_family_birth_target_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id="F0020",
                semantic=TargetSemantic.BIRTH,
            )

    def test_family_death_target_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id="F0020",
                semantic=TargetSemantic.DEATH,
            )

    def test_person_marriage_target_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I_VICTOR",
                semantic=TargetSemantic.MARRIAGE,
            )


if __name__ == "__main__":
    unittest.main()