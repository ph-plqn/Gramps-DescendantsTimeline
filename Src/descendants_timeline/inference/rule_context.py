from dataclasses import dataclass

from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.temporal_evidence import TemporalEvidence


@dataclass(frozen=True, slots=True)
class RuleContext:
    data: RawGenealogyData
    evidences: tuple[TemporalEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.data, RawGenealogyData):
            raise TypeError("data must be a RawGenealogyData")

        if not isinstance(self.evidences, tuple):
            raise TypeError("evidences must be a tuple")

        if not all(
            isinstance(evidence, TemporalEvidence)
            for evidence in self.evidences
        ):
            raise TypeError(
                "evidences must contain only TemporalEvidence objects"
            )