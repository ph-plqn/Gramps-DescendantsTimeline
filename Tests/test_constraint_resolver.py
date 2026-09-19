import unittest

from descendants_timeline.inference.constraint_resolver import (
    ConstraintResolver,
)
from descendants_timeline.inference.constraint_resolution import (
    ConstraintConflictType,
    ConstraintResolution,
)
from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)
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
from dataclasses import FrozenInstanceError

class ConstraintResolverTestCase(unittest.TestCase):

    def make_resolved_bound(
            self,
            target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ):
            evidence_date = TemporalValue(
                source_value=value.strftime("%d/%m/%Y"),
                source_calendar="GREGORIAN",
                normalized_minimum=value,
                normalized_maximum=value,
                representative_value=value,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            )

            evidence = TemporalEvidence(
                owner_type=EvidenceOwnerType.PERSON,
                owner_id=target.owner_id,
                event_id="E_TEST",
                semantic=EventSemantic.BIRTH,
                role=EventRoleSemantic.PRINCIPAL,
                date=evidence_date,
                principal_owner_type=TemporalOwnerType.PERSON,
                principal_owner_id=target.owner_id,
            )

            constraint = TemporalConstraint(
                target=target,
                operator=operator,
                bound=value,
                rule_id="TEST_RULE",
                strength=strength,
                evidences=(evidence,),
            )

            return ResolvedBound(
                target=target,
                value=value,
                operator=operator,
                strength=strength,
                constraints=(constraint,),
            )
    def test_empty_constraints_returns_empty_resolution(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(),
        )

        self.assertEqual(result.target, target)

        self.assertIsNone(result.hard_minimum)
        self.assertIsNone(result.hard_maximum)

        self.assertIsNone(result.refined_minimum)
        self.assertIsNone(result.refined_maximum)

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_invalid_target_raises_type_error(self):
        resolver = ConstraintResolver()

        with self.assertRaises(TypeError):
            resolver.resolve(
                target="I0001",
                constraints=(),
            )
    def test_constraints_must_be_tuple(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        resolver = ConstraintResolver()

        with self.assertRaises(TypeError):
            resolver.resolve(
                target=target,
                constraints=[],
            )
    def test_constraints_must_contain_only_temporal_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        resolver = ConstraintResolver()

        with self.assertRaises(TypeError):
            resolver.resolve(
                target=target,
                constraints=("not a constraint",),
            )
    def test_constraint_with_different_target_raises_value_error(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        other_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0002",
            semantic=TargetSemantic.BIRTH,
        )

        resolved_bound = self.make_resolved_bound(
            target=other_target,
        )

        constraint = resolved_bound.constraints[0]

        resolver = ConstraintResolver()

        with self.assertRaises(ValueError):
            resolver.resolve(
                target=target,
                constraints=(constraint,),
            )
    def test_single_hard_minimum_constraint_is_resolved(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        source_bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint = source_bound.constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(constraint,),
        )

        self.assertIsNotNone(result.hard_minimum)
        self.assertEqual(
            result.hard_minimum.value,
            date(1840, 1, 1),
        )
        self.assertEqual(
            result.hard_minimum.operator,
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertEqual(
            result.hard_minimum.strength,
            ConstraintStrength.HARD,
        )
        self.assertEqual(
            result.hard_minimum.constraints,
            (constraint,),
        )

        self.assertIsNone(result.hard_maximum)
    def test_hard_minimum_uses_maximum_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_1812 = self.make_resolved_bound(
            target=target,
            value=date(1812, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        constraint_1817 = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                constraint_1812,
                constraint_1817,
            ),
        )

        self.assertIsNotNone(result.hard_minimum)
        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_minimum.constraints,
            (constraint_1817,),
        )
    def test_hard_minimum_keeps_all_constraints_at_winning_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_a = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        constraint_1812 = self.make_resolved_bound(
            target=target,
            value=date(1812, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        constraint_b = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                constraint_a,
                constraint_1812,
                constraint_b,
            ),
        )

        self.assertIsNotNone(result.hard_minimum)
        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_minimum.constraints,
            (constraint_a, constraint_b),
        )
    def test_single_hard_maximum_constraint_is_resolved(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint = self.make_resolved_bound(
            target=target,
            value=date(1870, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(constraint,),
        )

        self.assertIsNone(result.hard_minimum)

        self.assertIsNotNone(result.hard_maximum)
        self.assertEqual(
            result.hard_maximum.value,
            date(1870, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(
            result.hard_maximum.strength,
            ConstraintStrength.HARD,
        )
        self.assertEqual(
            result.hard_maximum.constraints,
            (constraint,),
        )
    def test_hard_maximum_uses_minimum_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_1870 = self.make_resolved_bound(
            target=target,
            value=date(1870, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        constraint_1860 = self.make_resolved_bound(
            target=target,
            value=date(1860, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                constraint_1870,
                constraint_1860,
            ),
        )

        self.assertIsNotNone(result.hard_maximum)
        self.assertEqual(
            result.hard_maximum.value,
            date(1860, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.constraints,
            (constraint_1860,),
        )
    def test_hard_maximum_keeps_all_constraints_at_winning_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_a = self.make_resolved_bound(
            target=target,
            value=date(1860, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        constraint_1870 = self.make_resolved_bound(
            target=target,
            value=date(1870, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        constraint_b = self.make_resolved_bound(
            target=target,
            value=date(1860, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                constraint_a,
                constraint_1870,
                constraint_b,
            ),
        )

        self.assertIsNotNone(result.hard_maximum)
        self.assertEqual(
            result.hard_maximum.value,
            date(1860, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.constraints,
            (constraint_a, constraint_b),
        )
    def test_coherent_hard_domain_becomes_refined_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(
            result.conflicting_constraints,
            (),
        )
    def test_contradictory_hard_bounds_create_hard_hard_conflict(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1817, 1, 1),
        )

        self.assertIsNone(result.refined_minimum)
        self.assertIsNone(result.refined_maximum)

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.HARD_HARD,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                minimum_constraint,
                maximum_constraint,
            ),
        )
    def test_equal_hard_bounds_are_not_a_conflict(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1820, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(
            result.conflicting_constraints,
            (),
        )
    def test_hard_hard_conflict_keeps_only_winning_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        minimum_1800 = self.make_resolved_bound(
            target=target,
            value=date(1800, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        minimum_1825 = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        maximum_1817 = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        maximum_1850 = self.make_resolved_bound(
            target=target,
            value=date(1850, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                minimum_1800,
                minimum_1825,
                maximum_1817,
                maximum_1850,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1817, 1, 1),
        )

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.HARD_HARD,
        )

        self.assertEqual(
            result.conflicting_constraints,
            (
                minimum_1825,
                maximum_1817,
            ),
        )
    def test_single_soft_minimum_creates_refined_minimum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint = self.make_resolved_bound(
            target=target,
            value=date(1854, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(constraint,),
        )

        self.assertIsNone(result.hard_minimum)
        self.assertIsNone(result.hard_maximum)

        self.assertIsNotNone(result.refined_minimum)
        self.assertEqual(
            result.refined_minimum.value,
            date(1854, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.operator,
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_minimum.constraints,
            (constraint,),
        )

        self.assertIsNone(result.refined_maximum)
        self.assertIsNone(result.conflict_type)
        self.assertEqual(
            result.conflicting_constraints,
            (),
        )
    def test_single_soft_maximum_creates_refined_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint = self.make_resolved_bound(
            target=target,
            value=date(1862, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(constraint,),
        )

        self.assertIsNone(result.hard_minimum)
        self.assertIsNone(result.hard_maximum)

        self.assertIsNone(result.refined_minimum)

        self.assertIsNotNone(result.refined_maximum)
        self.assertEqual(
            result.refined_maximum.value,
            date(1862, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_maximum.constraints,
            (constraint,),
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(
            result.conflicting_constraints,
            (),
        )
    def test_soft_constraints_create_coherent_refined_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1854, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1862, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertIsNone(result.hard_minimum)
        self.assertIsNone(result.hard_maximum)

        self.assertEqual(
            result.refined_minimum.value,
            date(1854, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.value,
            date(1862, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(
            result.conflicting_constraints,
            (),
        )
    def test_contradictory_soft_bounds_create_soft_soft_conflict(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1865, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1862, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertIsNone(result.hard_minimum)
        self.assertIsNone(result.hard_maximum)

        self.assertIsNone(result.refined_minimum)
        self.assertIsNone(result.refined_maximum)

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.SOFT_SOFT,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                minimum_constraint,
                maximum_constraint,
            ),
        )
    def test_soft_maximum_conflicting_with_hard_minimum_creates_hard_soft_conflict(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1816, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                soft_maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertIsNone(result.hard_maximum)

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertIsNone(result.refined_maximum)

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                hard_minimum_constraint,
                soft_maximum_constraint,
            ),
        )
    def test_soft_minimum_conflicting_with_hard_maximum_creates_hard_soft_conflict(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1826, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_maximum_constraint,
                soft_minimum_constraint,
            ),
        )

        self.assertIsNone(result.hard_minimum)
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertIsNone(result.refined_minimum)
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                hard_maximum_constraint,
                soft_minimum_constraint,
            ),
        )
    def test_soft_maximum_can_refine_hard_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )

        self.assertEqual(
            result.refined_maximum.value,
            date(1822, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_minimum_can_refine_hard_minimum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_minimum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_minimum_does_not_widen_hard_minimum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1810, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_minimum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_minimum_equal_to_hard_minimum_keeps_hard_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 12, 5),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 12, 5),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_minimum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 12, 5),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_maximum_does_not_widen_hard_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_maximum_equal_to_hard_maximum_keeps_hard_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 12, 5),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 12, 5),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 12, 5),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.HARD,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_mutually_conflicting_soft_bounds_fall_back_to_hard_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1823, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_maximum_constraint,
                soft_minimum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.SOFT_SOFT,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                soft_minimum_constraint,
                soft_maximum_constraint,
            ),
        )
    def test_conflicting_soft_constraint_does_not_discard_compatible_soft_refinement(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        compatible_soft_constraint = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        conflicting_soft_constraint = self.make_resolved_bound(
            target=target,
            value=date(1816, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                compatible_soft_constraint,
                conflicting_soft_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )
        self.assertEqual(
            result.refined_maximum.value,
            date(1822, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                hard_minimum_constraint,
                conflicting_soft_constraint,
            ),
        )
    def test_conflicting_soft_constraint_does_not_discard_compatible_soft_minimum_refinement(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        compatible_soft_constraint = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        conflicting_soft_constraint = self.make_resolved_bound(
            target=target,
            value=date(1826, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                compatible_soft_constraint,
                conflicting_soft_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertEqual(
            result.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertEqual(
            result.conflicting_constraints,
            (
                hard_maximum_constraint,
                conflicting_soft_constraint,
            ),
        )
    def test_compatible_soft_bounds_refine_both_sides_of_hard_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_minimum_constraint,
                soft_maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertEqual(
            result.refined_maximum.value,
            date(1822, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_multiple_compatible_soft_minimums_use_most_restrictive_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_1819 = self.make_resolved_bound(
            target=target,
            value=date(1819, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_minimum_1820 = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_minimum_1818 = self.make_resolved_bound(
            target=target,
            value=date(1818, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_minimum_1819,
                soft_minimum_1820,
                soft_minimum_1818,
            ),
        )

        self.assertEqual(
            result.refined_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_minimum.constraints,
            (soft_minimum_1820,),
        )

        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_tied_soft_minimums_keep_all_winning_constraints_in_order(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_minimum_1819 = self.make_resolved_bound(
            target=target,
            value=date(1819, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_minimum_1820_first = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_minimum_1820_second = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_minimum_1818 = self.make_resolved_bound(
            target=target,
            value=date(1818, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_minimum_1819,
                soft_minimum_1820_first,
                soft_minimum_1820_second,
                soft_minimum_1818,
            ),
        )

        self.assertEqual(
            result.refined_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_minimum.constraints,
            (
                soft_minimum_1820_first,
                soft_minimum_1820_second,
            ),
        )

        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_tied_soft_maximums_keep_all_winning_constraints_in_order(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_1824 = self.make_resolved_bound(
            target=target,
            value=date(1824, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_maximum_1822_first = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_maximum_1822_second = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        soft_maximum_1823 = self.make_resolved_bound(
            target=target,
            value=date(1823, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                hard_maximum_constraint,
                soft_maximum_1824,
                soft_maximum_1822_first,
                soft_maximum_1822_second,
                soft_maximum_1823,
            ),
        )

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )

        self.assertEqual(
            result.refined_maximum.value,
            date(1822, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_maximum.constraints,
            (
                soft_maximum_1822_first,
                soft_maximum_1822_second,
            ),
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_maximum_can_complete_partial_hard_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        soft_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                hard_minimum_constraint,
                soft_maximum_constraint,
            ),
        )

        self.assertEqual(
            result.hard_minimum.value,
            date(1817, 1, 1),
        )
        self.assertIsNone(result.hard_maximum)

        self.assertEqual(
            result.refined_minimum,
            result.hard_minimum,
        )

        self.assertEqual(
            result.refined_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_maximum.constraints,
            (soft_maximum_constraint,),
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())
    def test_soft_minimum_can_complete_partial_hard_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        soft_minimum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        ).constraints[0]

        hard_maximum_constraint = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        ).constraints[0]

        resolver = ConstraintResolver()

        result = resolver.resolve(
            target=target,
            constraints=(
                soft_minimum_constraint,
                hard_maximum_constraint,
            ),
        )

        self.assertIsNone(result.hard_minimum)
        self.assertEqual(
            result.hard_maximum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            result.refined_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            result.refined_minimum.constraints,
            (soft_minimum_constraint,),
        )

        self.assertEqual(
            result.refined_maximum,
            result.hard_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_constraints, ())