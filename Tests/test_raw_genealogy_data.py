from __future__ import annotations

import unittest
from datetime import date

from descendants_timeline.model.child_ref import ChildRef, ChildRelation
from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.family import Family
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import EventRoleSemantic, PersonEventRef
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)


def make_date() -> TemporalValue:
    return TemporalValue(
        source_value="01/01/1900",
        source_calendar="Gregorian",
        normalized_minimum=date(1900, 1, 1),
        normalized_maximum=date(1900, 1, 1),
        representative_value=date(1900, 1, 1),
        value_origin=ValueOrigin.GRAMPS,
        source_quality=SourceQuality.NORMAL,
        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
        certainty=CertaintyLevel.CERTAIN,
    )


def make_data():
    event = Event("E0001", "Birth", EventSemantic.BIRTH, make_date())

    p1 = Person(
        "I0001", "Jean DUPONT", PersonGender.MALE,
        (PersonEventRef("E0001", EventRoleSemantic.PRINCIPAL, "Principal"),),
        (), ("F0001",)
    )
    p2 = Person("I0002", "Marie DURAND", PersonGender.FEMALE, (), (), ("F0001",))
    child = Person("I0003", "Paul DUPONT", PersonGender.MALE, (), ("F0001",), ())

    family = Family(
        "F0001",
        "I0001",
        "I0002",
        (),
        (ChildRef("I0003", ChildRelation.BIRTH, ChildRelation.BIRTH),),
    )

    return (
        {"I0001": p1, "I0002": p2, "I0003": child},
        {"F0001": family},
        {"E0001": event},
    )


class RawGenealogyDataTests(unittest.TestCase):
    def test_valid_data(self) -> None:
        persons, families, events = make_data()
        data = RawGenealogyData(persons, families, events, "I0001")
        self.assertEqual(data.root_person_id, "I0001")
        self.assertEqual(data.persons["I0003"].display_name, "Paul DUPONT")

    def test_isolated_root_is_valid(self) -> None:
        root = Person("I0100", "I0100", PersonGender.UNKNOWN, (), (), ())
        data = RawGenealogyData({"I0100": root}, {}, {}, "I0100")
        self.assertEqual(len(data.persons), 1)

    def test_rejects_missing_root(self) -> None:
        persons, families, events = make_data()
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I9999")

    def test_rejects_empty_root(self) -> None:
        persons, families, events = make_data()
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "")

    def test_rejects_person_key_mismatch(self) -> None:
        persons, families, events = make_data()
        p = persons.pop("I0001")
        persons["I9999"] = p
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I9999")

    def test_rejects_family_key_mismatch(self) -> None:
        persons, families, events = make_data()
        f = families.pop("F0001")
        families["F9999"] = f
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I0001")

    def test_rejects_event_key_mismatch(self) -> None:
        persons, families, events = make_data()
        e = events.pop("E0001")
        events["E9999"] = e
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I0001")

    def test_rejects_missing_event_reference(self) -> None:
        persons, families, events = make_data()
        events.clear()
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I0001")

    def test_rejects_missing_family_reference(self) -> None:
        persons, families, events = make_data()
        families.clear()
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I0001")

    def test_rejects_missing_parent_reference(self) -> None:
        persons, families, events = make_data()
        del persons["I0002"]
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I0001")

    def test_rejects_missing_child_reference(self) -> None:
        persons, families, events = make_data()
        del persons["I0003"]
        with self.assertRaises(ValueError):
            RawGenealogyData(persons, families, events, "I0001")

    def test_input_mappings_are_copied(self) -> None:
        persons, families, events = make_data()
        data = RawGenealogyData(persons, families, events, "I0001")
        persons.clear()
        families.clear()
        events.clear()
        self.assertIn("I0001", data.persons)
        self.assertIn("F0001", data.families)
        self.assertIn("E0001", data.events)

    def test_persons_mapping_is_read_only(self) -> None:
        persons, families, events = make_data()
        data = RawGenealogyData(persons, families, events, "I0001")
        with self.assertRaises(TypeError):
            data.persons["I9999"] = data.persons["I0001"]  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
