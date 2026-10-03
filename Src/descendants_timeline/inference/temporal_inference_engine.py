"""Orchestration du moteur d'inférence temporelle."""

from __future__ import annotations

from descendants_timeline.model.genealogy import RawGenealogyData


from descendants_timeline.inference.temporal_inference_result import (
    TemporalInferenceResult,
)
from descendants_timeline.inference.temporal_target_index_builder import (
    TemporalTargetIndexBuilder,
)
from descendants_timeline.inference.constraint_resolver import (
    ConstraintResolver,
)
from descendants_timeline.inference.temporal_reconciler import (
    TemporalReconciler,
)
from descendants_timeline.inference.temporal_estimator import (
    TemporalEstimator,
)
from descendants_timeline.inference.temporal_evidence_builder import (
    TemporalEvidenceBuilder,
)
from descendants_timeline.inference.rule_context import (
    RuleContext,
)
from descendants_timeline.inference.rule_engine import (
    RuleEngine,
)
from descendants_timeline.inference.default_rules import (
    default_rules,
)
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class TemporalInferenceEngine:
    """Orchestre le pipeline complet d'inférence temporelle."""

    rule_engine: RuleEngine = field(
        default_factory=lambda: RuleEngine(
            rules=default_rules()
        )
    )

    def __post_init__(self) -> None:
        if not isinstance(self.rule_engine, RuleEngine):
            raise TypeError(
                "rule_engine must be a RuleEngine"
            )


    def run(
        self,
        data: RawGenealogyData,
    ) -> tuple[TemporalInferenceResult, ...]:
        if not isinstance(data, RawGenealogyData):
            raise TypeError(
                "data must be a RawGenealogyData"
            )

        target_index = TemporalTargetIndexBuilder().build(data)
        evidences = TemporalEvidenceBuilder().build(data)

        context = RuleContext(
            data=data,
            evidences=evidences,
        )

        resolver = ConstraintResolver()
        reconciler = TemporalReconciler()
        estimator = TemporalEstimator()

        results: list[TemporalInferenceResult] = []

        for target_entry in target_index.entries.values():
            constraints = self.rule_engine.evaluate(
                target_entry.target,
                context,
            )

            constraint_resolution = resolver.resolve(
                target_entry.target,
                constraints,
            )

            reconciled_domain = reconciler.reconcile(
                target_entry.target,
                target_entry.gramps_value,
                constraint_resolution,
            )

            estimate = estimator.estimate(
                reconciled_domain
            )

            results.append(
                TemporalInferenceResult(
                    target_entry=target_entry,
                    constraints=constraints,
                    constraint_resolution=constraint_resolution,
                    reconciled_domain=reconciled_domain,
                    estimate=estimate,
                )
            )

        return tuple(results)