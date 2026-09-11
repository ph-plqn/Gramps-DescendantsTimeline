import unittest

from descendants_timeline.inference.temporal_evidence_builder import (
    TemporalEvidenceBuilder,
)
from datetime import date

from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import (
    PersonEventRef,
    EventRoleSemantic,
)
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.temporal import (
    TemporalValue,
    ValueOrigin,
    SourceQuality,
    EvidenceStatus,
    CertaintyLevel,
)
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.model.temporal_evidence import EvidenceOwnerType
from descendants_timeline.model.temporal_target import TemporalOwnerType

class TestTemporalEvidenceBuilder(unittest.TestCase):

    def test_build_rejects_invalid_data(self):
        with self.assertRaises(TypeError):
            TemporalEvidenceBuilder.build(None)

    def test_build_birth_principal_creates_one_evidence(self):
        birth_date = TemporalValue(
            source_value="01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1850, 1, 1),
            representative_value=date(1850, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=birth_date,
        )

        person = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(evidence.owner_id, "I001")
        self.assertEqual(evidence.event_id, "E001")
        self.assertEqual(evidence.semantic, EventSemantic.BIRTH)
        self.assertEqual(evidence.role, EventRoleSemantic.PRINCIPAL)
        self.assertEqual(evidence.principal_owner_id, "I001")

    def test_build_birth_without_principal_returns_no_evidence(self):
        birth_date = TemporalValue(
            source_value="01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1850, 1, 1),
            representative_value=date(1850, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=birth_date,
        )

        person = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="Witness",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

    def test_build_birth_with_two_principals_returns_no_evidence(self):
        birth_date = TemporalValue(
            source_value="01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1850, 1, 1),
            representative_value=date(1850, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=birth_date,
        )

        person1 = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        person2 = Person(
            person_id="I002",
            display_name="Pierre TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

    def test_build_birth_with_unusable_date_returns_no_evidence(self):
        birth_date = TemporalValue(
            source_value="01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1850, 1, 1),
            representative_value=date(1850, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.CALCULATED,
            evidence_status=EvidenceStatus.EVIDENCE_UNPROVEN,
            certainty=CertaintyLevel.UNDETERMINED,
        )

        event = Event(
            event_id="E001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=birth_date,
        )

        person = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

    def test_build_birth_with_witness_creates_two_evidences(self):
        birth_date = TemporalValue(
            source_value="01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1850, 1, 1),
            representative_value=date(1850, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=birth_date,
        )

        child = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        witness = Person(
            person_id="I002",
            display_name="Victor TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="Witness",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": child,
                "I002": witness,
            },
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 2)

        principal_evidence = evidences[0]
        witness_evidence = evidences[1]

        self.assertEqual(principal_evidence.owner_id, "I001")
        self.assertEqual(
            principal_evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            principal_evidence.principal_owner_id,
            "I001",
        )

        self.assertEqual(witness_evidence.owner_id, "I002")
        self.assertEqual(
            witness_evidence.role,
            EventRoleSemantic.WITNESS,
        )
        self.assertEqual(
            witness_evidence.principal_owner_id,
            "I001",
        )
    
    def test_build_birth_with_informant_creates_two_evidences(self):
        birth_date = TemporalValue(
            source_value="01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1850, 1, 1),
            representative_value=date(1850, 1, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Birth",
            semantic=EventSemantic.BIRTH,
            date=birth_date,
        )

        child = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        informant = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.INFORMANT,
                    source_role="Informant",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": child,
                "I002": informant,
            },
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 2)

        principal_evidence = evidences[0]
        informant_evidence = evidences[1]

        self.assertEqual(principal_evidence.owner_id, "I001")
        self.assertEqual(
            principal_evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            principal_evidence.principal_owner_id,
            "I001",
        )

        self.assertEqual(informant_evidence.owner_id, "I002")
        self.assertEqual(
            informant_evidence.role,
            EventRoleSemantic.INFORMANT,
        )
        self.assertEqual(
            informant_evidence.principal_owner_id,
            "I001",
        )

    def test_build_baptism_principal_creates_one_evidence(self):
        baptism_date = TemporalValue(
            source_value="15/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 15),
            normalized_maximum=date(1850, 1, 15),
            representative_value=date(1850, 1, 15),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Baptism",
            semantic=EventSemantic.BAPTISM,
            date=baptism_date,
        )

        person = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(evidence.owner_id, "I001")
        self.assertEqual(evidence.event_id, "E001")
        self.assertEqual(evidence.semantic, EventSemantic.BAPTISM)
        self.assertEqual(
            evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "I001",
        )
    def test_build_death_principal_creates_one_evidence(self):
        death_date = TemporalValue(
            source_value="20/06/1900",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1900, 6, 20),
            normalized_maximum=date(1900, 6, 20),
            representative_value=date(1900, 6, 20),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Death",
            semantic=EventSemantic.DEATH,
            date=death_date,
        )

        person = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(evidence.owner_id, "I001")
        self.assertEqual(evidence.event_id, "E001")
        self.assertEqual(evidence.semantic, EventSemantic.DEATH)
        self.assertEqual(
            evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "I001",
        )

    def test_build_burial_principal_creates_one_evidence(self):
        burial_date = TemporalValue(
            source_value="23/06/1900",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1900, 6, 23),
            normalized_maximum=date(1900, 6, 23),
            representative_value=date(1900, 6, 23),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Burial",
            semantic=EventSemantic.BURIAL,
            date=burial_date,
        )

        person = Person(
            person_id="I001",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(evidence.owner_id, "I001")
        self.assertEqual(evidence.event_id, "E001")
        self.assertEqual(evidence.semantic, EventSemantic.BURIAL)
        self.assertEqual(
            evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "I001",
        )
    def test_build_marriage_family_creates_one_evidence(self):
        marriage_date = TemporalValue(
            source_value="10/05/1875",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1875, 5, 10),
            normalized_maximum=date(1875, 5, 10),
            representative_value=date(1875, 5, 10),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_date,
        )

        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(
                FamilyEventRef(
                    event_id="E001",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="Family",
                ),
            ),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={"F001": family},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(
            evidence.owner_type,
            EvidenceOwnerType.FAMILY,
        )
        self.assertEqual(evidence.owner_id, "F001")
        self.assertEqual(evidence.event_id, "E001")
        self.assertEqual(
            evidence.semantic,
            EventSemantic.MARRIAGE,
        )
        self.assertEqual(
            evidence.role,
            FamilyRoleSemantic.FAMILY,
        )
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.FAMILY,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "F001",
        )
    def test_build_marriage_with_witness_creates_two_evidences(self):
        marriage_date = TemporalValue(
            source_value="10/05/1875",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1875, 5, 10),
            normalized_maximum=date(1875, 5, 10),
            representative_value=date(1875, 5, 10),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_date,
        )

        spouse1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        spouse2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        witness = Person(
            person_id="I003",
            display_name="Victor TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="Witness",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(
                FamilyEventRef(
                    event_id="E001",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="Family",
                ),
            ),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": spouse1,
                "I002": spouse2,
                "I003": witness,
            },
            families={"F001": family},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 2)

        family_evidence = next(
            evidence
            for evidence in evidences
            if (
                evidence.owner_type is EvidenceOwnerType.FAMILY
                and evidence.owner_id == "F001"
            )
        )

        witness_evidence = next(
            evidence
            for evidence in evidences
            if (
                evidence.owner_type is EvidenceOwnerType.PERSON
                and evidence.owner_id == "I003"
            )
        )

        self.assertEqual(
            family_evidence.owner_type,
            EvidenceOwnerType.FAMILY,
        )
        self.assertEqual(family_evidence.owner_id, "F001")
        self.assertEqual(
            family_evidence.role,
            FamilyRoleSemantic.FAMILY,
        )
        self.assertEqual(
            family_evidence.principal_owner_type,
            TemporalOwnerType.FAMILY,
        )
        self.assertEqual(
            family_evidence.principal_owner_id,
            "F001",
        )

        self.assertEqual(
            witness_evidence.owner_type,
            EvidenceOwnerType.PERSON,
        )
        self.assertEqual(witness_evidence.owner_id, "I003")
        self.assertEqual(
            witness_evidence.role,
            EventRoleSemantic.WITNESS,
        )
        self.assertEqual(
            witness_evidence.principal_owner_type,
            TemporalOwnerType.FAMILY,
        )
        self.assertEqual(
            witness_evidence.principal_owner_id,
            "F001",
        )

    def test_build_marriage_with_informant_creates_two_evidences(self):
            marriage_date = TemporalValue(
                source_value="10/05/1875",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1875, 5, 10),
                normalized_maximum=date(1875, 5, 10),
                representative_value=date(1875, 5, 10),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            )

            event = Event(
                event_id="E001",
                source_type="Marriage",
                semantic=EventSemantic.MARRIAGE,
                date=marriage_date,
            )

            spouse1 = Person(
                person_id="I001",
                display_name="Joseph TEST",
                gender=PersonGender.MALE,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F001",),
            )

            spouse2 = Person(
                person_id="I002",
                display_name="Marie TEST",
                gender=PersonGender.FEMALE,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F001",),
            )

            informant = Person(
                person_id="I004",
                display_name="Carlos TEST",
                gender=PersonGender.MALE,
                event_refs=(
                    PersonEventRef(
                        event_id="E001",
                        semantic_role=EventRoleSemantic.INFORMANT,
                        source_role="Informant",
                    ),
                ),
                parent_family_ids=(),
                family_ids=(),
            )

            family = Family(
                family_id="F001",
                parent1_id="I001",
                parent2_id="I002",
                event_refs=(
                    FamilyEventRef(
                        event_id="E001",
                        semantic_role=FamilyRoleSemantic.FAMILY,
                        source_role="Family",
                    ),
                ),
                child_refs=(),
            )

            data = RawGenealogyData(
                persons={
                    "I001": spouse1,
                    "I002": spouse2,
                    "I004": informant,
                },
                families={"F001": family},
                events={"E001": event},
                root_person_id="I001",
            )

            evidences = TemporalEvidenceBuilder.build(data)

            self.assertEqual(len(evidences), 2)

            family_evidence = next(
                evidence
                for evidence in evidences
                if (
                    evidence.owner_type is EvidenceOwnerType.FAMILY
                    and evidence.owner_id == "F001"
                )
            )

            informant_evidence = next(
                evidence
                for evidence in evidences
                if (
                    evidence.owner_type is EvidenceOwnerType.PERSON
                    and evidence.owner_id == "I004"
                )
            )

            self.assertEqual(
                family_evidence.owner_type,
                EvidenceOwnerType.FAMILY,
            )
            self.assertEqual(family_evidence.owner_id, "F001")
            self.assertEqual(
                family_evidence.role,
                FamilyRoleSemantic.FAMILY,
            )
            self.assertEqual(
                family_evidence.principal_owner_type,
                TemporalOwnerType.FAMILY,
            )
            self.assertEqual(
                family_evidence.principal_owner_id,
                "F001",
            )

            self.assertEqual(
                informant_evidence.owner_type,
                EvidenceOwnerType.PERSON,
            )
            self.assertEqual(informant_evidence.owner_id, "I004")
            self.assertEqual(
                informant_evidence.role,
                EventRoleSemantic.INFORMANT,
            )
            self.assertEqual(
                informant_evidence.principal_owner_type,
                TemporalOwnerType.FAMILY,
            )
            self.assertEqual(
                informant_evidence.principal_owner_id,
                "F001",
            )
    def test_build_marriage_without_family_principal_creates_no_evidence(self):
        marriage_date = TemporalValue(
            source_value="10/05/1875",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1875, 5, 10),
            normalized_maximum=date(1875, 5, 10),
            representative_value=date(1875, 5, 10),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_date,
        )

        spouse1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        spouse2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        witness = Person(
            person_id="I003",
            display_name="Victor TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="Witness",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": spouse1,
                "I002": spouse2,
                "I003": witness,
            },
            families={"F001": family},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

    def test_build_marriage_with_two_family_principals_creates_no_evidence(self):
        marriage_date = TemporalValue(
            source_value="10/05/1875",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1875, 5, 10),
            normalized_maximum=date(1875, 5, 10),
            representative_value=date(1875, 5, 10),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_date,
        )

        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person3 = Person(
            person_id="I003",
            display_name="Paul TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F002",),
        )

        person4 = Person(
            person_id="I004",
            display_name="Anne TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F002",),
        )

        family1 = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(
                FamilyEventRef(
                    event_id="E001",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="Family",
                ),
            ),
            child_refs=(),
        )

        family2 = Family(
            family_id="F002",
            parent1_id="I003",
            parent2_id="I004",
            event_refs=(
                FamilyEventRef(
                    event_id="E001",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="Family",
                ),
            ),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
                "I003": person3,
                "I004": person4,
            },
            families={
                "F001": family1,
                "F002": family2,
            },
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

    def test_build_marriage_person_principal_is_ignored(self):
        marriage_date = TemporalValue(
            source_value="10/05/1875",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1875, 5, 10),
            normalized_maximum=date(1875, 5, 10),
            representative_value=date(1875, 5, 10),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Marriage",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_date,
        )

        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Principal",
                ),
            ),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(
                FamilyEventRef(
                    event_id="E001",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="Family",
                ),
            ),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={"F001": family},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(
            evidence.owner_type,
            EvidenceOwnerType.FAMILY,
        )
        self.assertEqual(evidence.owner_id, "F001")
        self.assertEqual(
            evidence.role,
            FamilyRoleSemantic.FAMILY,
        )
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.FAMILY,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "F001",
        )

    def test_build_divorce_family_creates_one_evidence(self):
        divorce_date = TemporalValue(
            source_value="20/09/1885",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1885, 9, 20),
            normalized_maximum=date(1885, 9, 20),
            representative_value=date(1885, 9, 20),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Divorce",
            semantic=EventSemantic.DIVORCE,
            date=divorce_date,
        )

        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(
                FamilyEventRef(
                    event_id="E001",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="Family",
                ),
            ),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={"F001": family},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(
            evidence.owner_type,
            EvidenceOwnerType.FAMILY,
        )
        self.assertEqual(evidence.owner_id, "F001")
        self.assertEqual(
            evidence.event_id,
            "E001",
        )
        self.assertEqual(
            evidence.semantic,
            EventSemantic.DIVORCE,
        )
        self.assertEqual(
            evidence.role,
            FamilyRoleSemantic.FAMILY,
        )
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.FAMILY,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "F001",
        )

    def test_build_divorce_with_witness_creates_two_evidences(self):
            divorce_date = TemporalValue(
                source_value="20/09/1885",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1885, 9, 20),
                normalized_maximum=date(1885, 9, 20),
                representative_value=date(1885, 9, 20),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            )

            event = Event(
                event_id="E001",
                source_type="Divorce",
                semantic=EventSemantic.DIVORCE,
                date=divorce_date,
            )
    
            spouse1 = Person(
                person_id="I001",
                display_name="Joseph TEST",
                gender=PersonGender.MALE,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F001",),
            )
    
            spouse2 = Person(
                person_id="I002",
                display_name="Marie TEST",
                gender=PersonGender.FEMALE,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F001",),
            )
    
            witness = Person(
                person_id="I003",
                display_name="Victor TEST",
                gender=PersonGender.MALE,
                event_refs=(
                    PersonEventRef(
                        event_id="E001",
                        semantic_role=EventRoleSemantic.WITNESS,
                        source_role="Witness",
                    ),
                ),
                parent_family_ids=(),
                family_ids=(),
            )
    
            family = Family(
                family_id="F001",
                parent1_id="I001",
                parent2_id="I002",
                event_refs=(
                    FamilyEventRef(
                        event_id="E001",
                        semantic_role=FamilyRoleSemantic.FAMILY,
                        source_role="Family",
                    ),
                ),
                child_refs=(),
            )
    
            data = RawGenealogyData(
                persons={
                    "I001": spouse1,
                    "I002": spouse2,
                    "I003": witness,
                },
                families={"F001": family},
                events={"E001": event},
                root_person_id="I001",
            )
    
            evidences = TemporalEvidenceBuilder.build(data)
    
            self.assertEqual(len(evidences), 2)
    
            family_evidence = next(
                evidence
                for evidence in evidences
                if (
                    evidence.owner_type is EvidenceOwnerType.FAMILY
                    and evidence.owner_id == "F001"
                )
            )
    
            witness_evidence = next(
                evidence
                for evidence in evidences
                if (
                    evidence.owner_type is EvidenceOwnerType.PERSON
                    and evidence.owner_id == "I003"
                )
            )
    
            self.assertEqual(
                family_evidence.owner_type,
                EvidenceOwnerType.FAMILY,
            )
            self.assertEqual(family_evidence.owner_id, "F001")
            self.assertEqual(
                family_evidence.role,
                FamilyRoleSemantic.FAMILY,
            )
            self.assertEqual(
                family_evidence.principal_owner_type,
                TemporalOwnerType.FAMILY,
            )
            self.assertEqual(
                family_evidence.principal_owner_id,
                "F001",
            )
    
            self.assertEqual(
                witness_evidence.owner_type,
                EvidenceOwnerType.PERSON,
            )
            self.assertEqual(witness_evidence.owner_id, "I003")
            self.assertEqual(
                witness_evidence.role,
                EventRoleSemantic.WITNESS,
            )
            self.assertEqual(
                witness_evidence.principal_owner_type,
                TemporalOwnerType.FAMILY,
            )
            self.assertEqual(
                witness_evidence.principal_owner_id,
                "F001",
            )
            self.assertEqual(len(evidences), 2)

            self.assertEqual(
                family_evidence.semantic,
                EventSemantic.DIVORCE,
            )

            self.assertEqual(
                witness_evidence.semantic,
                EventSemantic.DIVORCE,
            )

            self.assertEqual(
                witness_evidence.role,
                EventRoleSemantic.WITNESS,
            )

            self.assertEqual(
                witness_evidence.principal_owner_type,
                TemporalOwnerType.FAMILY,
            )

            self.assertEqual(
                witness_evidence.principal_owner_id,
                "F001",
            )
    def test_build_census_principal_creates_one_evidence(self):
        census_date = TemporalValue(
            source_value="01/06/1823",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1823, 6, 1),
            normalized_maximum=date(1823, 6, 1),
            representative_value=date(1823, 6, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Census",
            semantic=EventSemantic.CENSUS,
            date=census_date,
        )

        person = Person(
            person_id="I001",
            display_name="Edgard ELLA",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(
            evidence.owner_type,
            EvidenceOwnerType.PERSON,
        )
        self.assertEqual(evidence.owner_id, "I001")
        self.assertEqual(evidence.event_id, "E001")
        self.assertEqual(
            evidence.semantic,
            EventSemantic.CENSUS,
        )
        self.assertEqual(
            evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.PERSON,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "I001",
        )

    def test_build_census_witness_is_ignored(self):
        census_date = TemporalValue(
            source_value="01/06/1823",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1823, 6, 1),
            normalized_maximum=date(1823, 6, 1),
            representative_value=date(1823, 6, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Census",
            semantic=EventSemantic.CENSUS,
            date=census_date,
        )

        principal = Person(
            person_id="I001",
            display_name="Edgard ELLA",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        witness = Person(
            person_id="I002",
            display_name="Victor TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="Witness",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": principal,
                "I002": witness,
            },
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(len(evidences), 1)

        evidence = evidences[0]

        self.assertEqual(
            evidence.owner_type,
            EvidenceOwnerType.PERSON,
        )
        self.assertEqual(evidence.owner_id, "I001")
        self.assertEqual(
            evidence.semantic,
            EventSemantic.CENSUS,
        )
        self.assertEqual(
            evidence.role,
            EventRoleSemantic.PRINCIPAL,
        )
        self.assertEqual(
            evidence.principal_owner_type,
            TemporalOwnerType.PERSON,
        )
        self.assertEqual(
            evidence.principal_owner_id,
            "I001",
        )

    def test_build_census_without_principal_creates_no_evidence(self):
        census_date = TemporalValue(
            source_value="01/06/1823",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1823, 6, 1),
            normalized_maximum=date(1823, 6, 1),
            representative_value=date(1823, 6, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Census",
            semantic=EventSemantic.CENSUS,
            date=census_date,
        )

        witness = Person(
            person_id="I002",
            display_name="Victor TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.WITNESS,
                    source_role="Witness",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I002": witness},
            families={},
            events={"E001": event},
            root_person_id="I002",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

    def test_build_census_with_two_principals_creates_no_evidence(self):
        census_date = TemporalValue(
            source_value="01/06/1823",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1823, 6, 1),
            normalized_maximum=date(1823, 6, 1),
            representative_value=date(1823, 6, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        event = Event(
            event_id="E001",
            source_type="Census",
            semantic=EventSemantic.CENSUS,
            date=census_date,
        )

        person1 = Person(
            person_id="I001",
            display_name="Edgard ELLA",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        person2 = Person(
            person_id="I002",
            display_name="Victor TEST",
            gender=PersonGender.MALE,
            event_refs=(
                PersonEventRef(
                    event_id="E001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="Primary",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={},
            events={"E001": event},
            root_person_id="I001",
        )

        evidences = TemporalEvidenceBuilder.build(data)

        self.assertEqual(evidences, ())

if __name__ == "__main__":
    unittest.main()