import unittest
from datetime import date

from descendants_timeline.inference.birth_before_baptism_rule import (
    BirthBeforeBaptismRule,
)
from descendants_timeline.inference.rule_context import RuleContext

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    TemporalValue,
    ValueOrigin,
    SourceQuality,
    EvidenceStatus,
    CertaintyLevel,
)
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)


class BirthBeforeBaptismRuleTests(unittest.TestCase):

    def setUp(self):
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

        self.context = RuleContext(
            data=data,
            evidences=(),
        )

        self.rule = BirthBeforeBaptismRule()

    def make_baptism_evidence(
        self,
        event_id,
        minimum,
        maximum,
        owner_id="I001",
        role=EventRoleSemantic.PRINCIPAL,
        principal_owner_id="I001",
    ):
        baptism_date = TemporalValue(
            source_value="test",
            source_calendar="GREGORIAN",
            normalized_minimum=minimum,
            normalized_maximum=maximum,
            representative_value=(
                minimum if minimum is not None and minimum == maximum else None
            ),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        return TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id=owner_id,
            event_id=event_id,
            semantic=EventSemantic.BAPTISM,
            role=role,
            date=baptism_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id=principal_owner_id,
        )

    def birth_target(self):
        return TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

    def test_is_applicable_to_person_birth(self):
        self.assertTrue(
            self.rule.is_applicable(
                self.birth_target(),
                self.context,
            )
        )

    def test_is_not_applicable_to_person_death(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        self.assertFalse(
            self.rule.is_applicable(target, self.context)
        )

    def test_evaluate_without_baptism_returns_empty(self):
        constraints = self.rule.evaluate(
            self.birth_target(),
            self.context,
        )

        self.assertEqual(constraints, ())

    def test_evaluate_birth_from_baptism(self):
        evidence = self.make_baptism_evidence(
            "E001",
            date(1841, 8, 17),
            date(1841, 8, 19),
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(len(constraints), 1)

        constraint = constraints[0]

        self.assertIs(
            constraint.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1841, 8, 19),
        )
        self.assertEqual(
            constraint.rule_id,
            "BIRTH_BEFORE_BAPTISM",
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )
        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_multiple_baptisms_produce_multiple_constraints(self):
        evidence_1 = self.make_baptism_evidence(
            "E001",
            date(1801, 1, 10),
            date(1801, 1, 10),
        )

        evidence_2 = self.make_baptism_evidence(
            "E002",
            date(1840, 6, 15),
            date(1840, 6, 15),
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(evidence_1, evidence_2),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(len(constraints), 2)

        self.assertEqual(
            constraints[0].bound,
            date(1801, 1, 10),
        )
        self.assertEqual(
            constraints[1].bound,
            date(1840, 6, 15),
        )

        self.assertEqual(
            constraints[0].evidences,
            (evidence_1,),
        )
        self.assertEqual(
            constraints[1].evidences,
            (evidence_2,),
        )

    def test_ignores_baptism_of_another_person(self):
        evidence = self.make_baptism_evidence(
            "E001",
            date(1841, 8, 17),
            date(1841, 8, 17),
            owner_id="I002",
            principal_owner_id="I002",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_ignores_baptism_witness(self):
        evidence = self.make_baptism_evidence(
            "E001",
            date(1841, 8, 17),
            date(1841, 8, 17),
            role=EventRoleSemantic.WITNESS,
            principal_owner_id="I002",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_ignores_baptism_without_upper_bound(self):
        evidence = self.make_baptism_evidence(
            "E001",
            date(1841, 8, 19),
            None,
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(constraints, ())