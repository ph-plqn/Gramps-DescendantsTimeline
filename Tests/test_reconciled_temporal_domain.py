import unittest
from datetime import date

from descendants_timeline.inference.resolved_bound import ResolvedBound

from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBound,
    ReconciledBoundOrigin,
)

from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)
from descendants_timeline.inference.constraint_resolution import (
    ConstraintStrength,
)

from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
)

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

from descendants_timeline.model.event import EventSemantic

from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
)

from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
    TemporalConstraint,
)

from descendants_timeline.inference.constraint_resolution import (
    ConstraintResolution,
)

from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBound,
    ReconciledBoundOrigin,
    ReconciledTemporalDomain,
    ReconciliationConflictType,
)

class ReconciledBoundTestCase(unittest.TestCase):

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

    def test_gramps_bound_is_valid_without_inferred_bound(self):
        bound = ReconciledBound(
            value=date(1850, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(bound.value, date(1850, 1, 1))
        self.assertEqual(
            bound.origin,
            ReconciledBoundOrigin.GRAMPS,
        )
        self.assertIsNone(bound.inferred_bound)

    

    def test_inference_bound_keeps_resolved_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        resolved_bound = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        bound = ReconciledBound(
            value=date(1820, 1, 1),
            origin=ReconciledBoundOrigin.INFERENCE,
            inferred_bound=resolved_bound,
        )

        self.assertEqual(bound.value, date(1820, 1, 1))
        self.assertEqual(
            bound.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(bound.inferred_bound, resolved_bound)

    def test_gramps_bound_rejects_inferred_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        resolved_bound = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        with self.assertRaises(ValueError):
            ReconciledBound(
                value=date(1820, 1, 1),
                origin=ReconciledBoundOrigin.GRAMPS,
                inferred_bound=resolved_bound,
            )


    def test_inference_bound_requires_resolved_bound(self):
        with self.assertRaises(ValueError):
            ReconciledBound(
                value=date(1820, 1, 1),
                origin=ReconciledBoundOrigin.INFERENCE,
            )


    def test_inference_bound_value_must_match_resolved_bound(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        resolved_bound = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        with self.assertRaises(ValueError):
            ReconciledBound(
                value=date(1821, 1, 1),
                origin=ReconciledBoundOrigin.INFERENCE,
                inferred_bound=resolved_bound,
            )
    def test_empty_reconciled_domain_is_valid(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )

        self.assertEqual(result.target, target)
        self.assertIs(result.gramps_value, gramps_value)
        self.assertIs(
            result.constraint_resolution,
            constraint_resolution,
        )
        self.assertIsNone(result.principal_minimum)
        self.assertIsNone(result.principal_maximum)
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())
    def test_gramps_only_domain_is_valid(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="entre 1815 et 1825",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1815, 1, 1),
            normalized_maximum=date(1825, 1, 1),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_minimum = ReconciledBound(
            value=date(1815, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        principal_maximum = ReconciledBound(
            value=date(1825, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=principal_minimum,
            principal_maximum=principal_maximum,
            conflict_type=None,
            conflicting_bounds=(),
        )

        self.assertIs(result.principal_minimum, principal_minimum)
        self.assertIs(result.principal_maximum, principal_maximum)

        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_inference_only_domain_is_valid(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=inferred_maximum,
            refined_minimum=inferred_minimum,
            refined_maximum=inferred_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_minimum = ReconciledBound(
            value=date(1817, 1, 1),
            origin=ReconciledBoundOrigin.INFERENCE,
            inferred_bound=inferred_minimum,
        )

        principal_maximum = ReconciledBound(
            value=date(1825, 1, 1),
            origin=ReconciledBoundOrigin.INFERENCE,
            inferred_bound=inferred_maximum,
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=principal_minimum,
            principal_maximum=principal_maximum,
            conflict_type=None,
            conflicting_bounds=(),
        )

        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )

        self.assertIs(
            result.principal_minimum.inferred_bound,
            inferred_minimum,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            inferred_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_hybrid_domain_gramps_minimum_inference_maximum_is_valid(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="après 1815",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1815, 1, 1),
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=inferred_maximum,
            refined_minimum=None,
            refined_maximum=inferred_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_minimum = ReconciledBound(
            value=date(1815, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        principal_maximum = ReconciledBound(
            value=date(1825, 1, 1),
            origin=ReconciledBoundOrigin.INFERENCE,
            inferred_bound=inferred_maximum,
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=principal_minimum,
            principal_maximum=principal_maximum,
            conflict_type=None,
            conflicting_bounds=(),
        )

        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )
        self.assertEqual(
            result.principal_minimum.value,
            date(1815, 1, 1),
        )

        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            inferred_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_hybrid_domain_inference_minimum_gramps_maximum_is_valid(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="avant 1825",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=date(1825, 1, 1),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=None,
            refined_minimum=inferred_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_minimum = ReconciledBound(
            value=date(1817, 1, 1),
            origin=ReconciledBoundOrigin.INFERENCE,
            inferred_bound=inferred_minimum,
        )

        principal_maximum = ReconciledBound(
            value=date(1825, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=principal_minimum,
            principal_maximum=principal_maximum,
            conflict_type=None,
            conflicting_bounds=(),
        )

        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            inferred_minimum,
        )

        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )
        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_gramps_minimum_kept_when_inferred_maximum_conflicts(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="après 1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=inferred_maximum,
            refined_minimum=None,
            refined_maximum=inferred_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_minimum = ReconciledBound(
            value=date(1850, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=principal_minimum,
            principal_maximum=None,
            conflict_type=(
                ReconciliationConflictType.GRAMPS_INFERENCE
            ),
            conflicting_bounds=(inferred_maximum,),
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        # La borne inférée incompatible n'entre pas
        # dans le domaine principal.
        self.assertIsNone(result.principal_maximum)

        # Mais elle est conservée pour le diagnostic.
        self.assertEqual(
            result.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertEqual(
            result.conflicting_bounds,
            (inferred_maximum,),
        )

    def test_gramps_maximum_kept_when_inferred_minimum_conflicts(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="avant 1850",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=date(1850, 1, 1),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1860, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=None,
            refined_minimum=inferred_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_maximum = ReconciledBound(
            value=date(1850, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        result = ReconciledTemporalDomain(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=principal_maximum,
            conflict_type=(
                ReconciliationConflictType.GRAMPS_INFERENCE
            ),
            conflicting_bounds=(inferred_minimum,),
        )

        # La borne Gramps reste souveraine.
        self.assertEqual(
            result.principal_maximum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        # La borne inférée incompatible n'entre pas
        # dans le domaine principal.
        self.assertIsNone(result.principal_minimum)

        # Mais elle reste disponible pour le diagnostic.
        self.assertEqual(
            result.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertEqual(
            result.conflicting_bounds,
            (inferred_minimum,),
        )

    def test_rejects_constraint_resolution_for_another_target(self):
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

        constraint_resolution = ConstraintResolution(
            target=other_target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(ValueError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )


    def test_rejects_inverted_principal_domain(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        principal_minimum = ReconciledBound(
            value=date(1860, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        principal_maximum = ReconciledBound(
            value=date(1850, 1, 1),
            origin=ReconciledBoundOrigin.GRAMPS,
        )

        with self.assertRaises(ValueError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=principal_minimum,
                principal_maximum=principal_maximum,
                conflict_type=None,
                conflicting_bounds=(),
            )


    def test_rejects_conflicting_bounds_without_conflict_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        inferred_bound = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=inferred_bound,
            refined_minimum=None,
            refined_maximum=inferred_bound,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(ValueError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(inferred_bound,),
            )


    def test_rejects_conflict_type_without_conflicting_bounds(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(ValueError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=(
                    ReconciliationConflictType.GRAMPS_INFERENCE
                ),
                conflicting_bounds=(),
            )

    def test_rejects_invalid_target_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(TypeError):
            ReconciledTemporalDomain(
                target="I0001",
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )


    def test_rejects_invalid_gramps_value_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(TypeError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value="unknown",
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )


    def test_rejects_invalid_constraint_resolution_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution="invalid",
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )


    def test_rejects_invalid_principal_bound_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(TypeError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=date(1815, 1, 1),
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )


    def test_rejects_invalid_conflicting_bounds_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(TypeError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=[],
            )

    def test_rejects_invalid_item_in_conflicting_bounds(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        with self.assertRaises(TypeError):
            ReconciledTemporalDomain(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=(
                    ReconciliationConflictType.GRAMPS_INFERENCE
                ),
                conflicting_bounds=("invalid",),
            )

if __name__ == "__main__":
    unittest.main()
