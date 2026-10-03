import unittest

from descendants_timeline.inference.temporal_inference_engine import (
    TemporalInferenceEngine,
)
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.inference.temporal_inference_result import (
    TemporalInferenceResult,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
)
from datetime import date

from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
    PersonEventRef,
)
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
)
from descendants_timeline.inference.rule_engine import (
    RuleEngine,
)
from descendants_timeline.inference.default_rules import (
    default_rules,
)

class TestTemporalInferenceEngine(unittest.TestCase):

    def test_run_rejects_non_raw_genealogy_data(self) -> None:
        engine = TemporalInferenceEngine()

        with self.assertRaisesRegex(
            TypeError,
            "data must be a RawGenealogyData",
        ):
            engine.run(None)
    def make_minimal_genealogy(self) -> RawGenealogyData:
        person = Person(
            person_id="I0001",
            display_name="Person I0001",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        return RawGenealogyData(
            persons={person.person_id: person},
            families={},
            events={},
            root_person_id=person.person_id,
        )
    def make_genealogy_with_death(self) -> RawGenealogyData:
        death = Event(
            event_id="E0001",
            source_type="DEATH",
            semantic=EventSemantic.DEATH,
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
        )

        person = Person(
            person_id="I0001",
            display_name="Person I0001",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E0001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        return RawGenealogyData(
            persons={person.person_id: person},
            families={},
            events={death.event_id: death},
            root_person_id=person.person_id,
        )

    def make_genealogy_with_birth(self) -> RawGenealogyData:
        birth = Event(
            event_id="E0001",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1840, 1, 1),
                normalized_maximum=date(1840, 1, 1),
                representative_value=date(1840, 1, 1),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )

        person = Person(
            person_id="I0001",
            display_name="Person I0001",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E0001",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        return RawGenealogyData(
            persons={person.person_id: person},
            families={},
            events={birth.event_id: birth},
            root_person_id=person.person_id,
        )
    def test_run_returns_tuple_of_inference_results(self) -> None:
        data = self.make_minimal_genealogy()

        results = TemporalInferenceEngine().run(data)

        self.assertIsInstance(results, tuple)
        self.assertTrue(
            all(
                isinstance(result, TemporalInferenceResult)
                for result in results
            )
        )
    def test_run_returns_one_result_per_temporal_target(self) -> None:
        data = self.make_minimal_genealogy()

        results = TemporalInferenceEngine().run(data)

        self.assertEqual(len(results), 2)
    def test_run_preserves_temporal_target_order(self) -> None:
        data = self.make_minimal_genealogy()

        results = TemporalInferenceEngine().run(data)

        self.assertEqual(
            tuple(
                result.target_entry.target.semantic
                for result in results
            ),
            (
                TargetSemantic.BIRTH,
                TargetSemantic.DEATH,
            ),
        )
    def test_run_applies_birth_before_death_rule(self) -> None:
        data = self.make_genealogy_with_death()

        results = TemporalInferenceEngine().run(data)

        birth_result = next(
            result
            for result in results
            if result.target_entry.target.semantic
            is TargetSemantic.BIRTH
        )

        constraint = next(
            constraint
            for constraint in birth_result.constraints
            if constraint.rule_id == "BIRTH_BEFORE_DEATH"
        )

        self.assertEqual(
            constraint.rule_id,
            "BIRTH_BEFORE_DEATH",
        )
        self.assertIs(
            constraint.operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1900, 1, 1),
        )
    def test_run_propagates_constraint_to_reconciled_domain(self) -> None:
        data = self.make_genealogy_with_death()

        results = TemporalInferenceEngine().run(data)

        birth_result = next(
            result
            for result in results
            if result.target_entry.target.semantic
            is TargetSemantic.BIRTH
        )

        self.assertIsNotNone(
            birth_result.reconciled_domain.principal_maximum
        )
        self.assertEqual(
            birth_result.reconciled_domain.principal_maximum.value,
            date(1900, 1, 1),
        )
    def test_run_applies_birth_before_death_rule_to_death(self) -> None:
        data = self.make_genealogy_with_birth()

        results = TemporalInferenceEngine().run(data)

        death_result = next(
            result
            for result in results
            if result.target_entry.target.semantic
            is TargetSemantic.DEATH
        )

        constraint = next(
            constraint
            for constraint in death_result.constraints
            if constraint.rule_id == "BIRTH_BEFORE_DEATH"
        )

        self.assertEqual(
            constraint.rule_id,
            "BIRTH_BEFORE_DEATH",
        )
        self.assertIs(
            constraint.operator,
            ConstraintOperator.AFTER_OR_EQUAL,
        )
        self.assertEqual(
            constraint.bound,
            date(1840, 1, 1),
        )
    def test_accepts_explicit_rule_engine(self) -> None:
        rule_engine = RuleEngine(
            rules=(),
        )

        engine = TemporalInferenceEngine(
            rule_engine=rule_engine,
        )

        self.assertIs(
            engine.rule_engine,
            rule_engine,
        )
    def test_run_uses_explicit_rule_engine(self) -> None:
        data = self.make_genealogy_with_death()

        engine = TemporalInferenceEngine(
            rule_engine=RuleEngine(
                rules=(),
            )
        )

        results = engine.run(data)

        birth_result = next(
            result
            for result in results
            if result.target_entry.target.semantic
            is TargetSemantic.BIRTH
        )

        self.assertEqual(
            birth_result.constraints,
            (),
        )
    def test_default_rule_engine_uses_default_rules(self) -> None:
        engine = TemporalInferenceEngine()

        self.assertEqual(
            tuple(
                rule.rule_id
                for rule in engine.rule_engine.rules
            ),
            tuple(
                rule.rule_id
                for rule in default_rules()
            ),
        )

    def test_run_preserves_certain_gramps_value_in_estimate(self) -> None:
        data = self.make_genealogy_with_birth()

        results = TemporalInferenceEngine().run(data)

        birth_result = next(
            result
            for result in results
            if result.target_entry.target.semantic
            is TargetSemantic.BIRTH
        )

        self.assertEqual(
            birth_result.estimate.representative_value,
            date(1840, 1, 1),
        )
        self.assertIs(
            birth_result.estimate.certainty,
            CertaintyLevel.CERTAIN,
        )
    def test_run_builds_inferred_birth_domain_without_inventing_estimate(
        self,
    ) -> None:
        data = self.make_genealogy_with_death()

        results = TemporalInferenceEngine().run(data)

        birth_result = next(
            result
            for result in results
            if result.target_entry.target.semantic
            is TargetSemantic.BIRTH
        )

        self.assertEqual(
            birth_result.reconciled_domain.principal_minimum.value,
            date(1775, 1, 1),
        )
        self.assertEqual(
            birth_result.reconciled_domain.principal_maximum.value,
            date(1900, 1, 1),
        )
        self.assertIsNone(
            birth_result.estimate.representative_value
        )
        self.assertIs(
            birth_result.estimate.certainty,
            CertaintyLevel.UNDETERMINED,
        )
if __name__ == "__main__":
    unittest.main()
