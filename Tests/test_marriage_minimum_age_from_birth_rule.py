import unittest
from datetime import date

from descendants_timeline.inference.marriage_minimum_age_from_birth_rule import (
    MarriageMinimumAgeFromBirthRule,
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

class MarriageMinimumAgeFromBirthRuleTests(unittest.TestCase):

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

        self.rule = MarriageMinimumAgeFromBirthRule()

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

    def make_birth_evidence(
        self,
        person_id,
        event_id,
        minimum,
        maximum,
        role=EventRoleSemantic.PRINCIPAL,
    ):
        birth_date = TemporalValue(
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
            semantic=EventSemantic.BIRTH,
            role=role,
            date=birth_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id=person_id,
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

    def test_returns_no_constraint_without_birth_evidence(self):
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
        
    def test_birth_of_parent1_produces_constraint(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_birth_evidence(
            person_id="I001",
            event_id="E001",
            minimum=date(1800, 1, 1),
            maximum=date(1801, 1, 1),
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
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1812, 1, 1),
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            constraint.rule_id,
            "MARRIAGE_MINIMUM_AGE_FROM_BIRTH",
        )
        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_birth_of_parent2_produces_constraint(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_birth_evidence(
            person_id="I002",
            event_id="E002",
            minimum=date(1805, 1, 1),
            maximum=date(1806, 1, 1),
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
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1817, 1, 1),
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            constraint.rule_id,
            "MARRIAGE_MINIMUM_AGE_FROM_BIRTH",
        )
        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_births_of_both_parents_produce_two_constraints(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence1 = self.make_birth_evidence(
            person_id="I001",
            event_id="E001",
            minimum=date(1800, 1, 1),
            maximum=date(1801, 1, 1),
        )

        evidence2 = self.make_birth_evidence(
            person_id="I002",
            event_id="E002",
            minimum=date(1805, 1, 1),
            maximum=date(1806, 1, 1),
        )

        context = RuleContext(
            data=data,
            evidences=(
                evidence1,
                evidence2,
            ),
        )

        target = self.make_target()

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(len(constraints), 2)

        self.assertEqual(
            tuple(constraint.bound for constraint in constraints),
            (
                date(1812, 1, 1),
                date(1817, 1, 1),
            ),
        )

        self.assertTrue(
            all(
                constraint.operator
                is ConstraintOperator.AFTER_OR_EQUAL
                for constraint in constraints
            )
        )

        self.assertTrue(
            all(
                constraint.strength
                is ConstraintStrength.SOFT
                for constraint in constraints
            )
        )

        self.assertEqual(
            constraints[0].evidences,
            (evidence1,),
        )

        self.assertEqual(
            constraints[1].evidences,
            (evidence2,),
        )

    def test_birth_of_unrelated_person_is_ignored(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_birth_evidence(
            person_id="I003",
            event_id="E003",
            minimum=date(1810, 1, 1),
            maximum=date(1810, 1, 1),
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

        self.assertEqual(constraints, ())

    def test_birth_without_minimum_is_ignored(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_birth_evidence(
            person_id="I001",
            event_id="E001",
            minimum=None,
            maximum=date(1800, 1, 1),
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

        self.assertEqual(constraints, ())
    def test_february_29_birth_uses_calendar_year_arithmetic(self):
        family = self.make_family(
            "F001",
            "I001",
            "I002",
        )

        data = self.make_data(family)

        evidence = self.make_birth_evidence(
            person_id="I001",
            event_id="E001",
            minimum=date(1804, 2, 29),
            maximum=date(1804, 2, 29),
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

        self.assertEqual(
            constraints[0].bound,
            date(1816, 2, 29),
        )
