"""Tests unitaires de TemporalConstraint et de ses objets associés."""

from dataclasses import FrozenInstanceError
from datetime import date
import unittest

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
    TemporalConstraint,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)


class TestTemporalConstraint(unittest.TestCase):
    """Tests du modèle de contrainte temporelle."""

    def setUp(self) -> None:
        """Construit une preuve réutilisable dans les tests.

        Victor est témoin de la naissance de Joseph le 12/01/1790.
        """

        self.event_date = date(1790, 1, 12)

        self.temporal_value = TemporalValue(
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

        self.evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I_VICTOR",
            event_id="E_BIRTH_JOSEPH",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.WITNESS,
            date=self.temporal_value,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I_JOSEPH",
        )

        self.target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I_VICTOR",
            semantic=TargetSemantic.BIRTH,
        )

    def make_constraint(self, **changes) -> TemporalConstraint:
        """Construit une contrainte valide, avec substitutions éventuelles."""

        values = {
            "target": self.target,
            "operator": ConstraintOperator.BEFORE_OR_EQUAL,
            "bound": self.event_date,
            "rule_id": "EXISTENCE_BEFORE_EVENT",
            "strength": ConstraintStrength.HARD,
            "evidences": (self.evidence,),
        }

        values.update(changes)
        return TemporalConstraint(**values)

    def test_valid_constraint(self) -> None:
        constraint = self.make_constraint()

        self.assertEqual(constraint.target, self.target)
        self.assertEqual(
            constraint.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(constraint.bound, date(1790, 1, 12))
        self.assertEqual(constraint.rule_id, "EXISTENCE_BEFORE_EVENT")
        self.assertEqual(constraint.strength, ConstraintStrength.HARD)
        self.assertEqual(constraint.evidences, (self.evidence,))

    def test_constraint_is_immutable(self) -> None:
        constraint = self.make_constraint()

        with self.assertRaises(FrozenInstanceError):
            constraint.bound = date(1800, 1, 1)

    def test_target_must_be_temporal_target(self) -> None:
        with self.assertRaises(TypeError):
            self.make_constraint(target="I_VICTOR")

    def test_operator_must_be_constraint_operator(self) -> None:
        with self.assertRaises(TypeError):
            self.make_constraint(operator="BEFORE_OR_EQUAL")

    def test_bound_must_be_date(self) -> None:
        with self.assertRaises(TypeError):
            self.make_constraint(bound="12/01/1790")

    def test_rule_id_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.make_constraint(rule_id="")

    def test_rule_id_must_not_be_blank(self) -> None:
        with self.assertRaises(ValueError):
            self.make_constraint(rule_id="   ")

    def test_strength_must_be_constraint_strength(self) -> None:
        with self.assertRaises(TypeError):
            self.make_constraint(strength="HARD")

    def test_evidences_must_be_tuple(self) -> None:
        with self.assertRaises(TypeError):
            self.make_constraint(evidences=[self.evidence])

    def test_evidences_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            self.make_constraint(evidences=())

    def test_evidences_must_contain_only_temporal_evidence(self) -> None:
        with self.assertRaises(TypeError):
            self.make_constraint(evidences=(self.evidence, "invalid"))


if __name__ == "__main__":
    unittest.main()