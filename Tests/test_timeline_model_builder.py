from __future__ import annotations

import unittest

from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.timeline.timeline_model import TimelineModel
from descendants_timeline.timeline.timeline_model_builder import (
    TimelineModelBuilder,
)
from descendants_timeline.traversal.descendance_traversal import (
    DescendanceTraversal,
)
from descendants_timeline.inference.temporal_inference_engine import (
    TemporalInferenceEngine,
)

class TimelineModelBuilderTests(unittest.TestCase):
    def test_builds_minimal_timeline_model(self) -> None:
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

        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=(),
        )

        self.assertIsInstance(
            model,
            TimelineModel,
        )
        self.assertIs(
            model.data,
            data,
        )
        self.assertIs(
            model.traversal,
            traversal,
        )
        self.assertEqual(
            model.temporal_results,
            {},
        )

    def test_indexes_temporal_results_by_target(self) -> None:
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

        temporal_results = TemporalInferenceEngine().run(data)

        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        self.assertEqual(
            len(model.temporal_results),
            len(temporal_results),
        )

        for result in temporal_results:
            target = result.target_entry.target

            self.assertIs(
                model.temporal_results[target],
                result,
            )

    def test_rejects_duplicate_temporal_targets(self) -> None:
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

        temporal_results = TemporalInferenceEngine().run(data)

        duplicated_result = temporal_results[0]

        with self.assertRaisesRegex(
            ValueError,
            "duplicate temporal target",
        ):
            TimelineModelBuilder().build(
                data=data,
                traversal=traversal,
                temporal_results=(
                    duplicated_result,
                    duplicated_result,
                ),
            )

    def test_temporal_results_must_be_tuple(self) -> None:
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
            "temporal_results must be a tuple",
        ):
            TimelineModelBuilder().build(
                data=data,
                traversal=traversal,
                temporal_results=[],
            )

if __name__ == "__main__":
    unittest.main()