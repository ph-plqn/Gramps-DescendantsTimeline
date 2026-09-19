import unittest
from datetime import date

from descendants_timeline.inference.constraint_resolution import (
    ConstraintResolution,
)
from descendants_timeline.inference.temporal_estimate import (
    TemporalEstimate,
)
from descendants_timeline.inference.temporal_estimator import (
    TemporalEstimator,
)
from descendants_timeline.inference.temporal_reconciler import (
    TemporalReconciler,
)
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
from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from descendants_timeline.inference.resolved_bound import (
    ResolvedBound,
)
from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBound,
    ReconciledBoundOrigin,
    ReconciledTemporalDomain,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)

class TestTemporalEstimator(unittest.TestCase):

    def make_target(self):
        return TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

    def make_empty_resolution(self, target):
        return ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

    def make_domain(self, gramps_value):
        target = self.make_target()

        resolution = self.make_empty_resolution(target)

        return TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=resolution,
        )

    def make_resolved_bound(
        self,
        target,
        value,
        operator,
        strength,
    ):
        evidence_date = TemporalValue(
            source_value="01/01/1900",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1900, 1, 1),
            normalized_maximum=date(1900, 1, 1),
            representative_value=date(1900, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I9999",
            event_id="E9999",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I9999",
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

    
    def test_rejects_invalid_domain_type(self):
        estimator = TemporalEstimator()

        with self.assertRaises(TypeError):
            estimator.estimate("not a domain")
    def test_empty_domain_returns_no_representative_value(self):
        domain = self.make_domain(
            TemporalValue.unknown()
        )

        result = TemporalEstimator().estimate(domain)

        self.assertIsInstance(result, TemporalEstimate)
        self.assertIsNone(result.representative_value)
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_gramps_interval_returns_no_representative_value(self):
        gramps_value = TemporalValue(
            source_value="entre 1817 et 1825",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1817, 1, 1),
            normalized_maximum=date(1825, 1, 1),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        domain = self.make_domain(gramps_value)

        result = TemporalEstimator().estimate(domain)

        self.assertIsNone(result.representative_value)
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_exact_usable_gramps_date_is_certain(self):
        exact_date = date(1821, 3, 12)

        gramps_value = TemporalValue(
            source_value="12/03/1821",
            source_calendar="GREGORIAN",
            normalized_minimum=exact_date,
            normalized_maximum=exact_date,
            representative_value=exact_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        domain = self.make_domain(gramps_value)

        result = TemporalEstimator().estimate(domain)

        self.assertEqual(
            result.representative_value,
            exact_date,
        )
        self.assertEqual(
            result.certainty,
            CertaintyLevel.CERTAIN,
        )
    def test_exact_unproven_gramps_date_is_not_certain(self):
        exact_date = date(1821, 3, 12)

        gramps_value = TemporalValue(
            source_value="12/03/1821",
            source_calendar="GREGORIAN",
            normalized_minimum=exact_date,
            normalized_maximum=exact_date,
            representative_value=exact_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.CALCULATED,
            evidence_status=EvidenceStatus.EVIDENCE_UNPROVEN,
            certainty=CertaintyLevel.UNDETERMINED,
        )

        domain = self.make_domain(gramps_value)

        result = TemporalEstimator().estimate(domain)

        # Le domaine est ponctuel :
        # il possède donc une valeur représentative.
        self.assertEqual(
            result.representative_value,
            exact_date,
        )

        # Mais la donnée Gramps n'est pas prouvée.
        # La qualification précise sera affinée ultérieurement.
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_exact_inferred_domain_has_representative_value(
        self,
    ):
        exact_date = date(1821, 3, 12)

        target = self.make_target()

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=exact_date,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=exact_date,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=inferred_maximum,
            refined_minimum=inferred_minimum,
            refined_maximum=inferred_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )

        domain = TemporalReconciler().reconcile(
            target=target,
            gramps_value=TemporalValue.unknown(),
            constraint_resolution=resolution,
        )

        result = TemporalEstimator().estimate(domain)

        self.assertEqual(
            result.representative_value,
            exact_date,
        )
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_exact_mixed_domain_gramps_minimum_inference_maximum(
        self,
    ):
        exact_date = date(1821, 3, 12)
        target = self.make_target()

        gramps_value = TemporalValue(
            source_value="après le 12/03/1821",
            source_calendar="GREGORIAN",
            normalized_minimum=exact_date,
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        inferred_maximum = self.make_resolved_bound(
            target=target,
            value=exact_date,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=inferred_maximum,
            refined_minimum=None,
            refined_maximum=inferred_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )

        domain = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=resolution,
        )

        result = TemporalEstimator().estimate(domain)

        self.assertEqual(
            result.representative_value,
            exact_date,
        )
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_exact_mixed_domain_inference_minimum_gramps_maximum(
        self,
    ):
        exact_date = date(1821, 3, 12)
        target = self.make_target()

        gramps_value = TemporalValue(
            source_value="avant le 12/03/1821",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=exact_date,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        inferred_minimum = self.make_resolved_bound(
            target=target,
            value=exact_date,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
        )

        resolution = ConstraintResolution(
            target=target,
            hard_minimum=inferred_minimum,
            hard_maximum=None,
            refined_minimum=inferred_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        domain = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_value,
            constraint_resolution=resolution,
        )

        result = TemporalEstimator().estimate(domain)

        self.assertEqual(
            result.representative_value,
            exact_date,
        )
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_open_domain_with_minimum_has_no_representative_value(
        self,
    ):
        minimum_date = date(1821, 3, 12)

        gramps_value = TemporalValue(
            source_value="après le 12/03/1821",
            source_calendar="GREGORIAN",
            normalized_minimum=minimum_date,
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        domain = self.make_domain(gramps_value)

        result = TemporalEstimator().estimate(domain)

        self.assertIsNone(result.representative_value)
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )
    def test_open_domain_with_maximum_has_no_representative_value(
        self,
    ):
        maximum_date = date(1821, 3, 12)

        gramps_value = TemporalValue(
            source_value="avant le 12/03/1821",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=maximum_date,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        domain = self.make_domain(gramps_value)

        result = TemporalEstimator().estimate(domain)

        self.assertIsNone(result.representative_value)
        self.assertEqual(
            result.certainty,
            CertaintyLevel.UNDETERMINED,
        )