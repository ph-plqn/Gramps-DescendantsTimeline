from __future__ import annotations

import unittest
from datetime import date

from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    TemporalValue,
    ValueOrigin,
    SourceQuality
)


class TemporalValueTests(unittest.TestCase):
    def test_exact_gramps_date_is_usable(self) -> None:
        value = TemporalValue(
            source_value="1786",
            source_calendar="Gregorian",
            normalized_minimum=date(1786, 1, 1),
            normalized_maximum=date(1786, 1, 1),
            representative_value=date(1786, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )
        self.assertTrue(value.is_exact)
        self.assertTrue(value.is_usable_as_evidence)

    def test_documented_gramps_interval_is_usable(self) -> None:
        value = TemporalValue(
            source_value="entre le 10/02/1947 et le 28/02/1947",
            source_calendar="Gregorian",
            normalized_minimum=date(1947, 2, 10),
            normalized_maximum=date(1947, 2, 28),
            representative_value=date(1947, 2, 19),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )
        self.assertTrue(value.has_closed_interval)
        self.assertFalse(value.is_exact)
        self.assertTrue(value.is_usable_as_evidence)

    def test_calculated_gramps_date_is_displayable_but_unproven(self) -> None:
        value = TemporalValue(
            source_value="1786",
            source_calendar="Gregorian",
            normalized_minimum=date(1786, 1, 1),
            normalized_maximum=date(1786, 1, 1),
            representative_value=date(1786, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.CALCULATED,
            evidence_status=EvidenceStatus.EVIDENCE_UNPROVEN,
            certainty=CertaintyLevel.UNDETERMINED,
        )
        self.assertTrue(value.is_exact)
        self.assertFalse(value.is_usable_as_evidence)
        self.assertEqual(value.representative_value, date(1786, 1, 1))

    def test_inferred_interval_has_no_gramps_source_value(self) -> None:
        value = TemporalValue(
            source_value=None,
            source_calendar=None,
            normalized_minimum=date(1786, 1, 1),
            normalized_maximum=date(1792, 12, 31),
            representative_value=date(1789, 7, 2),
            value_origin=ValueOrigin.INFERRED,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.PROBABLE,
        )
        self.assertEqual(value.value_origin, ValueOrigin.INFERRED)
        self.assertTrue(value.is_usable_as_evidence)

    def test_unknown_factory(self) -> None:
        value = TemporalValue.unknown()
        self.assertEqual(value.value_origin, ValueOrigin.UNKNOWN)
        self.assertEqual(value.evidence_status, EvidenceStatus.EVIDENCE_UNAVAILABLE)
        self.assertIsNone(value.representative_value)

    def test_rejects_inverted_interval(self) -> None:
        with self.assertRaises(ValueError):
            TemporalValue(
                source_value="intervalle invalide",
                source_calendar="Gregorian",
                normalized_minimum=date(1800, 1, 2),
                normalized_maximum=date(1800, 1, 1),
                representative_value=None,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            )

    def test_rejects_representative_outside_interval(self) -> None:
        with self.assertRaises(ValueError):
            TemporalValue(
                source_value=None,
                source_calendar=None,
                normalized_minimum=date(1786, 1, 1),
                normalized_maximum=date(1792, 12, 31),
                representative_value=date(1800, 1, 1),
                value_origin=ValueOrigin.INFERRED,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.POSSIBLE,
            )

    def test_unknown_cannot_contain_a_date(self) -> None:
        with self.assertRaises(ValueError):
            TemporalValue(
                source_value=None,
                source_calendar=None,
                normalized_minimum=None,
                normalized_maximum=None,
                representative_value=date(1800, 1, 1),
                value_origin=ValueOrigin.UNKNOWN,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_UNAVAILABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            )

    def test_unknown_cannot_contain_a_calendar(self) -> None:
        with self.assertRaises(ValueError):
            TemporalValue(
                source_value=None,
                source_calendar="Gregorian",
                normalized_minimum=None,
                normalized_maximum=None,
                representative_value=None,
                value_origin=ValueOrigin.UNKNOWN,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_UNAVAILABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            )

    def test_calculated_cannot_be_evidence_usable(self) -> None:
        with self.assertRaises(ValueError):
            TemporalValue(
                source_value="01/01/1810",
                source_calendar="Gregorian",
                normalized_minimum=date(1810, 1, 1),
                normalized_maximum=date(1810, 1, 1),
                representative_value=date(1810, 1, 1),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.CALCULATED,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            )

    def test_gramps_without_source_value(self) -> None:
        with self.assertRaises(ValueError):
            TemporalValue(
                source_value=None,
                source_calendar=None,
                normalized_minimum=None,
                normalized_maximum=None,
                representative_value=None,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_UNAVAILABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            )


if __name__ == "__main__":
    unittest.main()
