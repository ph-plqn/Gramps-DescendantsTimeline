import unittest
from datetime import date

from descendants_timeline.inference.birth_before_marriage_rule import (
    BirthBeforeMarriageRule,
)
from descendants_timeline.inference.rule_context import RuleContext

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import FamilyRoleSemantic
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
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


class BirthBeforeMarriageRuleTests(unittest.TestCase):

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

        self.rule = BirthBeforeMarriageRule()
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

    def make_marriage_evidence(
        self,
        family_id,
        event_id,
        minimum,
        maximum,
    ):
        date_value = TemporalValue(
            source_value="test",
            source_calendar="GREGORIAN",
            normalized_minimum=minimum,
            normalized_maximum=maximum,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        return TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id=family_id,
            event_id=event_id,
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=date_value,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id=family_id,
        )

    def make_context(
        self,
        families=(),
        evidences=(),
    ):
        family_mapping = {
            family.family_id: family
            for family in families
        }

        return RuleContext(
            data=RawGenealogyData(
                persons={
                    "I001": self.person1,
                    "I002": self.person2,
                    "I003": self.person3,
                },
                families=family_mapping,
                events={},
                root_person_id="I001",
            ),
            evidences=evidences,
        )

    def birth_target(self):
        return TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

    def test_is_applicable_to_person_birth(self):
        context = self.make_context()

        self.assertTrue(
            self.rule.is_applicable(
                self.birth_target(),
                context,
            )
        )

    def test_is_not_applicable_to_person_death(self):
        context = self.make_context()

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        self.assertFalse(
            self.rule.is_applicable(target, context)
        )

    def test_evaluate_without_marriage_evidence_returns_empty(self):
        context = self.make_context()

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_evaluate_birth_when_person_is_parent1(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        evidence = self.make_marriage_evidence(
            "F001",
            "E001",
            date(1825, 1, 1),
            date(1827, 1, 1),
        )

        context = self.make_context(
            families=(family,),
            evidences=(evidence,),
        )

        target = self.birth_target()

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(len(constraints), 1)

        constraint = constraints[0]

        self.assertEqual(constraint.target, target)

        self.assertIs(
            constraint.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )

        self.assertEqual(
            constraint.bound,
            date(1827, 1, 1),
        )

        self.assertEqual(
            constraint.rule_id,
            "BIRTH_BEFORE_MARRIAGE",
        )

        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_evaluate_birth_when_person_is_parent2(self):
        family = self.make_family(
            "F001",
            "I002",
            "I001",
        )

        evidence = self.make_marriage_evidence(
            "F001",
            "E001",
            date(1841, 8, 17),
            date(1841, 8, 17),
        )

        context = self.make_context(
            families=(family,),
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(len(constraints), 1)

        self.assertEqual(
            constraints[0].bound,
            date(1841, 8, 17),
        )

    def test_ignores_marriage_of_unrelated_family(self):
        family = self.make_family(
            "F001",
            "I002",
            "I003",
        )

        evidence = self.make_marriage_evidence(
            "F001",
            "E001",
            date(1841, 8, 17),
            date(1841, 8, 17),
        )

        context = self.make_context(
            families=(family,),
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_multiple_marriages_produce_multiple_constraints(self):
        family1 = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        family2 = self.make_family(
            "F002",
            "I001",
            "I003",
        )

        evidence1 = self.make_marriage_evidence(
            "F001",
            "E001",
            date(1825, 6, 10),
            date(1825, 6, 10),
        )

        evidence2 = self.make_marriage_evidence(
            "F002",
            "E002",
            date(1840, 8, 20),
            date(1840, 8, 20),
        )

        context = self.make_context(
            families=(family1, family2),
            evidences=(evidence1, evidence2),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(len(constraints), 2)

        self.assertEqual(
            constraints[0].bound,
            date(1825, 6, 10),
        )

        self.assertEqual(
            constraints[1].bound,
            date(1840, 8, 20),
        )

        self.assertEqual(
            constraints[0].evidences,
            (evidence1,),
        )

        self.assertEqual(
            constraints[1].evidences,
            (evidence2,),
        )

    def test_ignores_marriage_without_upper_bound(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        evidence = self.make_marriage_evidence(
            "F001",
            "E001",
            date(1825, 6, 10),
            None,
        )

        context = self.make_context(
            families=(family,),
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.birth_target(),
            context,
        )

        self.assertEqual(constraints, ())

