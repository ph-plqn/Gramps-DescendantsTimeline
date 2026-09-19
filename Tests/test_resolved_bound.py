import unittest
from datetime import date

from descendants_timeline.inference.resolved_bound import ResolvedBound
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
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)
from dataclasses import FrozenInstanceError

class ResolvedBoundTests(unittest.TestCase):

    def test_accepts_valid_resolved_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1840, 1, 1),
            normalized_maximum=date(1840, 1, 1),
            representative_value=date(1840, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_RULE",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        resolved_bound = ResolvedBound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(constraint,),
        )

        self.assertEqual(
            resolved_bound.target,
            target,
        )
        self.assertEqual(
            resolved_bound.value,
            date(1840, 1, 1),
        )
        self.assertIs(
            resolved_bound.operator,
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertIs(
            resolved_bound.strength,
            ConstraintStrength.HARD,
        )
        self.assertEqual(
            resolved_bound.constraints,
            (constraint,),
        )
    def test_rejects_empty_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(ValueError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(),
            )
    def test_rejects_constraint_with_different_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1830",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1830, 1, 1),
            normalized_maximum=date(1830, 1, 1),
            representative_value=date(1830, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1830, 1, 1),
            rule_id="TEST_RULE",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        with self.assertRaises(ValueError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(constraint,),
            )
    def test_rejects_constraint_with_different_target(self):
        resolved_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1840, 1, 1),
            normalized_maximum=date(1840, 1, 1),
            representative_value=date(1840, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint = TemporalConstraint(
            target=constraint_target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_RULE",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        with self.assertRaises(ValueError):
            ResolvedBound(
                target=resolved_target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(constraint,),
            )
    def test_rejects_constraint_with_different_operator(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1840, 1, 1),
            normalized_maximum=date(1840, 1, 1),
            representative_value=date(1840, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_RULE",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        with self.assertRaises(ValueError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(constraint,),
            )
    def test_rejects_constraint_with_different_strength(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1840, 1, 1),
            normalized_maximum=date(1840, 1, 1),
            representative_value=date(1840, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_SOFT_RULE",
            strength=ConstraintStrength.SOFT,
            evidences=(evidence,),
        )

        with self.assertRaises(ValueError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(constraint,),
            )

    def test_accepts_multiple_constraints_for_same_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1840, 1, 1),
            normalized_maximum=date(1840, 1, 1),
            representative_value=date(1840, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint_a = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_RULE_A",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        constraint_b = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_RULE_B",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        resolved_bound = ResolvedBound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(
                constraint_a,
                constraint_b,
            ),
        )

        self.assertEqual(
            resolved_bound.constraints,
            (
                constraint_a,
                constraint_b,
            ),
        )
    def test_is_immutable(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        evidence_date = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1840, 1, 1),
            normalized_maximum=date(1840, 1, 1),
            representative_value=date(1840, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1840, 1, 1),
            rule_id="TEST_RULE",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        resolved_bound = ResolvedBound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(constraint,),
        )

        with self.assertRaises(FrozenInstanceError):
            resolved_bound.value = date(1850, 1, 1)
    def test_rejects_non_tuple_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=[],
            )
    def test_rejects_invalid_constraint_item(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=("not a constraint",),
            )
    def test_rejects_invalid_target(self):
        with self.assertRaises(TypeError):
            ResolvedBound(
                target="not a target",
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(),
            )
    def test_rejects_invalid_value(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ResolvedBound(
                target=target,
                value="1840-01-01",
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength=ConstraintStrength.HARD,
                constraints=(),
            )
    def test_rejects_invalid_operator(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator="AFTER_OR_EQUAL",
                strength=ConstraintStrength.HARD,
                constraints=(),
            )
    def test_rejects_invalid_strenght(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ResolvedBound(
                target=target,
                value=date(1840, 1, 1),
                operator=ConstraintOperator.AFTER_OR_EQUAL,
                strength="SOFT",
                constraints=(),
            )