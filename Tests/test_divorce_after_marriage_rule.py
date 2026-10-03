import unittest
from datetime import date

from descendants_timeline.inference.divorce_after_marriage_rule import (
    DivorceAfterMarriageRule,
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


class DivorceAfterMarriageRuleTests(unittest.TestCase):

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

        self.family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        self.data = RawGenealogyData(
            persons={
                "I001": self.person1,
                "I002": self.person2,
            },
            families={
                "F001": self.family,
            },
            events={},
            root_person_id="I001",
        )

        self.rule = DivorceAfterMarriageRule()

    def make_target(self):
        return TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

    def make_marriage_evidence(
        self,
        family_id,
        event_id,
        minimum,
        maximum,
    ):
        marriage_date = TemporalValue(
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
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id=family_id,
            event_id=event_id,
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=marriage_date,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id=family_id,
        )

    def test_is_applicable_to_family_divorce_target(self):
        context = RuleContext(
            data=self.data,
            evidences=(),
        )

        self.assertTrue(
            self.rule.is_applicable(
                self.make_target(),
                context,
            )
        )

    def test_is_not_applicable_to_family_marriage_target(self):
        context = RuleContext(
            data=self.data,
            evidences=(),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        self.assertFalse(
            self.rule.is_applicable(
                target,
                context,
            )
        )

    def test_returns_no_constraint_without_marriage_evidence(self):
        context = RuleContext(
            data=self.data,
            evidences=(),
        )

        constraints = self.rule.evaluate(
            self.make_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_marriage_produces_divorce_upper_bound(self):
        evidence = self.make_marriage_evidence(
            family_id="F001",
            event_id="E001",
            minimum=date(1840, 1, 1),
            maximum=date(1842, 1, 1),
        )

        context = RuleContext(
            data=self.data,
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
            date(1840, 1, 1),
        )

        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            constraint.rule_id,
            "DIVORCE_AFTER_MARRIAGE",
        )

        self.assertEqual(
            constraint.evidences,
            (evidence,),
        )

    def test_marriage_of_other_family_is_ignored(self):
        evidence = self.make_marriage_evidence(
            family_id="F002",
            event_id="E002",
            minimum=date(1850, 1, 1),
            maximum=date(1850, 1, 1),
        )

        context = RuleContext(
            data=self.data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.make_target(),
            context,
        )

        self.assertEqual(constraints, ())

    def test_multiple_marriages_produce_multiple_constraints(self):
        evidence1 = self.make_marriage_evidence(
            family_id="F001",
            event_id="E001",
            minimum=date(1840, 1, 1),
            maximum=date(1842, 1, 1),
        )

        evidence2 = self.make_marriage_evidence(
            family_id="F001",
            event_id="E002",
            minimum=date(1838, 1, 1),
            maximum=date(1839, 1, 1),
        )

        context = RuleContext(
            data=self.data,
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
                date(1840, 1, 1),
                date(1838, 1, 1),
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

    def test_marriage_without_minimum_is_ignored(self):
        evidence = self.make_marriage_evidence(
            family_id="F001",
            event_id="E001",
            minimum=None,
            maximum=date(1840, 1, 1),
        )

        context = RuleContext(
            data=self.data,
            evidences=(evidence,),
        )

        constraints = self.rule.evaluate(
            self.make_target(),
            context,
        )

        self.assertEqual(constraints, ())