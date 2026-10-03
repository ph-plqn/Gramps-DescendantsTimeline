"""Tests du constructeur de l'index des cibles temporelles."""

from __future__ import annotations

import unittest
from datetime import date

from descendants_timeline.inference.temporal_target_index_builder import (
    TemporalTargetIndexBuilder,
)
from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
    PersonEventRef,
)
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
    TemporalTargetAnomalyType,
)
from descendants_timeline.model.temporal_target_index import TemporalTargetIndex

def _gramps_exact_value(
    year: int = 1812,
    month: int = 4,
    day: int = 5,
) -> TemporalValue:
    value = date(year, month, day)

    return TemporalValue(
        source_value=f"{day:02d}/{month:02d}/{year}",
        source_calendar="GREGORIAN",
        normalized_minimum=value,
        normalized_maximum=value,
        representative_value=value,
        value_origin=ValueOrigin.GRAMPS,
        source_quality=SourceQuality.NORMAL,
        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
        certainty=CertaintyLevel.CERTAIN,
    )
def _event(
    event_id: str,
    semantic: EventSemantic,
    temporal_value: TemporalValue | None = None,
) -> Event:
    if temporal_value is None:
        temporal_value = _gramps_exact_value()

    return Event(
        event_id=event_id,
        source_type=semantic.value,
        semantic=semantic,
        date=temporal_value,
    )
def _person_event_ref(
    event_id: str,
    semantic_role: EventRoleSemantic = EventRoleSemantic.PRINCIPAL,
    source_role: str = "PRIMARY",
) -> PersonEventRef:
    return PersonEventRef(
        event_id=event_id,
        semantic_role=semantic_role,
        source_role=source_role,
    )
def _family_event_ref(
    event_id: str,
    semantic_role: FamilyRoleSemantic = FamilyRoleSemantic.FAMILY,
    source_role: str = "FAMILY",
) -> FamilyEventRef:
    return FamilyEventRef(
        event_id=event_id,
        semantic_role=semantic_role,
        source_role=source_role,
    )
def _family(
    family_id: str,
    parent1_id: str | None = None,
    parent2_id: str | None = None,
    event_refs: tuple[FamilyEventRef, ...] = (),
) -> Family:
    return Family(
        family_id=family_id,
        parent1_id=parent1_id,
        parent2_id=parent2_id,
        event_refs=event_refs,
        child_refs=(),
    )
def _person(
    person_id: str,
    event_refs: tuple[PersonEventRef, ...] = (),
) -> Person:
    return Person(
        person_id=person_id,
        display_name=f"Person {person_id}",
        gender=PersonGender.UNKNOWN,
        event_refs=event_refs,
        parent_family_ids=(),
        family_ids=(),
    )
def _genealogy(
    persons: tuple[Person, ...],
    events: tuple[Event, ...] = (),
    families: tuple[Family, ...] = (),
    root_person_id: str | None = None,
) -> RawGenealogyData:
    if root_person_id is None:
        root_person_id = persons[0].person_id

    return RawGenealogyData(
        persons={person.person_id: person for person in persons},
        families={family.family_id: family for family in families},
        events={event.event_id: event for event in events},
        root_person_id=root_person_id,
    )
