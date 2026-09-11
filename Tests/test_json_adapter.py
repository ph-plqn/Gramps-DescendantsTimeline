from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from descendants_timeline.gramps.json_adapter import JsonGrampsAdapter
from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.person import PersonGender


REAL_GRAMPS_JSON = Path(__file__).resolve().parent.parent / "74.json"

CENSUS_GRAMPS_JSON = (
    Path(__file__).resolve().parent.parent / "Recensement.json"
)

def read_records(path: Path) -> list[dict]:
    """Lit l'export JSON Lines Gramps pour préparer les assertions de test."""

    records: list[dict] = []

    with path.open("r", encoding="utf-8-sig") as stream:
        for raw_line in stream:
            line = raw_line.strip()
            if line:
                records.append(json.loads(line))

    return records


def first_person_id(records: list[dict]) -> str:
    """Retourne un person_id réellement présent dans le fichier de test."""

    for record in records:
        if record.get("_class") == "Person":
            person_id = record.get("gramps_id")
            if isinstance(person_id, str) and person_id:
                return person_id

    raise AssertionError("The JSON fixture contains no Person object")


class JsonGrampsAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if REAL_GRAMPS_JSON.is_file():
            cls.records = read_records(REAL_GRAMPS_JSON)
            cls.root_person_id = first_person_id(cls.records)
        else:
            cls.records = []
            cls.root_person_id = ""

    def require_real_export(self) -> None:
        if not REAL_GRAMPS_JSON.is_file():
            self.skipTest("74.json is not available next to the project root")

    def load_real_export(self):
        self.require_real_export()

        return JsonGrampsAdapter().load(
            REAL_GRAMPS_JSON,
            root_person_id=self.root_person_id,
        )

    def test_real_export_builds_raw_genealogy_data(self) -> None:
        data = self.load_real_export()

        source_persons = [
            r for r in self.records if r.get("_class") == "Person"
        ]
        source_families = [
            r for r in self.records if r.get("_class") == "Family"
        ]
        source_events = [
            r for r in self.records if r.get("_class") == "Event"
        ]

        self.assertEqual(len(data.persons), len(source_persons))
        self.assertEqual(len(data.families), len(source_families))
        self.assertEqual(len(data.events), len(source_events))
        self.assertEqual(data.root_person_id, self.root_person_id)

    def test_real_export_converts_root_person(self) -> None:
        data = self.load_real_export()
        person = data.persons[self.root_person_id]

        self.assertEqual(person.person_id, self.root_person_id)
        self.assertTrue(person.display_name)
        self.assertIsInstance(person.gender, PersonGender)

    def test_all_family_references_resolve(self) -> None:
        data = self.load_real_export()

        for family in data.families.values():
            if family.parent1_id is not None:
                self.assertIn(family.parent1_id, data.persons)

            if family.parent2_id is not None:
                self.assertIn(family.parent2_id, data.persons)

            for child_ref in family.child_refs:
                self.assertIn(child_ref.person_id, data.persons)

            for event_ref in family.event_refs:
                self.assertIn(event_ref.event_id, data.events)

    def test_all_person_references_resolve(self) -> None:
        data = self.load_real_export()

        for person in data.persons.values():
            for family_id in person.parent_family_ids:
                self.assertIn(family_id, data.families)

            for family_id in person.family_ids:
                self.assertIn(family_id, data.families)

            for event_ref in person.event_refs:
                self.assertIn(event_ref.event_id, data.events)

    def test_unknown_event_types_are_preserved(self) -> None:
        data = self.load_real_export()

        unknown_events = [
            event
            for event in data.events.values()
            if event.semantic is EventSemantic.UNKNOWN
        ]

        # Ce test reste valide même si l'export ne contient aucun type inconnu.
        for event in unknown_events:
            self.assertTrue(event.source_type)

    def test_non_gregorian_dates_are_preserved_if_present(self) -> None:
        data = self.load_real_export()

        source_non_gregorian_ids = {
            record["gramps_id"]
            for record in self.records
            if record.get("_class") == "Event"
            and isinstance(record.get("date"), dict)
            and record["date"].get("calendar") not in (None, 0)
        }

        for event_id in source_non_gregorian_ids:
            event = data.events[event_id]
            self.assertIsNotNone(event.date.source_calendar)
            self.assertIsNotNone(event.date.source_value)
            self.assertIsNone(event.date.normalized_minimum)
            self.assertIsNone(event.date.normalized_maximum)

    def test_invalid_json_line_is_reported_with_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(
                '{"_class":"Person"}\nnot-json\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "line 2"):
                JsonGrampsAdapter().load(
                    path,
                    root_person_id="I0001",
                )

    def test_real_export_maps_census_event_semantic(self) -> None:
        if not CENSUS_GRAMPS_JSON.exists():
            self.skipTest(
                f"Missing real Gramps census export: {CENSUS_GRAMPS_JSON}"
            )

        data = JsonGrampsAdapter().load(
            CENSUS_GRAMPS_JSON,
            root_person_id="I0000",
        )

        census_events = [
            event
            for event in data.events.values()
            if event.semantic is EventSemantic.CENSUS
        ]

        self.assertEqual(len(census_events), 1)

        census_event = census_events[0]

        self.assertEqual(census_event.event_id, "E0000")
        self.assertEqual(
            census_event.semantic,
            EventSemantic.CENSUS,
        )
        self.assertEqual(census_event.source_type, "Census")


if __name__ == "__main__":
    unittest.main()
