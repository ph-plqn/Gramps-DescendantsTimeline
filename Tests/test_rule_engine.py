import unittest

from descendants_timeline.inference.rule_context import RuleContext
from descendants_timeline.inference.rule_engine import RuleEngine
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)
from dataclasses import FrozenInstanceError
from descendants_timeline.inference.rule import Rule
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
    TemporalConstraint,
)
from datetime import date

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.inference.birth_before_death_rule import (
    BirthBeforeDeathRule,
)

class ConstraintRule(Rule):
    rule_id = "TEST_CONSTRAINT"
    strength = ConstraintStrength.HARD

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return True

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id=target.owner_id,
            event_id="E_TEST",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=TemporalValue(
                source_value="01/01/1900",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1900, 1, 1),
                normalized_maximum=date(1900, 1, 1),
                representative_value=date(1900, 1, 1),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id=target.owner_id,
        )

        return (
            TemporalConstraint(
                target=target,
                operator=ConstraintOperator.BEFORE_OR_EQUAL,
                bound=date(1900, 1, 1),
                rule_id=self.rule_id,
                strength=self.strength,
                evidences=(evidence,),
            ),
        )

class NonApplicableRule(Rule):
    rule_id = "TEST_NON_APPLICABLE"
    strength = ConstraintStrength.HARD

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return False

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:
        raise AssertionError(
            "evaluate() must not be called for a non-applicable rule"
        )

class FirstConstraintRule(Rule):
    rule_id = "TEST_FIRST"
    strength = ConstraintStrength.HARD

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return True

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id=target.owner_id,
            event_id="E_FIRST",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=TemporalValue(
                source_value="01/01/1900",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1900, 1, 1),
                normalized_maximum=date(1900, 1, 1),
                representative_value=date(1900, 1, 1),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id=target.owner_id,
        )

        return (
            TemporalConstraint(
                target=target,
                operator=ConstraintOperator.BEFORE_OR_EQUAL,
                bound=date(1900, 1, 1),
                rule_id=self.rule_id,
                strength=self.strength,
                evidences=(evidence,),
            ),
        )

class SecondConstraintRule(Rule):
    rule_id = "TEST_SECOND"
    strength = ConstraintStrength.HARD

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return True

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:

        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id=target.owner_id,
            event_id="E_SECOND",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=TemporalValue(
                source_value="02/01/1900",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1900, 1, 2),
                normalized_maximum=date(1900, 1, 2),
                representative_value=date(1900, 1, 2),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id=target.owner_id,
        )

        return (
            TemporalConstraint(
                target=target,
                operator=ConstraintOperator.BEFORE_OR_EQUAL,
                bound=date(1900, 1, 2),
                rule_id=self.rule_id,
                strength=self.strength,
                evidences=(evidence,),
            ),
        )

class MultipleConstraintsRule(ConstraintRule):
    rule_id = "TEST_MULTIPLE"

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:
        base_constraint = super().evaluate(
            target,
            context,
        )[0]

        evidence = base_constraint.evidences[0]

        return (
            TemporalConstraint(
                target=target,
                operator=ConstraintOperator.BEFORE_OR_EQUAL,
                bound=date(1900, 1, 1),
                rule_id=self.rule_id,
                strength=self.strength,
                evidences=(evidence,),
            ),
            TemporalConstraint(
                target=target,
                operator=ConstraintOperator.BEFORE_OR_EQUAL,
                bound=date(1910, 1, 1),
                rule_id=self.rule_id,
                strength=self.strength,
                evidences=(evidence,),
            ),
        )

class ApplicableRule(Rule):
    rule_id = "TEST_APPLICABLE"
    strength = ConstraintStrength.HARD

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return True

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:
        return ()

