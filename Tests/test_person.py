from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
    PersonEventRef,
)


def make_event_ref(event_id: str = "E0001") -> PersonEventRef:
    return PersonEventRef(
        event_id=event_id,
        semantic_role=EventRoleSemantic.PRINCIPAL,
        source_role="Principal",
    )


class PersonTests(unittest.TestCase):
    def test_valid_person(self) -> None:
        person = Person(
            "I0001",
            "Jean DUPONT",
            PersonGender.MALE,
            (make_event_ref(),),
            ("F0001",),
            ("F0002", "F0003"),
        )
        self.assertEqual(person.person_id, "I0001")
        self.assertEqual(person.family_ids, ("F0002", "F0003"))

    def test_person_without_parent_family_is_valid(self) -> None:
        person = Person("I0002", "Marie DURAND", PersonGender.FEMALE, (), (), ("F0010",))
        self.assertEqual(person.parent_family_ids, ())

    def test_person_without_any_family_is_valid(self) -> None:
        person = Person("I0003", "Louis MARTIN", PersonGender.MALE, (), (), ())
        self.assertEqual(person.family_ids, ())

    def test_missing_name_can_use_gramps_id_as_display_name(self) -> None:
        person = Person("I0709", "I0709", PersonGender.UNKNOWN, (), (), ())
        self.assertEqual(person.display_name, "I0709")

    def test_unknown_gender_is_valid(self) -> None:
        person = Person("I0011", "Enfant I0011", PersonGender.UNKNOWN, (), (), ())
        self.assertIs(person.gender, PersonGender.UNKNOWN)

    def test_other_gender_is_valid(self) -> None:
        person = Person("I0012", "Personne I0012", PersonGender.OTHER, (), (), ())
        self.assertIs(person.gender, PersonGender.OTHER)

    def test_rejects_empty_person_id(self) -> None:
        with self.assertRaises(ValueError):
            Person("", "Jean DUPONT", PersonGender.MALE, (), (), ())

    def test_rejects_blank_display_name(self) -> None:
        with self.assertRaises(ValueError):
            Person("I0004", "   ", PersonGender.MALE, (), (), ())

    def test_rejects_gender_as_plain_string(self) -> None:
        with self.assertRaises(TypeError):
            Person("I0005", "Jean DUPONT", "MALE", (), (), ())  # type: ignore[arg-type]

    def test_rejects_event_refs_as_list(self) -> None:
        with self.assertRaises(TypeError):
            Person("I0006", "Jean DUPONT", PersonGender.MALE, [make_event_ref()], (), ())  # type: ignore[arg-type]

    def test_rejects_invalid_object_in_event_refs(self) -> None:
        with self.assertRaises(TypeError):
            Person("I0007", "Jean DUPONT", PersonGender.MALE, ("E0001",), (), ())  # type: ignore[arg-type]

    def test_rejects_parent_family_ids_as_list(self) -> None:
        with self.assertRaises(TypeError):
            Person("I0008", "Jean DUPONT", PersonGender.MALE, (), ["F0001"], ())  # type: ignore[arg-type]

    def test_rejects_empty_parent_family_id(self) -> None:
        with self.assertRaises(ValueError):
            Person("I0009", "Jean DUPONT", PersonGender.MALE, (), ("",), ())

    def test_rejects_family_ids_as_list(self) -> None:
        with self.assertRaises(TypeError):
            Person("I0010", "Jean DUPONT", PersonGender.MALE, (), (), ["F0002"])  # type: ignore[arg-type]

    def test_rejects_empty_family_id(self) -> None:
        with self.assertRaises(ValueError):
            Person("I0013", "Jean DUPONT", PersonGender.MALE, (), (), ("F0002", ""))

    def test_family_order_is_preserved(self) -> None:
        person = Person(
            "I0014", "Jean DUPONT", PersonGender.MALE, (),
            ("F0003", "F0001"), ("F0009", "F0004", "F0007")
        )
        self.assertEqual(person.parent_family_ids, ("F0003", "F0001"))
        self.assertEqual(person.family_ids, ("F0009", "F0004", "F0007"))

    def test_event_order_is_preserved(self) -> None:
        first = make_event_ref("E0009")
        second = make_event_ref("E0002")
        person = Person("I0015", "Jean DUPONT", PersonGender.MALE, (first, second), (), ())
        self.assertEqual(person.event_refs, (first, second))

    def test_person_is_immutable(self) -> None:
        person = Person("I0016", "Jean DUPONT", PersonGender.MALE, (), (), ())
        with self.assertRaises(FrozenInstanceError):
            person.display_name = "Pierre DUPONT"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
