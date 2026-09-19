import unittest

from descendants_timeline.inference.constraint_resolution import (
    ConstraintConflictType,
    ConstraintResolution,
)
from descendants_timeline.inference.temporal_reconciler import (
    TemporalReconciler,
)
from descendants_timeline.model.temporal import TemporalValue
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from datetime import date

from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBoundOrigin,
)
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.inference.resolved_bound import (
    ResolvedBound,
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
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBoundOrigin,
    ReconciliationConflictType,
)

class TemporalReconcilerTestCase(unittest.TestCase):

    def make_resolved_bound(
        self,
        target,
        value,
        operator,
        strength,
    ):
        evidence_date = TemporalValue(
            source_value="01/01/1800",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1800, 1, 1),
            normalized_maximum=date(1800, 1, 1),
            representative_value=date(1800, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I0099",
            event_id="E0099",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I0099",
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

    def test_empty_gramps_and_empty_inference_produce_empty_domain(self):
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

        reconciler = TemporalReconciler()

        result = reconciler.reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
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

    def test_exact_gramps_date_produces_gramps_principal_bounds(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="15/06/1820",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1820, 6, 15),
            normalized_maximum=date(1820, 6, 15),
            representative_value=date(1820, 6, 15),
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

        reconciler = TemporalReconciler()

        result = reconciler.reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1820, 6, 15),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1820, 6, 15),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_gramps_minimum_only_produces_open_principal_domain(self):
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

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1815, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.principal_maximum)

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_gramps_maximum_only_produces_open_principal_domain(self):
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

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertIsNone(result.principal_minimum)

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_inferred_minimum_fills_missing_gramps_minimum(self):
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

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=None,
            refined_minimum=inferred_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            inferred_minimum,
        )

        self.assertIsNone(result.principal_maximum)

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_inferred_maximum_fills_missing_gramps_maximum(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertIsNone(result.principal_minimum)

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            inferred_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_inferred_maximum_completes_gramps_minimum(self):
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1815, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            inferred_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_inferred_minimum_completes_gramps_maximum(self):
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            inferred_minimum,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_conflicting_inferred_maximum_does_not_override_gramps_minimum(
        self,
    ):
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
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

        # Elle est cependant conservée pour le diagnostic.
        self.assertEqual(
            result.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertEqual(
            result.conflicting_bounds,
            (inferred_maximum,),
        )

    def test_conflicting_inferred_minimum_does_not_override_gramps_maximum(
        self,
    ):
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        # La borne Gramps reste souveraine.
        self.assertIsNone(result.principal_minimum)

        self.assertEqual(
            result.principal_maximum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        # La borne inférée incompatible reste disponible
        # uniquement pour le diagnostic.
        self.assertEqual(
            result.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertEqual(
            result.conflicting_bounds,
            (inferred_minimum,),
        )

    def test_equal_gramps_minimum_and_inferred_maximum_produce_point_domain(
        self,
    ):
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
            value=date(1850, 1, 1),
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            inferred_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_equal_inferred_minimum_and_gramps_maximum_produce_point_domain(
        self,
    ):
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
            value=date(1850, 1, 1),
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            inferred_minimum,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1850, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_two_inferred_bounds_produce_inference_principal_domain(
        self,
    ):
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            inferred_minimum,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            inferred_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

    def test_closed_gramps_domain_is_kept_despite_refined_inference(
        self,
    ):
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

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        # Le minimum Gramps reste souverain.
        self.assertEqual(
            result.principal_minimum.value,
            date(1815, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )
        self.assertIsNone(
            result.principal_minimum.inferred_bound
        )

        # Le maximum Gramps reste également souverain.
        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )
        self.assertIsNone(
            result.principal_maximum.inferred_bound
        )

        # L'inférence n'est pas considérée comme conflictuelle :
        # elle n'était pas éligible pour remplacer ces bornes.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # La résolution d'inférence reste néanmoins conservée
        # dans le résultat pour sa provenance complète.
        self.assertIs(
            result.constraint_resolution,
            constraint_resolution,
        )

    def test_closed_gramps_domain_ignores_incompatible_inference(
        self,
    ):
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

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1840, 1, 1),
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1815, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        # L'inférence n'était éligible pour aucune borne.
        # Il n'y a donc pas de conflit de réconciliation.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # La résolution inférée reste néanmoins disponible.
        self.assertIs(
            result.constraint_resolution,
            constraint_resolution,
        )

    def test_unproven_calculated_gramps_bounds_remain_sovereign(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue(
            source_value="1820",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1820, 1, 1),
            normalized_maximum=date(1820, 1, 1),
            representative_value=date(1820, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.CALCULATED,
            evidence_status=EvidenceStatus.EVIDENCE_UNPROVEN,
            certainty=CertaintyLevel.UNDETERMINED,
        )

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
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

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1820, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

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
            TemporalReconciler().reconcile(
                target="I0001",
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
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
            TemporalReconciler().reconcile(
                target=target,
                gramps_value="invalid",
                constraint_resolution=constraint_resolution,
            )


    def test_rejects_invalid_constraint_resolution_type(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaises(TypeError):
            TemporalReconciler().reconcile(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution="invalid",
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
            TemporalReconciler().reconcile(
                target=target,
                gramps_value=TemporalValue.unknown(),
                constraint_resolution=constraint_resolution,
            )

    def test_gramps_domain_is_kept_when_inference_has_hard_hard_conflict(
        self,
    ):
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

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        conflicting_constraints = (
            inferred_minimum.constraints
            + inferred_maximum.constraints
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=inferred_maximum,

            # HARD_HARD ne produit aucun domaine raffiné utilisable.
            refined_minimum=None,
            refined_maximum=None,

            conflict_type=ConstraintConflictType.HARD_HARD,
            conflicting_constraints=conflicting_constraints,
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        # Le domaine Gramps reste intégralement souverain.
        self.assertEqual(
            result.principal_minimum.value,
            date(1815, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        # Aucun conflit de RECONCILIATION :
        # HARD_HARD appartient au ConstraintResolver.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # Le diagnostic du Resolver n'est cependant pas perdu.
        self.assertIs(
            result.constraint_resolution,
            constraint_resolution,
        )
        self.assertEqual(
            result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_HARD,
        )

    def test_no_gramps_domain_and_hard_hard_conflict_produce_empty_domain(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=date(1830, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=date(1820, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        conflicting_constraints = (
            inferred_minimum.constraints
            + inferred_maximum.constraints
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=inferred_maximum,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_HARD,
            conflicting_constraints=conflicting_constraints,
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        # Aucune borne Gramps et aucun domaine inféré fiable :
        # le domaine principal reste vide.
        self.assertIsNone(result.principal_minimum)
        self.assertIsNone(result.principal_maximum)

        # HARD_HARD n'est pas un conflit de réconciliation.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # Le diagnostic d'inférence reste intégralement disponible.
        self.assertIs(
            result.constraint_resolution,
            constraint_resolution,
        )
        self.assertEqual(
            result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_HARD,
        )
        self.assertEqual(
            result.constraint_resolution.conflicting_constraints,
            conflicting_constraints,
        )

    def test_hard_soft_resolution_can_supply_valid_inferred_domain(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        soft_maximum = self.make_resolved_bound(
            target=target,
            value=date(1810, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        conflicting_constraints = (
            hard_minimum.constraints
            + soft_maximum.constraints
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,

            # Le SOFT incompatible a été écarté par le Resolver.
            refined_minimum=hard_minimum,
            refined_maximum=None,

            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=conflicting_constraints,
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        # La partie valide du domaine inféré reste utilisable.
        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            hard_minimum,
        )

        self.assertIsNone(result.principal_maximum)

        # HARD_SOFT n'est pas un conflit GRAMPS ↔ INFERENCE.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # Le diagnostic du Resolver reste disponible.
        self.assertEqual(
            result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertEqual(
            result.constraint_resolution.conflicting_constraints,
            conflicting_constraints,
        )

    def test_hard_soft_resolution_uses_refined_soft_bound(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        hard_maximum = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        refined_maximum = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        incompatible_soft = self.make_resolved_bound(
            target=target,
            value=date(1816, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        conflicting_constraints = (
            hard_minimum.constraints
            + incompatible_soft.constraints
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=hard_maximum,
            refined_minimum=hard_minimum,
            refined_maximum=refined_maximum,
            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=conflicting_constraints,
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            hard_minimum,
        )

        # Point essentiel :
        # 1822 raffiné est utilisé, et non le HARD 1825.
        self.assertEqual(
            result.principal_maximum.value,
            date(1822, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            refined_maximum,
        )

        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        self.assertEqual(
            result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )

    def test_soft_soft_conflict_uses_hard_fallback_domain(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        hard_minimum = self.make_resolved_bound(
            target=target,
            value=date(1817, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        hard_maximum = self.make_resolved_bound(
            target=target,
            value=date(1825, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        soft_maximum = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        soft_minimum = self.make_resolved_bound(
            target=target,
            value=date(1823, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        conflicting_constraints = (
            soft_maximum.constraints
            + soft_minimum.constraints
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=hard_maximum,

            # Les SOFT contradictoires sont abandonnés :
            # retour au domaine HARD.
            refined_minimum=hard_minimum,
            refined_maximum=hard_maximum,

            conflict_type=ConstraintConflictType.SOFT_SOFT,
            conflicting_constraints=conflicting_constraints,
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        self.assertEqual(
            result.principal_minimum.value,
            date(1817, 1, 1),
        )
        self.assertEqual(
            result.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_minimum.inferred_bound,
            hard_minimum,
        )

        self.assertEqual(
            result.principal_maximum.value,
            date(1825, 1, 1),
        )
        self.assertEqual(
            result.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )
        self.assertIs(
            result.principal_maximum.inferred_bound,
            hard_maximum,
        )

        # SOFT_SOFT appartient au Resolver,
        # pas à la réconciliation Gramps/inférence.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # Le diagnostic original reste disponible.
        self.assertEqual(
            result.constraint_resolution.conflict_type,
            ConstraintConflictType.SOFT_SOFT,
        )
        self.assertEqual(
            result.constraint_resolution.conflicting_constraints,
            conflicting_constraints,
        )

    def test_soft_soft_conflict_without_hard_domain_produces_empty_domain(
        self,
    ):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        gramps_value = TemporalValue.unknown()

        soft_maximum = self.make_resolved_bound(
            target=target,
            value=date(1822, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        soft_minimum = self.make_resolved_bound(
            target=target,
            value=date(1823, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.SOFT,
        )

        conflicting_constraints = (
            soft_maximum.constraints
            + soft_minimum.constraints
        )

        constraint_resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,

            # Aucun domaine HARD sur lequel revenir.
            refined_minimum=None,
            refined_maximum=None,

            conflict_type=ConstraintConflictType.SOFT_SOFT,
            conflicting_constraints=conflicting_constraints,
        )

        result = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=constraint_resolution,
        )

        # Ni Gramps ni l'inférence ne fournissent
        # un domaine temporel exploitable.
        self.assertIsNone(result.principal_minimum)
        self.assertIsNone(result.principal_maximum)

        # Il n'y a pas de conflit GRAMPS ↔ INFERENCE.
        self.assertIsNone(result.conflict_type)
        self.assertEqual(result.conflicting_bounds, ())

        # Le conflit d'inférence n'est cependant pas perdu.
        self.assertEqual(
            result.constraint_resolution.conflict_type,
            ConstraintConflictType.SOFT_SOFT,
        )
        self.assertEqual(
            result.constraint_resolution.conflicting_constraints,
            conflicting_constraints,
        )

if __name__ == "__main__":
    unittest.main()