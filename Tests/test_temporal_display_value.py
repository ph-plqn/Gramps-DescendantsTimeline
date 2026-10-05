import unittest
from datetime import date

from descendants_timeline.inference.constraint_resolution import ConstraintResolution
from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledTemporalDomain,
)
from descendants_timeline.inference.temporal_estimate import TemporalEstimate
from descendants_timeline.inference.temporal_inference_result import (
    TemporalInferenceResult,
)
from descendants_timeline.model.temporal import CertaintyLevel, TemporalValue
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry


class TemporalDisplayValueTests(unittest.TestCase):
    def test_birth_display_value_equals_representative_date(self) -> None:
        representative_value = date(1900, 5, 17)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=representative_value,
                certainty=CertaintyLevel.PROBABLE,
            ),
        )

        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, representative_value)

    def test_birth_without_representative_date_uses_domain_maximum(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        minimum = date(1695, 1, 1)
        maximum = date(1808, 1, 1)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=minimum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=ReconciledBound(
                value=maximum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, maximum)

    def test_birth_without_representative_date_or_domain_maximum_returns_none(self) -> None:
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertIsNone(display_value)

    def test_death_without_representative_date_uses_domain_minimum(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        minimum = date(1820, 1, 1)
        maximum = date(1933, 1, 1)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=minimum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=ReconciledBound(
                value=maximum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, minimum)

    def test_death_without_representative_date_or_domain_minimum_returns_none(self) -> None:
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertIsNone(display_value)

    def test_marriage_without_representative_date_uses_closed_domain_midpoint(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        minimum = date(1820, 1, 1)
        maximum = date(1820, 1, 11)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=minimum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=ReconciledBound(
                value=maximum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, date(1820, 1, 6))

    def test_marriage_without_representative_date_uses_only_domain_minimum(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        minimum = date(1820, 1, 1)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=minimum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, minimum)

    def test_marriage_without_representative_date_uses_only_domain_maximum(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        maximum = date(1820, 1, 1)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=ReconciledBound(
                value=maximum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, maximum)

    def test_marriage_without_representative_date_or_domain_bounds_returns_none(self) -> None:
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertIsNone(display_value)

    def test_divorce_without_representative_date_uses_closed_domain_midpoint(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )

        minimum = date(1900, 1, 1)
        maximum = date(1900, 1, 11)
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.DIVORCE,
        )
        target_entry = TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
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
        reconciled_domain = ReconciledTemporalDomain(
            target=target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=minimum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=ReconciledBound(
                value=maximum,
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            conflict_type=None,
            conflicting_bounds=(),
        )
        result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        display_value = determine_display_value(result)

        self.assertEqual(display_value, date(1900, 1, 6))
