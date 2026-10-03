import unittest

from descendants_timeline.inference.temporal_inference_result import (
    TemporalInferenceResult,
)

from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from descendants_timeline.model.temporal_target_entry import (
    TemporalTargetEntry,
)
from datetime import date

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
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
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.inference.constraint_resolution import (
    ConstraintResolution,
)
from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledTemporalDomain,
)
from descendants_timeline.inference.temporal_estimate import (
    TemporalEstimate,
)

class TestTemporalInferenceResult(unittest.TestCase):

    def make_target_entry(self) -> TemporalTargetEntry:
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0001",
            semantic=TargetSemantic.BIRTH,
        )

        return TemporalTargetEntry(
            target=target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )

    def make_constraint_resolution(
        self,
        target: TemporalTarget | None = None,
    ) -> ConstraintResolution:
        if target is None:
            target = self.make_target_entry().target

        return ConstraintResolution(
            target=target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

    def make_reconciled_domain(
        self,
        target_entry: TemporalTargetEntry | None = None,
        constraint_resolution: ConstraintResolution | None = None,
    ) -> ReconciledTemporalDomain:
        if target_entry is None:
            target_entry = self.make_target_entry()

        if constraint_resolution is None:
            constraint_resolution = self.make_constraint_resolution(
                target_entry.target
            )

        return ReconciledTemporalDomain(
            target=target_entry.target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=None,
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
    def make_estimate(self) -> TemporalEstimate:
        return TemporalEstimate(
            representative_value=None,
            certainty=CertaintyLevel.UNDETERMINED,
        )
  
    # test 1
    def test_rejects_invalid_target_entry(self) -> None:
        constraint_resolution = self.make_constraint_resolution()
        reconciled_domain = self.make_reconciled_domain(
            constraint_resolution=constraint_resolution,
        )

        with self.assertRaisesRegex(
            TypeError,
            "target_entry must be a TemporalTargetEntry",
        ):
            TemporalInferenceResult(
                target_entry="not a target entry",
                constraints=(),
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )

    # test 2
    def test_rejects_non_tuple_constraints(self) -> None:
        target_entry = self.make_target_entry()
        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )
        reconciled_domain = self.make_reconciled_domain(
            target_entry,
            constraint_resolution,
        )

        with self.assertRaisesRegex(
            TypeError,
            "constraints must be a tuple",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=[],
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )

    # test 3
    def test_rejects_invalid_constraint_item(self) -> None:
        target_entry = self.make_target_entry()
        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )
        reconciled_domain = self.make_reconciled_domain(
            target_entry,
            constraint_resolution,
        )

        with self.assertRaisesRegex(
            TypeError,
            "constraints must contain only TemporalConstraint objects",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=("not a constraint",),
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )

    # test 4
    def test_rejects_constraint_for_different_target(self) -> None:
        target_entry = self.make_target_entry()
        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )
        reconciled_domain = self.make_reconciled_domain(
            target_entry,
            constraint_resolution,
        )

        other_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0002",
            semantic=TargetSemantic.BIRTH,
        )

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
            owner_id="I0002",
            event_id="E0001",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=evidence_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I0002",
        )

        constraint = TemporalConstraint(
            target=other_target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1900, 1, 1),
            rule_id="TEST_RULE",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )

        with self.assertRaisesRegex(
            ValueError,
            "constraints must target target_entry.target",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(constraint,),
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )

    # test 5
    def test_rejects_invalid_constraint_resolution(self) -> None:
        target_entry = self.make_target_entry()
        reconciled_domain = self.make_reconciled_domain(
            target_entry=target_entry,
        )

        with self.assertRaisesRegex(
            TypeError,
            "constraint_resolution must be a ConstraintResolution",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(),
                constraint_resolution="not a constraint resolution",
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )

    # test 6
    def test_rejects_constraint_resolution_for_different_target(self) -> None:
        target_entry = self.make_target_entry()

        other_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0002",
            semantic=TargetSemantic.BIRTH,
        )

        other_resolution = self.make_constraint_resolution(
            other_target
        )

        other_target_entry = TemporalTargetEntry(
            target=other_target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )

        reconciled_domain = self.make_reconciled_domain(
            other_target_entry,
            other_resolution,
        )

        with self.assertRaisesRegex(
            ValueError,
            "constraint_resolution must target target_entry.target",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(),
                constraint_resolution=other_resolution,
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )
    # test 7
    def test_rejects_invalid_reconciled_domain(self) -> None:
        target_entry = self.make_target_entry()
        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )

        with self.assertRaisesRegex(
            TypeError,
            "reconciled_domain must be a ReconciledTemporalDomain",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(),
                constraint_resolution=constraint_resolution,
                reconciled_domain="not a reconciled domain",
                estimate=self.make_estimate(),
            )
    # test 8
    def test_rejects_reconciled_domain_for_different_target(self) -> None:
        target_entry = self.make_target_entry()

        other_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I0002",
            semantic=TargetSemantic.BIRTH,
        )

        other_resolution = self.make_constraint_resolution(
            other_target
        )

        other_target_entry = TemporalTargetEntry(
            target=other_target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )

        other_domain = self.make_reconciled_domain(
            other_target_entry,
            other_resolution,
        )

        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )

        with self.assertRaisesRegex(
            ValueError,
            "reconciled_domain must target target_entry.target",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(),
                constraint_resolution=constraint_resolution,
                reconciled_domain=other_domain,
                estimate=self.make_estimate(),
            )
# test 9
    def test_rejects_reconciled_domain_with_different_constraint_resolution(
        self,
    ) -> None:
        target_entry = self.make_target_entry()

        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )

        other_resolution = ConstraintResolution(
            target=target_entry.target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )

        reconciled_domain = self.make_reconciled_domain(
            target_entry,
            other_resolution,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                "reconciled_domain.constraint_resolution "
                "must be constraint_resolution"
            ),
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(),
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=self.make_estimate(),
            )
    # test 10
    def test_rejects_invalid_estimate(self) -> None:
        target_entry = self.make_target_entry()
        constraint_resolution = self.make_constraint_resolution(
            target_entry.target
        )
        reconciled_domain = self.make_reconciled_domain(
            target_entry,
            constraint_resolution,
        )

        with self.assertRaisesRegex(
            TypeError,
            "estimate must be a TemporalEstimate",
        ):
            TemporalInferenceResult(
                target_entry=target_entry,
                constraints=(),
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate="not an estimate",
            )

    if __name__ == "__main__":
        unittest.main()