class RuleEngineTests(unittest.TestCase):

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

        self.target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )
    def test_evaluate_with_no_rules_returns_empty(self):
        engine = RuleEngine(
            rules=(),
        )

        constraints = engine.evaluate(
            self.target,
            self.context,
        )

        self.assertEqual(constraints, ())
    def test_rejects_non_tuple_rules(self):
        with self.assertRaises(TypeError):
            RuleEngine(
                rules=[],
            )
    def test_rejects_invalid_rule_item(self):
        with self.assertRaises(TypeError):
            RuleEngine(
                rules=("not a rule",),
            )
    def test_rule_engine_is_immutable(self):
        engine = RuleEngine(
            rules=(),
        )

        with self.assertRaises(FrozenInstanceError):
            engine.rules = ()  
    def test_evaluate_applicable_rule_returning_empty_returns_empty(self):
        rule = ApplicableRule()

        engine = RuleEngine(
            rules=(rule,),
        )

        constraints = engine.evaluate(
            self.target,
            self.context,
        )

        self.assertEqual(constraints, ())
    def test_evaluate_returns_constraint_from_applicable_rule(self):
        rule = ConstraintRule()

        engine = RuleEngine(
            rules=(rule,),
        )

        constraints = engine.evaluate(
            self.target,
            self.context,
        )

        self.assertEqual(len(constraints), 1)

        constraint = constraints[0]

        self.assertEqual(
            constraint.target,
            self.target,
        )
        self.assertIs(
            constraint.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1900, 1, 1),
        )
        self.assertEqual(
            constraint.rule_id,
            "TEST_CONSTRAINT",
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )
    def test_non_applicable_rule_is_not_evaluated(self):
        engine = RuleEngine(
            rules=(NonApplicableRule(),),
        )

        constraints = engine.evaluate(
            self.target,
            self.context,
        )

        self.assertEqual(constraints, ())
    def test_evaluate_preserves_rule_order(self):
        engine = RuleEngine(
            rules=(
                FirstConstraintRule(),
                SecondConstraintRule(),
            ),
        )

        constraints = engine.evaluate(
            self.target,
            self.context,
        )

        self.assertEqual(len(constraints), 2)

        self.assertEqual(
            constraints[0].rule_id,
            "TEST_FIRST",
        )
        self.assertEqual(
            constraints[1].rule_id,
            "TEST_SECOND",
        )
    def test_evaluate_preserves_multiple_constraints_from_one_rule(self):
        engine = RuleEngine(
            rules=(MultipleConstraintsRule(),),
        )

        constraints = engine.evaluate(
            self.target,
            self.context,
        )

        self.assertEqual(len(constraints), 2)

        self.assertEqual(
            constraints[0].bound,
            date(1900, 1, 1),
        )
        self.assertEqual(
            constraints[1].bound,
            date(1910, 1, 1),
        )

        self.assertEqual(
            constraints[0].rule_id,
            "TEST_MULTIPLE",
        )
        self.assertEqual(
            constraints[1].rule_id,
            "TEST_MULTIPLE",
        )
    def test_integration_birth_before_death_rule(self):
        death_date = TemporalValue(
            source_value="17/08/1872-19/08/1872",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1872, 8, 17),
            normalized_maximum=date(1872, 8, 19),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        death_evidence = TemporalEvidence(
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
            data=self.context.data,
            evidences=(death_evidence,),
        )

        engine = RuleEngine(
            rules=(BirthBeforeDeathRule(),),
        )

        constraints = engine.evaluate(
            self.target,
            context,
        )

        self.assertEqual(len(constraints), 1)

        constraint = constraints[0]

        self.assertEqual(
            constraint.target,
            self.target,
        )
        self.assertIs(
            constraint.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1872, 8, 19),
        )
        self.assertEqual(
            constraint.rule_id,
            "BIRTH_BEFORE_DEATH",
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )
        self.assertEqual(
            constraint.evidences,
            (death_evidence,),
        )
    def test_integration_birth_before_death_rule_for_death(self):
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

        engine = RuleEngine(
            rules=(BirthBeforeDeathRule(),),
        )

        constraints = engine.evaluate(
            target,
            context,
        )

        self.assertEqual(len(constraints), 1)

        constraint = constraints[0]

        self.assertEqual(
            constraint.target,
            target,
        )
        self.assertIs(
            constraint.operator,
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1841, 8, 17),
        )
        self.assertEqual(
            constraint.rule_id,
            "BIRTH_BEFORE_DEATH",
        )
        self.assertIs(
            constraint.strength,
            ConstraintStrength.HARD,
        )
        self.assertEqual(
            constraint.evidences,
            (birth_evidence,),
        )