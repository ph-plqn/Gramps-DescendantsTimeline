from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)


def make_known_date() -> TemporalValue:
    """Construit une date Gramps simple réutilisée dans les tests."""

    return TemporalValue(
        source_value="14/01/1902",
        source_calendar="Gregorian",
        normalized_minimum=date(1902, 1, 14),
        normalized_maximum=date(1902, 1, 14),
        representative_value=date(1902, 1, 14),
        value_origin=ValueOrigin.GRAMPS,
        source_quality=SourceQuality.NORMAL,
        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
        certainty=CertaintyLevel.CERTAIN,
    )


class EventTests(unittest.TestCase):
    def test_valid_birth_event(self) -> None:
        event = Event(
            event_id="E0001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=make_known_date(),
        )

        self.assertEqual(event.event_id, "E0001")
        self.assertEqual(event.source_type, "Birth")
        self.assertIs(event.semantic, EventSemantic.BIRTH)
        self.assertTrue(event.date.is_exact)

    def test_unknown_semantic_preserves_custom_source_type(self) -> None:
        event = Event(
            event_id="E0002",
            source_type="Occupation",
            semantic=EventSemantic.UNKNOWN,
            date=make_known_date(),
        )

        self.assertEqual(event.source_type, "Occupation")
        self.assertIs(event.semantic, EventSemantic.UNKNOWN)

    def test_rejects_empty_event_id(self) -> None:
        with self.assertRaises(ValueError):
            Event(
                event_id="",
                source_type="Birth",
                semantic=EventSemantic.BIRTH,
                date=make_known_date(),
            )

    def test_rejects_blank_event_id(self) -> None:
        with self.assertRaises(ValueError):
            Event(
                event_id="   ",
                source_type="Birth",
                semantic=EventSemantic.BIRTH,
                date=make_known_date(),
            )

    def test_rejects_empty_source_type(self) -> None:
        with self.assertRaises(ValueError):
            Event(
                event_id="E0003",
                source_type="",
                semantic=EventSemantic.BIRTH,
                date=make_known_date(),
            )

    def test_rejects_blank_source_type(self) -> None:
        with self.assertRaises(ValueError):
            Event(
                event_id="E0004",
                source_type="   ",
                semantic=EventSemantic.BIRTH,
                date=make_known_date(),
            )

    def test_rejects_semantic_as_plain_string(self) -> None:
        with self.assertRaises(TypeError):
            Event(
                event_id="E0005",
                source_type="Birth",
                semantic="BIRTH",  # type: ignore[arg-type]
                date=make_known_date(),
            )

    def test_rejects_date_that_is_not_temporal_value(self) -> None:
        with self.assertRaises(TypeError):
            Event(
                event_id="E0006",
                source_type="Birth",
                semantic=EventSemantic.BIRTH,
                date=date(1902, 1, 14),  # type: ignore[arg-type]
            )

    def test_event_is_immutable(self) -> None:
        event = Event(
            event_id="E0007",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=make_known_date(),
        )

        with self.assertRaises(FrozenInstanceError):
            event.source_type = "Death"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
