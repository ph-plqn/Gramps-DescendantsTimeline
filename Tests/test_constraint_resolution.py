import unittest

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

class ConstraintResolutionTests(unittest.TestCase):
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

    def test_accepts_empty_coherent_resolution(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        self.assertEqual(resolution.target, target)
        self.assertIsNone(resolution.hard_minimum)
        self.assertIsNone(resolution.hard_maximum)
        self.assertIsNone(resolution.refined_minimum)
        self.assertIsNone(resolution.refined_maximum)
        self.assertIsNone(resolution.conflict_type)
        self.assertEqual(
            resolution.conflicting_constraints,
            (),
        )
    def test_rejects_invalid_target(self):
        with self.assertRaises(TypeError):
            ConstraintResolution(
                target="not a target",
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_rejects_bound_with_different_target(self):
        resolution_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I002",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=bound_target,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=resolution_target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_rejects_soft_hard_minimum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            strength=ConstraintStrength.SOFT,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_rejects_hard_minimum_with_wrong_operator(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_rejects_hard_maximum_with_wrong_operator(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=bound,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_rejects_soft_hard_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=bound,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_rejects_refined_minimum_with_wrong_operator(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=bound,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_accepts_hard_refined_minimum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=bound,
            hard_maximum=None,
            refined_minimum=bound,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        self.assertIs(
            resolution.refined_minimum,
            bound,
        )
    def test_accepts_soft_refined_minimum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        refined_minimum = self.make_resolved_bound(
            target=target,
            value=date(1850, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=refined_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        self.assertIs(
            resolution.refined_minimum,
            refined_minimum,
        )
    def test_rejects_refined_maximum_with_wrong_operator(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=bound,
                conflict_type=None,
                conflicting_constraints=(),
            )
    def test_accepts_hard_refined_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            value=date(1870, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=bound,
            refined_minimum=None,
            refined_maximum=bound,
            conflict_type=None,
            conflicting_constraints=(),
        )

        self.assertIs(
            resolution.refined_maximum,
            bound,
        )
    def test_accepts_soft_refined_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_maximum = self.make_resolved_bound(
            target=target,
            value=date(1870, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        refined_maximum = self.make_resolved_bound(
            target=target,
            value=date(1860, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=hard_maximum,
            refined_minimum=None,
            refined_maximum=refined_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )

        self.assertIs(
            resolution.refined_maximum,
            refined_maximum,
        )
    def test_rejects_conflicting_constraints_without_conflict_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint = bound.constraints[0]

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=bound,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(constraint,),
            )
    def test_rejects_conflict_type_without_conflicting_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_HARD,
                conflicting_constraints=(),
            )
    def test_rejects_invalid_conflict_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint = bound.constraints[0]

        with self.assertRaises(TypeError):
            ConstraintResolution(
                target=target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=bound,
                refined_maximum=None,
                conflict_type="HARD_HARD",
                conflicting_constraints=(constraint,),
            )
    def test_rejects_non_tuple_conflicting_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint = bound.constraints[0]

        with self.assertRaises(TypeError):
            ConstraintResolution(
                target=target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=bound,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_HARD,
                conflicting_constraints=[constraint],
            )
    def test_rejects_invalid_item_in_conflicting_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_HARD,
                conflicting_constraints=("not a constraint",),
            )
    def test_rejects_conflicting_constraint_with_different_target(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        other_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I002",
            semantic=TargetSemantic.BIRTH,
        )

        other_bound = self.make_resolved_bound(
            target=other_target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        conflicting_constraint = other_bound.constraints[0]

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_HARD,
                conflicting_constraints=(conflicting_constraint,),
            )
    def test_rejects_conflict_with_only_one_constraint(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint = bound.constraints[0]

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=bound,
                hard_maximum=None,
                refined_minimum=bound,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_HARD,
                conflicting_constraints=(constraint,),
            )
    def test_rejects_hard_hard_conflict_with_soft_constraint(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        soft_bound = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        hard_constraint = hard_bound.constraints[0]
        soft_constraint = soft_bound.constraints[0]

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=hard_bound,
                hard_maximum=None,
                refined_minimum=hard_bound,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_HARD,
                conflicting_constraints=(
                    hard_constraint,
                    soft_constraint,
                ),
            )
    def test_rejects_soft_soft_conflict_with_hard_constraint(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        soft_bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        hard_bound = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        soft_constraint = soft_bound.constraints[0]
        hard_constraint = hard_bound.constraints[0]

        with self.assertRaises(ValueError):
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=soft_bound,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.SOFT_SOFT,
                conflicting_constraints=(
                    soft_constraint,
                    hard_constraint,
                ),
            )
    def test_rejects_hard_soft_conflict_with_only_hard_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        hard_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        with self.assertRaises(ValueError) as context:
            ConstraintResolution(
                target=target,
                hard_minimum=hard_minimum,
                hard_maximum=hard_maximum,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=ConstraintConflictType.HARD_SOFT,
                conflicting_constraints=(
                    hard_minimum.constraints[0],
                    hard_maximum.constraints[0],
                ),
            )

    def test_rejects_hard_soft_conflict_with_only_soft_constraints(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        soft_minimum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        soft_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        with self.assertRaises(ValueError) as context:
            ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=soft_minimum,
                refined_maximum=soft_maximum,
                conflict_type=ConstraintConflictType.HARD_SOFT,
                conflicting_constraints=(
                    soft_minimum.constraints[0],
                    soft_maximum.constraints[0],
                ),
            )
    def test_accepts_hard_soft_conflict(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        soft_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        hard_constraint = hard_minimum.constraints[0]
        soft_constraint = soft_maximum.constraints[0]

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=(
                hard_constraint,
                soft_constraint,
            ),
        )

        self.assertIs(
            resolution.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )

        self.assertEqual(
            resolution.conflicting_constraints,
            (
                hard_constraint,
                soft_constraint,
            ),
        )
    def test_accepts_hard_hard_conflict(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        hard_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        minimum_constraint = hard_minimum.constraints[0]
        maximum_constraint = hard_maximum.constraints[0]

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=hard_maximum,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_HARD,
            conflicting_constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertIs(
            resolution.conflict_type,
            ConstraintConflictType.HARD_HARD,
        )

        self.assertEqual(
            resolution.conflicting_constraints,
            (
                minimum_constraint,
                maximum_constraint,
            ),
        )
    def test_accepts_soft_soft_conflict(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        soft_minimum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        soft_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        minimum_constraint = soft_minimum.constraints[0]
        maximum_constraint = soft_maximum.constraints[0]

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.SOFT_SOFT,
            conflicting_constraints=(
                minimum_constraint,
                maximum_constraint,
            ),
        )

        self.assertIs(
            resolution.conflict_type,
            ConstraintConflictType.SOFT_SOFT,
        )

        self.assertEqual(
            resolution.conflicting_constraints,
            (
                minimum_constraint,
                maximum_constraint,
            ),
        )
    def test_is_immutable(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(FrozenInstanceError):
            resolution.conflict_type = ConstraintConflictType.HARD_HARD
if __name__ == "__main__":
    unittest.main()