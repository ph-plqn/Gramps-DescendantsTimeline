import unittest
from datetime import date

from descendants_timeline.inference.marriage_before_spouse_burial_rule import (
    MarriageBeforeSpouseBurialRule,
)
from descendants_timeline.inference.rule_context import RuleContext

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.family import Family
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.temporal import (
    TemporalValue,
    ValueOrigin,
    SourceQuality,
    EvidenceStatus,
    CertaintyLevel,
)
from descendants_timeline.model.person_event_ref import EventRoleSemantic
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


class MarriageBeforeSpouseBurialRuleTests(unittest.TestCase):

    def setUp(self):
        self.person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        self.person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        self.person3 = Person(
            person_id="I003",
            display_name="Anne TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        self.rule = MarriageBeforeSpouseBurialRule()

    def make_family(
        self,
        family_id,
        parent1_id,
        parent2_id,
    ):
        return Family(
            family_id=family_id,
            parent1_id=parent1_id,
            parent2_id=parent2_id,
            event_refs=(),
            child_refs=(),
        )

    def make_data(self, family):
        return RawGenealogyData(
            persons={
                "I001": self.person1,
                "I002": self.person2,
                "I003": self.person3,
            },
            families={
                family.family_id: family,
            },
            events={},
            root_person_id="I001",
        )
    def make_target(self, family_id="F001"):
        return TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id=family_id,
            semantic=TargetSemantic.MARRIAGE,
        )

    def make_burial_evidence(
        self,
        person_id,
        event_id,
        minimum,
        maximum,
        role=EventRoleSemantic.PRINCIPAL,
    ):
        burial_date = TemporalValue(
            source_value="test",
            source_calendar="GREGORIAN",
            normalized_minimum=minimum,
            normalized_maximum=maximum,
            representative_value=(
                minimum
                if minimum is not None and minimum == maximum
                else None
            ),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        return TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id=person_id,
            event_id=event_id,
            semantic=EventSemantic.BURIAL,
            role=role,
            date=burial_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id=person_id,
        )

    def test_is_applicable_to_family_marriage_target(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        context = RuleContext(
            data=data,
            evidences=(),
        )

        target = self.make_target()

        self.assertTrue(
            self.rule.is_applicable(target, context)
        )

    def test_is_not_applicable_to_family_divorce_target(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        context = RuleContext(
            data=data,
            evidences=(),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        self.assertFalse(
            self.rule.is_applicable(target, context)
        )

    def test_returns_no_constraint_without_burial_evidence(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        context = RuleContext(
            data=data,
            evidences=(),
        )

        target = self.make_target()

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(constraints, ())

    def test_burial_of_parent1_produces_constraint(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_burial_evidence(
            person_id="I001",
            event_id="E001",
            minimum=date(1870, 1, 1),
            maximum=date(1871, 1, 1),
        )

        context = RuleContext(
            data=data,
            evidences=(evidence,),
        )

        target = self.make_target()

        constraints = self.rule.evaluate(
            target,
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
            date(1871, 1, 1),
        )

        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            constraint.rule_id,
            "MARRIAGE_BEFORE_SPOUSE_BURIAL",
        )

        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_burial_of_parent2_produces_constraint(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_burial_evidence(
            person_id="I002",
            event_id="E002",
            minimum=date(1880, 1, 1),
            maximum=date(1882, 1, 1),
        )

        context = RuleContext(
            data=data,
            evidences=(evidence,),
        )

        target = self.make_target()

        constraints = self.rule.evaluate(
            target,
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
            date(1882, 1, 1),
        )

        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            constraint.rule_id,
            "MARRIAGE_BEFORE_SPOUSE_BURIAL",
        )

        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_burials_of_both_parents_produce_two_constraints(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence1 = self.make_burial_evidence(
            person_id="I001",
            event_id="E001",
            minimum=date(1870, 1, 1),
            maximum=date(1871, 1, 1),
        )

        evidence2 = self.make_burial_evidence(
            person_id="I002",
            event_id="E002",
            minimum=date(1880, 1, 1),
            maximum=date(1882, 1, 1),
        )

        context = RuleContext(
            data=data,
            evidences=(
                evidence1,
                evidence2,
            ),
        )

        constraints = self.rule.evaluate(
            self.make_target(),
            context,
        )

        self.assertEqual(len(constraints), 2)

        self.assertEqual(
            tuple(constraint.bound for constraint in constraints),
            (
                date(1871, 1, 1),
                date(1882, 1, 1),
            ),
        )

        self.assertEqual(
            constraints[0].evidences,
            (evidence1,),
        )

        self.assertEqual(
            constraints[1].evidences,
            (evidence2,),
        )

    def test_burial_of_unrelated_person_is_ignored(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_burial_evidence(
            person_id="I003",
            event_id="E003",
            minimum=date(1860, 1, 1),
            maximum=date(1860, 1, 1),
        )

        context = RuleContext(
            data=data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.make_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_burial_without_maximum_is_ignored(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_burial_evidence(
            person_id="I001",
            event_id="E001",
            minimum=date(1870, 1, 1),
            maximum=None,
        )

        context = RuleContext(
            data=data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.make_target(),
            context,
        )

        self.assertEqual(constraints, ())