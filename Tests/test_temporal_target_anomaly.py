"""Tests du modèle TemporalTargetAnomaly."""

import unittest

from descendants_timeline.model.temporal_target_anomaly import (
    TemporalTargetAnomaly,
    TemporalTargetAnomalyType,
)


class TestTemporalTargetAnomaly(unittest.TestCase):

    def test_valid_multiple_principal_events(self) -> None:
        anomaly = TemporalTargetAnomaly(
            anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
            event_ids=("E001", "E002"),
        )

        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E001", "E002"))

    def test_anomaly_type_must_be_temporal_target_anomaly_type(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetAnomaly(
                anomaly_type="MULTIPLE_PRINCIPAL_EVENTS",  # type: ignore[arg-type]
                event_ids=("E001", "E002"),
            )

    def test_event_ids_must_be_tuple(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=["E001", "E002"],  # type: ignore[arg-type]
            )

    def test_event_ids_must_not_be_empty(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=(),
            )

    def test_event_id_must_be_string(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=("E001", 2),  # type: ignore[arg-type]
            )

    def test_event_id_must_not_be_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=("E001", ""),
            )

    def test_event_id_must_not_be_whitespace_only(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=("E001", "   "),
            )

    def test_event_ids_must_not_contain_duplicates(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=("E001", "E001"),
            )
    def test_multiple_principal_events_requires_at_least_two_events(self) -> None:
        with self.assertRaises(ValueError):
            TemporalTargetAnomaly(
                anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
                event_ids=("E001",),
            )
    def test_anomaly_is_immutable(self) -> None:
        anomaly = TemporalTargetAnomaly(
            anomaly_type=TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
            event_ids=("E001", "E002"),
        )

        with self.assertRaises(AttributeError):
            anomaly.event_ids = ("E003", "E004")  # type: ignore[misc]

if __name__ == "__main__":
    unittest.main()