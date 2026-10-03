import unittest

from descendants_timeline.inference.death_maximum_lifespan_from_birth_rule import (
    DeathMaximumLifespanFromBirthRule,
)
from descendants_timeline.inference.rule_context import RuleContext
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)

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
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)

class DeathMaximumLifespanFromBirthRuleTests(unittest.TestCase):

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

        self.rule = DeathMaximumLifespanFromBirthRule()

    def test_is_not_applicable_to_person_birth(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        self.assertFalse(
            self.rule.is_applicable(target, self.context)
        )

    def test_is_applicable_to_person_death(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        self.assertTrue(
            self.rule.is_applicable(target, self.context)
        )

    def test_is_not_applicable_to_family_marriage(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        self.assertFalse(
            self.rule.is_applicable(target, self.context)
        )


    def test_evaluate_death_from_birth_evidence(self):
        birth_date = TemporalValue(
            source_value="17/08/1841-19/08/1841",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1841, 8, 17),
            normalized_maximum=date(1841, 8, 19),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(birth_evidence,),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

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
            date(1966, 8, 19),
        )
        self.assertEqual(
            constraint.rule_id,
            "DEATH_MAXIMUM_LIFESPAN_FROM_BIRTH",
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.SOFT,
        )
        self.assertEqual(
            constraint.evidences,
            (birth_evidence,),
        )
    def test_evaluate_death_without_birth_evidence_returns_empty(self):
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        constraints = self.rule.evaluate(
            target,
            self.context,
        )

        self.assertEqual(constraints, ())


    def test_evaluate_death_with_multiple_birth_evidences_returns_empty(self):
        birth_date_1 = TemporalValue(
            source_value="17/08/1841",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1841, 8, 17),
            normalized_maximum=date(1841, 8, 17),
            representative_value=date(1841, 8, 17),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_date_2 = TemporalValue(
            source_value="22/08/1841",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1841, 8, 22),
            normalized_maximum=date(1841, 8, 22),
            representative_value=date(1841, 8, 22),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_evidence_1 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_date_1,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        birth_evidence_2 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E002",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_date_2,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(
                birth_evidence_1,
                birth_evidence_2,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(constraints, ())


    def test_evaluate_death_ignores_birth_witness_evidence(self):
        birth_date = TemporalValue(
            source_value="17/08/1841",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1841, 8, 17),
            normalized_maximum=date(1841, 8, 17),
            representative_value=date(1841, 8, 17),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.WITNESS,
            date=birth_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I002",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(birth_evidence,),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(constraints, ())

    def test_birth_without_upper_bound_returns_empty(self):
        birth_date = TemporalValue(
            source_value="after 17/08/1841",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1841, 8, 17),
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(birth_evidence,),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        constraints = self.rule.evaluate(target, context)

        self.assertEqual(constraints, ())

    def test_birth_without_lower_bound_uses_upper_bound(self):
        birth_date = TemporalValue(
            source_value="before 19/08/1841",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=date(1841, 8, 19),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(birth_evidence,),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(len(constraints), 1)

        self.assertEqual(
            constraints[0].bound,
            date(1966, 8, 19),
        )
    def test_february_29_birth_uses_march_1_when_needed(self):
        birth_date = TemporalValue(
            source_value="29/02/1804",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1804, 2, 29),
            normalized_maximum=date(1804, 2, 29),
            representative_value=date(1804, 2, 29),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=self.context.data,
            evidences=(birth_evidence,),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        constraints = self.rule.evaluate(
            target,
            context,
        )

        self.assertEqual(len(constraints), 1)

        self.assertEqual(
            constraints[0].bound,
            date(1929, 3, 1),
        )