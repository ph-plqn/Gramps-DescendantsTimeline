"""Tests du modèle TemporalTargetEntry."""

import unittest
from datetime import date

from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from descendants_timeline.model.temporal_target_anomaly import (
    TemporalTargetAnomaly,
    TemporalTargetAnomalyType,
)
from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry


class TestTemporalTargetEntry(unittest.TestCase):

    def _birth_target(self) -> TemporalTarget:
        return TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

    def _gramps_exact_value(self) -> TemporalValue:
        value = date(1812, 4, 5)

        return TemporalValue(
            source_value="5 avril 1812",
            source_calendar="GREGORIAN",
            normalized_minimum=value,
            normalized_maximum=value,
            representative_value=value,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

    def _multiple_birth_anomaly(self) -> TemporalTargetAnomaly:
        return TemporalTargetAnomaly(
            anomaly_type=(
                TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS
            ),
            event_ids=("E001", "E002"),
        )

    def test_valid_entry_with_gramps_value(self) -> None:
        target = self._birth_target()
        gramps_value = self._gramps_exact_value()

        entry = TemporalTargetEntry(
            target=target,
            gramps_value=gramps_value,
            anomalies=(),
        )

        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, gramps_value)
        self.assertEqual(entry.anomalies, ())

    def test_valid_unknown_value_without_anomaly(self) -> None:
        entry = TemporalTargetEntry(
            target=self._birth_target(),
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )

        self.assertIs(
            entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )

    def test_valid_multiple_principal_events_with_unknown_value(self) -> None:
        anomaly = self._multiple_birth_anomaly()

        entry = TemporalTargetEntry(
            target=self._birth_target(),
            gramps_value=TemporalValue.unknown(),
            anomalies=(anomaly,),
        )

        self.assertEqual(entry.anomalies, (anomaly,))
        self.assertIs(
            entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )

    def test_target_must_be_temporal_target(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetEntry(
                target="I001/BIRTH",  # type: ignore[arg-type]
                gramps_value=TemporalValue.unknown(),
                anomalies=(),
            )

    def test_gramps_value_must_be_temporal_value(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetEntry(
                target=self._birth_target(),
                gramps_value=None,  # type: ignore[arg-type]
                anomalies=(),
            )

    def test_anomalies_must_be_tuple(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetEntry(
                target=self._birth_target(),
                gramps_value=TemporalValue.unknown(),
                anomalies=[],  # type: ignore[arg-type]
            )

    def test_each_anomaly_must_be_temporal_target_anomaly(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetEntry(
                target=self._birth_target(),
                gramps_value=TemporalValue.unknown(),
                anomalies=("anomaly",),  # type: ignore[arg-type]
            )

    def test_anomalies_must_not_contain_duplicates(self) -> None:
        anomaly = self._multiple_birth_anomaly()

        with self.assertRaises(ValueError):
            TemporalTargetEntry(
                target=self._birth_target(),
                gramps_value=TemporalValue.unknown(),
                anomalies=(anomaly, anomaly),
            )

    def test_multiple_principal_events_requires_unknown_gramps_value(self) -> None:
        anomaly = self._multiple_birth_anomaly()

        with self.assertRaises(ValueError):
            TemporalTargetEntry(
                target=self._birth_target(),
                gramps_value=self._gramps_exact_value(),
                anomalies=(anomaly,),
            )

    def test_entry_is_immutable(self) -> None:
        entry = TemporalTargetEntry(
            target=self._birth_target(),
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )

        with self.assertRaises(AttributeError):
            entry.anomalies = ()  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()