class TestTemporalTargetIndexBuilder(unittest.TestCase):

    def test_person_birth_target_exists_without_birth_event(self) -> None:
        person = _person("I001")

        data = _genealogy(
            persons=(person,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())
        self.assertEqual(entry.anomalies, ())
        
    def test_person_birth_target_uses_single_principal_birth_event(self) -> None:
        birth_value = _gramps_exact_value(1812, 4, 5)

        birth = _event(
            "E001",
            EventSemantic.BIRTH,
            birth_value,
        )

        person = _person(
            "I001",
            event_refs=(
                _person_event_ref("E001"),
            ),
        )

        data = _genealogy(
            persons=(person,),
            events=(birth,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, birth_value)
        self.assertEqual(entry.anomalies, ())
    def test_person_birth_target_reports_multiple_principal_birth_events(self) -> None:
        birth_1 = _event(
            "E001",
            EventSemantic.BIRTH,
            _gramps_exact_value(1812, 4, 5),
        )

        birth_2 = _event(
            "E002",
            EventSemantic.BIRTH,
            _gramps_exact_value(1825, 7, 12),
        )

        person = _person(
            "I001",
            event_refs=(
                _person_event_ref("E001"),
                _person_event_ref("E002"),
            ),
        )

        data = _genealogy(
            persons=(person,),
            events=(birth_1, birth_2),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())

        self.assertEqual(len(entry.anomalies), 1)

        anomaly = entry.anomalies[0]

        self.assertEqual(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(
            anomaly.event_ids,
            ("E001", "E002"),
        )
    def test_person_death_target_exists_without_death_event(self) -> None:
        person = _person("I001")

        data = _genealogy(
            persons=(person,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())
        self.assertEqual(entry.anomalies, ())
    def test_person_death_target_uses_single_principal_death_event(self) -> None:
        death_value = _gramps_exact_value(1876, 9, 18)

        death = _event(
            "E001",
            EventSemantic.DEATH,
            death_value,
        )

        person = _person(
            "I001",
            event_refs=(
                _person_event_ref("E001"),
            ),
        )

        data = _genealogy(
            persons=(person,),
            events=(death,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, death_value)
        self.assertEqual(entry.anomalies, ())

    def test_person_death_target_reports_multiple_principal_death_events(self) -> None:
        death_1 = _event(
            "E001",
            EventSemantic.DEATH,
            _gramps_exact_value(1812, 4, 5),
        )

        death_2 = _event(
            "E002",
            EventSemantic.DEATH,
            _gramps_exact_value(1825, 7, 12),
        )

        person = _person(
            "I001",
            event_refs=(
                _person_event_ref("E001"),
                _person_event_ref("E002"),
            ),
        )

        data = _genealogy(
            persons=(person,),
            events=(death_1, death_2),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())

        self.assertEqual(len(entry.anomalies), 1)

        anomaly = entry.anomalies[0]

        self.assertEqual(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(
            anomaly.event_ids,
            ("E001", "E002"),
        )
    def test_family_marriage_target_does_not_exist_without_marriage_event(
        self,
    ) -> None:
        person = _person("I001")
        family = _family("F001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        entry = index.get(target)

        self.assertIsNone(entry)
    def test_family_marriage_target_uses_single_family_marriage_event(
        self,
    ) -> None:
        marriage_value = _gramps_exact_value(1850, 6, 15)

        marriage = _event(
            "E001",
            EventSemantic.MARRIAGE,
            marriage_value,
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref("E001"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(marriage,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, marriage_value)
        self.assertEqual(entry.anomalies, ())
    def test_family_marriage_target_reports_multiple_family_marriage_events(
        self,
    ) -> None:
        marriage_1 = _event(
            "E001",
            EventSemantic.MARRIAGE,
            _gramps_exact_value(1850, 6, 15),
        )

        marriage_2 = _event(
            "E002",
            EventSemantic.MARRIAGE,
            _gramps_exact_value(1862, 9, 3),
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref("E001"),
                _family_event_ref("E002"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(marriage_1, marriage_2),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())

        self.assertEqual(len(entry.anomalies), 1)

        anomaly = entry.anomalies[0]

        self.assertEqual(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(
            anomaly.event_ids,
            ("E001", "E002"),
        )
    def test_family_divorce_target_does_not_exist_without_divorce_event(
        self,
    ) -> None:
        person = _person("I001")
        family = _family("F001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        entry = index.get(target)

        self.assertIsNone(entry)
    def test_family_divorce_target_uses_single_family_divorce_event(
        self,
    ) -> None:
        divorce_value = _gramps_exact_value(1860, 3, 12)

        divorce = _event(
            "E001",
            EventSemantic.DIVORCE,
            divorce_value,
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref("E001"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(divorce,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, divorce_value)
        self.assertEqual(entry.anomalies, ())
    def test_family_divorce_target_reports_multiple_family_divorce_events(
        self,
    ) -> None:
        divorce_1 = _event(
            "E001",
            EventSemantic.DIVORCE,
            _gramps_exact_value(1860, 3, 12),
        )

        divorce_2 = _event(
            "E002",
            EventSemantic.DIVORCE,
            _gramps_exact_value(1865, 8, 20),
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref("E001"),
                _family_event_ref("E002"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(divorce_1, divorce_2),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())

        self.assertEqual(len(entry.anomalies), 1)

        anomaly = entry.anomalies[0]

        self.assertEqual(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(
            anomaly.event_ids,
            ("E001", "E002"),
        )
    def test_person_birth_target_ignores_birth_event_when_person_is_witness(
        self,
    ) -> None:
        birth = _event(
            "E001",
            EventSemantic.BIRTH,
            _gramps_exact_value(1812, 4, 5),
        )

        person = _person(
            "I001",
            event_refs=(
                _person_event_ref(
                    "E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="WITNESS",
                ),
            ),
        )

        data = _genealogy(
            persons=(person,),
            events=(birth,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        entry = index.get(target)

        self.assertIsNotNone(entry)
        self.assertEqual(entry.target, target)
        self.assertEqual(entry.gramps_value, TemporalValue.unknown())
        self.assertEqual(entry.anomalies, ())
    def test_family_target_ignores_event_referenced_by_another_family(
        self,
    ) -> None:
        marriage = _event(
            "E001",
            EventSemantic.MARRIAGE,
            _gramps_exact_value(1812, 4, 5),
        )

        family_1 = _family("F001")

        family_2 = _family(
            "F002",
            event_refs=(
                _family_event_ref("E001"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family_1, family_2),
            events=(marriage,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target_f001 = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        target_f002 = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F002",
            semantic=TargetSemantic.MARRIAGE,
        )

        entry_f001 = index.get(target_f001)
        entry_f002 = index.get(target_f002)

        self.assertIsNone(entry_f001)

        self.assertIsNotNone(entry_f002)
        self.assertEqual(entry_f002.target, target_f002)
        self.assertEqual(
            entry_f002.gramps_value,
            marriage.date,
        )
        self.assertEqual(entry_f002.anomalies, ())
    def test_family_marriage_target_ignores_non_marriage_event(
        self,
    ) -> None:
        divorce = _event(
            "E001",
            EventSemantic.DIVORCE,
            _gramps_exact_value(1860, 3, 12),
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref("E001"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(divorce,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        marriage_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        divorce_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        marriage_entry = index.get(marriage_target)
        divorce_entry = index.get(divorce_target)

        self.assertIsNone(marriage_entry)

        self.assertIsNotNone(divorce_entry)
        self.assertEqual(divorce_entry.target, divorce_target)
        self.assertEqual(
            divorce_entry.gramps_value,
            divorce.date,
        )
        self.assertEqual(divorce_entry.anomalies, ())
    def test_family_target_ignores_non_family_event_semantic(
        self,
    ) -> None:
        birth = _event(
            "E001",
            EventSemantic.BIRTH,
            _gramps_exact_value(1812, 4, 5),
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref("E001"),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(birth,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        marriage_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        divorce_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        marriage_entry = index.get(marriage_target)
        divorce_entry = index.get(divorce_target)

        self.assertIsNone(marriage_entry)
        self.assertIsNone(divorce_entry)
    def test_family_marriage_target_ignores_event_when_family_role_is_unknown(
        self,
    ) -> None:
        marriage = _event(
            "E001",
            EventSemantic.MARRIAGE,
            _gramps_exact_value(1850, 6, 15),
        )

        family = _family(
            "F001",
            event_refs=(
                _family_event_ref(
                    "E001",
                    semantic_role=FamilyRoleSemantic.UNKNOWN,
                    source_role="UNKNOWN",
                ),
            ),
        )

        person = _person("I001")

        data = _genealogy(
            persons=(person,),
            families=(family,),
            events=(marriage,),
        )

        index = TemporalTargetIndexBuilder().build(data)

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        entry = index.get(target)

        self.assertIsNone(entry)
    def test_build_rejects_non_raw_genealogy_data(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "data doit être un RawGenealogyData.",
        ):
            TemporalTargetIndexBuilder().build(None)