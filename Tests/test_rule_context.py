import unittest

from descendants_timeline.inference.rule_context import RuleContext
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender

from dataclasses import FrozenInstanceError

from datetime import date

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    TemporalValue,
    ValueOrigin,
    SourceQuality,
    EvidenceStatus,
    CertaintyLevel,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.model.temporal_target import TemporalOwnerType

class RuleContextTests(unittest.TestCase):

    def test_accepts_empty_evidences(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={},
            root_person_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(),
        )

        self.assertIs(context.data, data)
        self.assertEqual(context.evidences, ())

    def test_rejects_invalid_data(self):
        with self.assertRaises(TypeError):
            RuleContext(
                data="not genealogy data",
                evidences=(),
            )

    def test_rejects_non_tuple_evidences(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={},
            root_person_id="I001",
        )

        with self.assertRaises(TypeError):
            RuleContext(
                data=data,
                evidences=[],
            )

    def test_rejects_invalid_evidence_item(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={},
            root_person_id="I001",
        )

        with self.assertRaises(TypeError):
            RuleContext(
                data=data,
                evidences=("not an evidence",),
            )

    def test_is_immutable(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={},
            root_person_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(),
        )

        with self.assertRaises(FrozenInstanceError):
            context.evidences = ()

    def test_accepts_temporal_evidence(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={},
            root_person_id="I001",
        )

        death_date = TemporalValue(
            source_value="17/08/1872",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1872, 8, 17),
            normalized_maximum=date(1872, 8, 17),
            representative_value=date(1872, 8, 17),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=death_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(evidence,),
        )

        self.assertEqual(context.evidences, (evidence,))
        self.assertIs(context.evidences[0], evidence)

if __name__ == "__main__":
    unittest.main()