from datetime import date

from descendants_timeline.inference.temporal_inference_result import (
    TemporalInferenceResult,
)
from descendants_timeline.model.temporal_target import TargetSemantic


def determine_display_value(result: TemporalInferenceResult) -> date | None:
    representative_value = result.estimate.representative_value
    if isinstance(representative_value, date):
        return representative_value

    if (
        representative_value is None
        and result.target_entry.target.semantic == TargetSemantic.BIRTH
    ):
        maximum = result.reconciled_domain.principal_maximum
        if maximum is not None:
            return maximum.value

    if (
        representative_value is None
        and result.target_entry.target.semantic == TargetSemantic.DEATH
    ):
        minimum = result.reconciled_domain.principal_minimum
        if minimum is not None:
            return minimum.value

    if (
        representative_value is None
        and result.target_entry.target.semantic in (
            TargetSemantic.MARRIAGE,
            TargetSemantic.DIVORCE,
        )
    ):
        minimum = result.reconciled_domain.principal_minimum
        maximum = result.reconciled_domain.principal_maximum
        if minimum is not None and maximum is not None:
            return minimum.value + (maximum.value - minimum.value) // 2
        if minimum is not None and maximum is None:
            return minimum.value
        if minimum is None and maximum is not None:
            return maximum.value
