from __future__ import annotations

import unittest

from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.timeline.timeline_model import TimelineModel
from descendants_timeline.traversal.descendance_traversal import (
    DescendanceTraversal,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from descendants_timeline.inference.temporal_inference_engine import (
    TemporalInferenceEngine,
)
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.temporal import TemporalValue
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.temporal import TemporalValue


class TimelineModelTests(unittest.TestCase):
    def test_minimal_timeline_model_can_be_created(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        self.assertIs(model.data, data)
        self.assertIs(model.traversal, traversal)
        self.assertEqual(model.temporal_results, {})

    def test_data_must_be_raw_genealogy_data(self) -> None:
        with self.assertRaisesRegex(
            TypeError,
            "data must be a RawGenealogyData",
        ):
            TimelineModel(
                data="not genealogy data",
                traversal=None,
                temporal_results={},
            )
    def test_traversal_must_be_traversal_result(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        with self.assertRaisesRegex(
            TypeError,
            "traversal must be a TraversalResult",
        ):
            TimelineModel(
                data=data,
                traversal="not a traversal result",
                temporal_results={},
            )

    def test_temporal_results_must_be_mapping(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        with self.assertRaisesRegex(
            TypeError,
            "temporal_results must be a Mapping",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results=(),
            )

    def test_temporal_results_keys_must_be_temporal_targets(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        with self.assertRaisesRegex(
            TypeError,
            "temporal_results keys must be TemporalTarget objects",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results={
                    "not a temporal target": None,
                },
            )

    def test_temporal_results_values_must_be_temporal_inference_results(
        self,
    ) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )

        with self.assertRaisesRegex(
            TypeError,
            "temporal_results values must be TemporalInferenceResult objects",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results={
                    target: "not a temporal inference result",
                },
            )

    def test_temporal_result_key_must_match_result_target(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        results = TemporalInferenceEngine().run(data)

        birth_result = next(
            result
            for result in results
            if result.target_entry.target.semantic is TargetSemantic.BIRTH
        )

        wrong_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )

        with self.assertRaisesRegex(
            ValueError,
            "temporal_results key must match result target",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results={
                    wrong_target: birth_result,
                },
            )

    def test_person_temporal_target_owner_must_exist_in_data(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        other_person = Person(
            person_id="I2",
            display_name="Other",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        other_data = RawGenealogyData(
            persons={"I2": other_person},
            families={},
            events={},
            root_person_id="I2",
        )

        result = next(
            result
            for result in TemporalInferenceEngine().run(other_data)
            if result.target_entry.target.semantic is TargetSemantic.BIRTH
        )

        target = result.target_entry.target

        with self.assertRaisesRegex(
            ValueError,
            "temporal target person owner must exist in data",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results={
                    target: result,
                },
            )

    def test_family_temporal_target_owner_must_exist_in_data(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue.unknown(),
        )

        other_family = Family(
            family_id="F2",
            parent1_id=None,
            parent2_id=None,
            event_refs=(
                FamilyEventRef(
                    event_id="E1",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="FAMILY",
                ),
            ),
            child_refs=(),
        )

        other_data = RawGenealogyData(
            persons={},
            families={"F2": other_family},
            events={"E1": marriage},
            root_person_id=None,
        )

        result = next(
            result
            for result in TemporalInferenceEngine().run(other_data)
            if result.target_entry.target.semantic is TargetSemantic.MARRIAGE
        )

        target = result.target_entry.target

        with self.assertRaisesRegex(
            ValueError,
            "temporal target family owner must exist in data",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results={
                    target: result,
                },
            )

    def test_family_temporal_target_owner_must_exist_in_data(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        other_root = Person(
            person_id="I2",
            display_name="Other root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F2",),
        )

        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue.unknown(),
        )

        other_family = Family(
            family_id="F2",
            parent1_id="I2",
            parent2_id=None,
            event_refs=(
                FamilyEventRef(
                    event_id="E1",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="FAMILY",
                ),
            ),
            child_refs=(),
        )

        other_data = RawGenealogyData(
            persons={"I2": other_root},
            families={"F2": other_family},
            events={"E1": marriage},
            root_person_id="I2",
        )

        result = next(
            result
            for result in TemporalInferenceEngine().run(other_data)
            if result.target_entry.target.semantic is TargetSemantic.MARRIAGE
        )

        target = result.target_entry.target

        with self.assertRaisesRegex(
            ValueError,
            "temporal target family owner must exist in data",
        ):
            TimelineModel(
                data=data,
                traversal=traversal,
                temporal_results={
                    target: result,
                },
            )

    def test_temporal_results_are_defensively_copied(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = DescendanceTraversal().traverse(
            data,
            "I1",
        )

        temporal_results = {}

        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        temporal_results["external mutation"] = "invalid"

        self.assertEqual(
            model.temporal_results,
            {},
        )

if __name__ == "__main__":
    unittest.main()