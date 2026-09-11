import unittest
from datetime import date

from descendants_timeline.inference.event_reference_index import (
    EventReferenceIndex,
)
from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.family import Family
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
    PersonEventRef,
)
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_evidence import EvidenceOwnerType
from descendants_timeline.inference.event_reference_index import (
    EventReferenceIndex,
    _EventReferenceEntry,
)

class TestEventReferenceIndex(unittest.TestCase):

    def test_indexes_person_event_reference(self):
        event = Event(
            event_id="E1234",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue.unknown(),
        )

        event_ref = PersonEventRef(
            event_id="E1234",
            semantic_role=EventRoleSemantic.PRINCIPAL,
            source_role="Primary",
        )

        person = Person(
            person_id="I_JOSEPH",
            display_name="Joseph",
            gender=PersonGender.MALE,
            event_refs=(event_ref,),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I_JOSEPH": person},
            families={},
            events={"E1234": event},
            root_person_id="I_JOSEPH",
        )
        index = EventReferenceIndex.from_data(data)
        references = index.get("E1234")
        self.assertEqual(len(references), 1)
        self.assertEqual(
            references[0].owner_type,
            EvidenceOwnerType.PERSON,
        )
        self.assertEqual(
        references[0].owner_id,
        "I_JOSEPH",
        )
        self.assertEqual(
        references[0].role,
        EventRoleSemantic.PRINCIPAL,
        )
    def test_indexes_multiple_person_references_to_same_event(self):
        event = Event(
            event_id="E1234",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue.unknown(),
        )

        joseph_event_ref = PersonEventRef(
            event_id="E1234",
            semantic_role=EventRoleSemantic.PRINCIPAL,
            source_role="Primary",
        )

        victor_event_ref = PersonEventRef(
            event_id="E1234",
            semantic_role=EventRoleSemantic.WITNESS,
            source_role="Witness",
        )
        joseph = Person(
            person_id="I_JOSEPH",
            display_name="Joseph",
            gender=PersonGender.MALE,
            event_refs=(joseph_event_ref,),
            parent_family_ids=(),
            family_ids=(),
        )

        victor = Person(
            person_id="I_VICTOR",
            display_name="Victor",
            gender=PersonGender.MALE,
            event_refs=(victor_event_ref,),
            parent_family_ids=(),
            family_ids=(),
        )
        data = RawGenealogyData(
            persons={
                "I_JOSEPH": joseph,
                "I_VICTOR": victor,
            },
            families={},
            events={"E1234": event},
            root_person_id="I_JOSEPH",
        )
        index = EventReferenceIndex.from_data(data)
        references = index.get("E1234")

        self.assertEqual(len(references), 2)
        self.assertEqual(
            references[0].owner_type,
            EvidenceOwnerType.PERSON,
        )
        self.assertEqual(
            references[0].owner_id,
            "I_JOSEPH",
        )
        self.assertEqual(
            references[0].role,
            EventRoleSemantic.PRINCIPAL,
        )

        self.assertEqual(
            references[1].owner_type,
            EvidenceOwnerType.PERSON,
        )
        self.assertEqual(
            references[1].owner_id,
            "I_VICTOR",
        )
        self.assertEqual(
            references[1].role,
            EventRoleSemantic.WITNESS,
        )
    def test_indexes_family_event_reference(self):
        event = Event(
            event_id="E2000",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue.unknown(),
        )
        family_event_ref = FamilyEventRef(
            event_id="E2000",
            semantic_role=FamilyRoleSemantic.FAMILY,
            source_role="Family",
        )
        family = Family(
            family_id="F0010",
            parent1_id=None,
            parent2_id=None,
            event_refs=(family_event_ref,),
            child_refs=(),
        )
        person = Person(
            person_id="I_ROOT",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F0010",),
        )

        data = RawGenealogyData(
            persons={"I_ROOT": person},
            families={"F0010": family},
            events={"E2000": event},
            root_person_id="I_ROOT",
        )
        index = EventReferenceIndex.from_data(data)
        references = index.get("E2000")

        self.assertEqual(len(references), 1)
        self.assertEqual(
            references[0].owner_type,
            EvidenceOwnerType.FAMILY,
        )

        self.assertEqual(
            references[0].owner_id,
            "F0010",
        )

        self.assertEqual(
            references[0].role,
            FamilyRoleSemantic.FAMILY,
        )
    def test_indexes_person_and_family_references_to_same_event(self):
        event = Event(
            event_id="E3000",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue.unknown(),
        )
        jean_event_ref = PersonEventRef(
            event_id="E3000",
            semantic_role=EventRoleSemantic.PRINCIPAL,
            source_role="Primary",
        )

        marie_event_ref = PersonEventRef(
            event_id="E3000",
            semantic_role=EventRoleSemantic.PRINCIPAL,
            source_role="Primary",
        )

        family_event_ref = FamilyEventRef(
            event_id="E3000",
            semantic_role=FamilyRoleSemantic.FAMILY,
            source_role="Family",
        )
        jean = Person(
            person_id="I_JEAN",
            display_name="Jean",
            gender=PersonGender.MALE,
            event_refs=(jean_event_ref,),
            parent_family_ids=(),
            family_ids=("F0020",),
        )

        marie = Person(
            person_id="I_MARIE",
            display_name="Marie",
            gender=PersonGender.FEMALE,
            event_refs=(marie_event_ref,),
            parent_family_ids=(),
            family_ids=("F0020",),
        )

        family = Family(
            family_id="F0020",
            parent1_id="I_JEAN",
            parent2_id="I_MARIE",
            event_refs=(family_event_ref,),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons={
                "I_JEAN": jean,
                "I_MARIE": marie,
            },
            families={
                "F0020": family,
            },
            events={
                "E3000": event,
            },
            root_person_id="I_JEAN",
        )
        index = EventReferenceIndex.from_data(data)
        references = index.get("E3000")
        
        self.assertEqual(len(references), 3)
        self.assertEqual(
            references[0].owner_type,
            EvidenceOwnerType.PERSON,
        )
        
        self.assertEqual(
            references[0].owner_id,
            "I_JEAN",
        )
        
        self.assertEqual(
            references[0].role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            references[1].owner_type,
            EvidenceOwnerType.PERSON,
        )
                
        self.assertEqual(
            references[1].owner_id,
            "I_MARIE",
        )
                
        self.assertEqual(
            references[1].role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            references[2].owner_type,
            EvidenceOwnerType.FAMILY,
        )
                
        self.assertEqual(
            references[2].owner_id,
            "F0020",
        )
                
        self.assertEqual(
            references[2].role,
            FamilyRoleSemantic.FAMILY,
        )
    def test_get_returns_empty_tuple_for_unknown_event(self):
        event = Event(
            event_id="E1234",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue.unknown(),
        )

        person = Person(
            person_id="I_JOSEPH",
            display_name="Joseph",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I_JOSEPH": person},
            families={},
            events={"E1234": event},
            root_person_id="I_JOSEPH",
        )

        index = EventReferenceIndex.from_data(data)

        references = index.get("E_INEXISTANT")

        self.assertEqual(references, ())
    def test_get_rejects_empty_event_id(self):
        index = EventReferenceIndex(
            _references={}
        )

        with self.assertRaises(ValueError):
            index.get("")
    def test_get_rejects_whitespace_event_id(self):
        index = EventReferenceIndex(
            _references={}
        )

        with self.assertRaises(ValueError):
            index.get("   ")
    def test_get_rejects_none_event_id(self):
        index = EventReferenceIndex(
            _references={}
        )

        with self.assertRaises(ValueError):
            index.get(None)
    def test_direct_construction__protects_against_external_mutation(self):
        mutable_references = {}

        index = EventReferenceIndex(
            _references=mutable_references
        )

        mutable_references["E9999"] = ()

        self.assertNotIn("E9999", index._references)
    def test_preserves_unknown_person_event_role(self):
        event = Event(
            event_id="E4000",
            source_type="Custom",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue.unknown(),
        )

        event_ref = PersonEventRef(
            event_id="E4000",
            semantic_role=EventRoleSemantic.UNKNOWN,
            source_role="Unknown",
        )

        person = Person(
            person_id="I_TEST",
            display_name="Test",
            gender=PersonGender.UNKNOWN,
            event_refs=(event_ref,),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I_TEST": person},
            families={},
            events={"E4000": event},
            root_person_id="I_TEST",
        )

        index = EventReferenceIndex.from_data(data)
        references = index.get("E4000")

        self.assertEqual(len(references), 1)
        self.assertEqual(
            references[0].role,
        EventRoleSemantic.UNKNOWN,
        )
    def test_direct_construction_protects_against_mutable_entry_list(self):
        entry = _EventReferenceEntry(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I_JOSEPH",
            role=EventRoleSemantic.PRINCIPAL,
        )

        mutable_entries = [entry]

        index = EventReferenceIndex(
            _references={"E1234": mutable_entries}
        )

        mutable_entries.clear()

        self.assertEqual(len(index.get("E1234")), 1)