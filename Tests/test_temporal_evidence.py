"""Tests unitaires de TemporalEvidence."""

from dataclasses import FrozenInstanceError
from datetime import date
import unittest

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.family_event_ref import FamilyRoleSemantic
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.model.temporal_target import TemporalOwnerType


class TestTemporalEvidence(unittest.TestCase):
    """Tests du modèle de preuve temporelle."""

    def setUp(self) -> None:
        """Construit une date Gramps certaine et utilisable comme preuve."""

        self.event_date = date(1790, 1, 12)

        self.usable_date = TemporalValue(
            source_value="12/01/1790",
            source_calendar="GREGORIAN",
            normalized_minimum=self.event_date,
            normalized_maximum=self.event_date,
            representative_value=self.event_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

    def make_person_evidence(self, **changes) -> TemporalEvidence:
        """Construit l'exemple Victor témoin de la naissance de Joseph."""

        values = {
            "owner_type": EvidenceOwnerType.PERSON,
            "owner_id": "I_VICTOR",
            "event_id": "E_BIRTH_JOSEPH",
            "semantic": EventSemantic.BIRTH,
            "role": EventRoleSemantic.WITNESS,
            "date": self.usable_date,
            "principal_owner_type": TemporalOwnerType.PERSON,
            "principal_owner_id": "I_JOSEPH",
        }

        values.update(changes)
        return TemporalEvidence(**values)

    def test_valid_person_evidence(self) -> None:
        evidence = self.make_person_evidence()

        self.assertEqual(evidence.owner_type, EvidenceOwnerType.PERSON)
        self.assertEqual(evidence.owner_id, "I_VICTOR")
        self.assertEqual(evidence.event_id, "E_BIRTH_JOSEPH")
        self.assertEqual(evidence.semantic, EventSemantic.BIRTH)
        self.assertEqual(evidence.role, EventRoleSemantic.WITNESS)
        self.assertEqual(evidence.date, self.usable_date)
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.PERSON,
        )
        self.assertEqual(evidence.principal_owner_id, "I_JOSEPH")

    def test_owner_and_principal_owner_may_be_different(self) -> None:
        evidence = self.make_person_evidence()

        self.assertNotEqual(
            evidence.owner_id,
            evidence.principal_owner_id,
        )

    def test_evidence_is_immutable(self) -> None:
        evidence = self.make_person_evidence()

        with self.assertRaises(FrozenInstanceError):
            evidence.owner_id = "I_OTHER"

    def test_owner_type_must_be_evidence_owner_type(self) -> None:
        with self.assertRaises(TypeError):
            self.make_person_evidence(owner_type="PERSON")

    def test_owner_id_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(owner_id="")

    def test_owner_id_must_not_be_blank(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(owner_id="   ")

    def test_event_id_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(event_id="")

    def test_semantic_must_be_event_semantic(self) -> None:
        with self.assertRaises(TypeError):
            self.make_person_evidence(semantic="BIRTH")

    def test_unknown_semantic_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(
                semantic=EventSemantic.UNKNOWN,
            )

    def test_role_must_be_known_role_type(self) -> None:
        with self.assertRaises(TypeError):
            self.make_person_evidence(role="WITNESS")

    def test_unknown_person_role_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(
                role=EventRoleSemantic.UNKNOWN,
            )

    def test_unknown_family_role_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(
                role=FamilyRoleSemantic.UNKNOWN,
            )

    def test_date_must_be_temporal_value(self) -> None:
        with self.assertRaises(TypeError):
            self.make_person_evidence(date=self.event_date)

    def test_unavailable_date_is_rejected(self) -> None:
        unavailable_date = TemporalValue.unknown()

        with self.assertRaises(ValueError):
            self.make_person_evidence(date=unavailable_date)

    def test_unproven_date_is_rejected(self) -> None:
        unproven_date = TemporalValue(
            source_value="12/01/1790",
            source_calendar="GREGORIAN",
            normalized_minimum=self.event_date,
            normalized_maximum=self.event_date,
            representative_value=self.event_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.CALCULATED,
            evidence_status=EvidenceStatus.EVIDENCE_UNPROVEN,
            certainty=CertaintyLevel.UNDETERMINED,
        )

        with self.assertRaises(ValueError):
            self.make_person_evidence(date=unproven_date)

    def test_principal_owner_type_must_be_temporal_owner_type(self) -> None:
        with self.assertRaises(TypeError):
            self.make_person_evidence(
                principal_owner_type="PERSON",
            )

    def test_principal_owner_id_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.make_person_evidence(
                principal_owner_id="",
            )

    def test_valid_family_evidence(self) -> None:
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F0020",
            event_id="E_MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.usable_date,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F0020",
        )

        self.assertEqual(evidence.owner_type, EvidenceOwnerType.FAMILY)
        self.assertEqual(evidence.role, FamilyRoleSemantic.FAMILY)
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.FAMILY,
        )


if __name__ == "__main__":
    unittest.main()