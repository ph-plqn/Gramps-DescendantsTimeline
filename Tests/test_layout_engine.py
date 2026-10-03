from __future__ import annotations

import unittest

from descendants_timeline.layout.layout_engine import LayoutEngine
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.timeline.timeline_model import TimelineModel
from descendants_timeline.traversal.descendance_traversal import (
    DescendanceTraversal,
    TraversalRole,
)
from descendants_timeline.traversal.descendance_traversal import (
    DescendanceTraversal,
    TraversalResult,
    TraversalRole,
    TraversalRow,
)
from datetime import date

from descendants_timeline.inference.temporal_inference_engine import (
    TemporalInferenceEngine,
)
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
from descendants_timeline.timeline.timeline_model_builder import (
    TimelineModelBuilder,
)
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.traversal.descendance_traversal import (
    FamilyTraversalState,
    TraversalFamilyOccurrence,
)

class LayoutEngineTests(unittest.TestCase):
    def test_root_produces_one_person_placement(self) -> None:
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

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.person_placements), 1)

        placement = layout.person_placements[0]

        self.assertEqual(placement.person_id, "I1")
        self.assertEqual(placement.row_index, 0)
        self.assertEqual(placement.generation, 1)
        self.assertIs(placement.role, TraversalRole.ROOT)
        self.assertIsNone(placement.family_id)
        self.assertIsNone(placement.spouse_of_person_id)
        self.assertIsNone(placement.x_start)
        self.assertIsNone(placement.x_end)
        self.assertEqual(placement.y, 20.0)

        self.assertEqual(layout.marriage_node_placements, ())
        self.assertEqual(layout.remarriage_segment_placements, ())

    def test_person_placements_preserve_traversal_row_order(self) -> None:
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        child1 = Person(
            person_id="I2",
            display_name="Child 1",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        child2 = Person(
            person_id="I3",
            display_name="Child 2",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I1": root,
                "I2": child1,
                "I3": child2,
            },
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=1,
                    role=TraversalRole.ROOT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I3",
                    generation=2,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=2,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
            ),
            family_occurrences=(),
        )

        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(
            tuple(
                placement.person_id
                for placement in layout.person_placements
            ),
            ("I1", "I3", "I2"),
        )

        self.assertEqual(
            tuple(
                placement.row_index
                for placement in layout.person_placements
            ),
            (0, 1, 2),
        )

        self.assertEqual(
            tuple(
                placement.y
                for placement in layout.person_placements
            ),
            (20.0, 50.0, 80.0),
        )

    def test_spouse_row_context_is_preserved(self) -> None:
        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        spouse = Person(
            person_id="I2",
            display_name="Spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={
                "I1": descendant,
                "I2": spouse,
            },
            families={},
            events={},
            root_person_id="I1",
        )

        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=3,
                    role=TraversalRole.DESCENDANT,
                    family_id="F_PARENT",
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=3,
                    role=TraversalRole.SPOUSE,
                    family_id="F1",
                    spouse_of_person_id="I1",
                ),
            ),
            family_occurrences=(),
        )

        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        spouse_placement = layout.person_placements[1]

        self.assertEqual(spouse_placement.person_id, "I2")
        self.assertEqual(spouse_placement.row_index, 1)
        self.assertEqual(spouse_placement.generation, 3)
        self.assertIs(
            spouse_placement.role,
            TraversalRole.SPOUSE,
        )
        self.assertEqual(spouse_placement.family_id, "F1")
        self.assertEqual(
            spouse_placement.spouse_of_person_id,
            "I1",
        )
        self.assertEqual(spouse_placement.y, 50.0)

    def test_birth_representative_value_sets_person_x_start(self) -> None:
        birth = Event(
            event_id="E1",
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

        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={"E1": birth},
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

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertEqual(
            placement.x_start,
            float(date(1840, 1, 1).toordinal()),
        )
        self.assertIsNone(placement.x_end)
    def test_death_representative_value_sets_person_x_end(self) -> None:
        death = Event(
            event_id="E1",
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

        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={"E1": death},
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

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIsNone(placement.x_start)

        self.assertEqual(
            placement.x_end,
            float(date(1900, 1, 1).toordinal()),
        )
    def test_birth_and_death_set_complete_life_bar(self) -> None:
        birth = Event(
            event_id="E1",
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

        death = Event(
            event_id="E2",
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

        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
                PersonEventRef(
                    event_id="E2",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={
                "E1": birth,
                "E2": death,
            },
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

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertEqual(
            placement.x_start,
            float(date(1840, 1, 1).toordinal()),
        )
        self.assertEqual(
            placement.x_end,
            float(date(1900, 1, 1).toordinal()),
        )
        self.assertLess(
            placement.x_start,
            placement.x_end,
        )

    def test_marriage_representative_value_creates_marriage_node(self) -> None:
        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue(
                source_value="01/01/1870",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1870, 1, 1),
                normalized_maximum=date(1870, 1, 1),
                representative_value=date(1870, 1, 1),
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )

        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        spouse = Person(
            person_id="I2",
            display_name="Spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef(
                    event_id="E1",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="FAMILY",
                ),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons={"I1": descendant, "I2": spouse},
            families={"F1": family},
            events={"E1": marriage},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=1,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F1",
                    spouse_of_person_id="I1",
                ),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I2",
                    spouse_row_index=1,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
            ),
        )
        temporal_results = TemporalInferenceEngine().run(data)
        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.marriage_node_placements), 1)
        placement = layout.marriage_node_placements[0]
        self.assertEqual(placement.family_id, "F1")
        self.assertEqual(placement.descendant_person_id, "I1")
        self.assertEqual(placement.spouse_person_id, "I2")
        self.assertEqual(placement.descendant_row_index, 0)
        self.assertEqual(placement.spouse_row_index, 1)
        self.assertEqual(placement.x, float(date(1870, 1, 1).toordinal()))
        self.assertEqual(placement.y, 35.0)

    def test_family_without_marriage_date_creates_no_marriage_node(self) -> None:
        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        spouse = Person(
            person_id="I2",
            display_name="Spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons={"I1": descendant, "I2": spouse},
            families={"F1": family},
            events={},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=1,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F1",
                    spouse_of_person_id="I1",
                ),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I2",
                    spouse_row_index=1,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
            ),
        )
        temporal_results = TemporalInferenceEngine().run(data)
        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())

    def test_marriage_without_representative_value_creates_no_marriage_node(self) -> None:
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue(
                source_value="entre 1870 et 1872",
                source_calendar="GREGORIAN",
                normalized_minimum=date(1870, 1, 1),
                normalized_maximum=date(1872, 12, 31),
                representative_value=None,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )

        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        spouse = Person(
            person_id="I2",
            display_name="Spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef(
                    event_id="E1",
                    semantic_role=FamilyRoleSemantic.FAMILY,
                    source_role="FAMILY",
                ),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons={"I1": descendant, "I2": spouse},
            families={"F1": family},
            events={"E1": marriage},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=1,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F1",
                    spouse_of_person_id="I1",
                ),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I2",
                    spouse_row_index=1,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
            ),
        )
        temporal_results = TemporalInferenceEngine().run(data)
        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        marriage_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        self.assertIn(marriage_target, model.temporal_results)
        marriage_result = model.temporal_results[marriage_target]
        self.assertIsNone(marriage_result.estimate.representative_value)

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())

    def test_second_marriage_creates_vertical_remarriage_segment(self) -> None:
        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1", "F2"),
        )
        first_spouse = Person(
            person_id="I2",
            display_name="First spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        second_spouse = Person(
            person_id="I3",
            display_name="Second spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F2",),
        )
        events = {}
        families = {}
        for family_id, spouse_id, event_id, year in (
            ("F1", "I2", "E1", 1870),
            ("F2", "I3", "E2", 1890),
        ):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue(
                    source_value=f"01/01/{year}",
                    source_calendar="GREGORIAN",
                    normalized_minimum=date(year, 1, 1),
                    normalized_maximum=date(year, 1, 1),
                    representative_value=date(year, 1, 1),
                    value_origin=ValueOrigin.GRAMPS,
                    source_quality=SourceQuality.NORMAL,
                    evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                    certainty=CertaintyLevel.CERTAIN,
                ),
            )
            families[family_id] = Family(
                family_id=family_id,
                parent1_id="I1",
                parent2_id=spouse_id,
                event_refs=(
                    FamilyEventRef(
                        event_id=event_id,
                        semantic_role=FamilyRoleSemantic.FAMILY,
                        source_role="FAMILY",
                    ),
                ),
                child_refs=(),
            )
        data = RawGenealogyData(
            persons={
                "I1": descendant,
                "I2": first_spouse,
                "I3": second_spouse,
            },
            families=families,
            events=events,
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=1,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F1",
                    spouse_of_person_id="I1",
                ),
                TraversalRow(
                    person_id="I3",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F2",
                    spouse_of_person_id="I1",
                ),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I2",
                    spouse_row_index=1,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F2",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I3",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
            ),
        )
        temporal_results = TemporalInferenceEngine().run(data)
        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.marriage_node_placements), 2)
        first_marriage, second_marriage = layout.marriage_node_placements
        self.assertEqual(first_marriage.family_id, "F1")
        self.assertEqual(first_marriage.x, float(date(1870, 1, 1).toordinal()))
        self.assertEqual(first_marriage.y, 35.0)
        self.assertEqual(second_marriage.family_id, "F2")
        self.assertEqual(second_marriage.x, float(date(1890, 1, 1).toordinal()))
        self.assertEqual(second_marriage.y, 50.0)

        self.assertEqual(len(layout.remarriage_segment_placements), 1)
        segment = layout.remarriage_segment_placements[0]
        self.assertEqual(segment.person_id, "I1")
        self.assertEqual(segment.x, float(date(1890, 1, 1).toordinal()))
        self.assertEqual(segment.y_start, 20.0)
        self.assertEqual(segment.y_end, 50.0)

    def test_three_marriages_create_two_remarriage_segments(self) -> None:
        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1", "F2", "F3"),
        )
        first_spouse = Person(
            person_id="I2",
            display_name="First spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        second_spouse = Person(
            person_id="I3",
            display_name="Second spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F2",),
        )
        third_spouse = Person(
            person_id="I4",
            display_name="Third spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F3",),
        )
        events = {}
        families = {}
        for family_id, spouse_id, event_id, year in (
            ("F1", "I2", "E1", 1870),
            ("F2", "I3", "E2", 1890),
            ("F3", "I4", "E3", 1910),
        ):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue(
                    source_value=f"01/01/{year}",
                    source_calendar="GREGORIAN",
                    normalized_minimum=date(year, 1, 1),
                    normalized_maximum=date(year, 1, 1),
                    representative_value=date(year, 1, 1),
                    value_origin=ValueOrigin.GRAMPS,
                    source_quality=SourceQuality.NORMAL,
                    evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                    certainty=CertaintyLevel.CERTAIN,
                ),
            )
            families[family_id] = Family(
                family_id=family_id,
                parent1_id="I1",
                parent2_id=spouse_id,
                event_refs=(
                    FamilyEventRef(
                        event_id=event_id,
                        semantic_role=FamilyRoleSemantic.FAMILY,
                        source_role="FAMILY",
                    ),
                ),
                child_refs=(),
            )
        data = RawGenealogyData(
            persons={
                "I1": descendant,
                "I2": first_spouse,
                "I3": second_spouse,
                "I4": third_spouse,
            },
            families=families,
            events=events,
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow(
                    person_id="I1",
                    generation=1,
                    role=TraversalRole.DESCENDANT,
                    family_id=None,
                    spouse_of_person_id=None,
                ),
                TraversalRow(
                    person_id="I2",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F1",
                    spouse_of_person_id="I1",
                ),
                TraversalRow(
                    person_id="I3",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F2",
                    spouse_of_person_id="I1",
                ),
                TraversalRow(
                    person_id="I4",
                    generation=1,
                    role=TraversalRole.SPOUSE,
                    family_id="F3",
                    spouse_of_person_id="I1",
                ),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I2",
                    spouse_row_index=1,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F2",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I3",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F3",
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id="I4",
                    spouse_row_index=3,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
            ),
        )
        temporal_results = TemporalInferenceEngine().run(data)
        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.marriage_node_placements), 3)
        self.assertEqual(len(layout.remarriage_segment_placements), 2)

        first_segment, second_segment = layout.remarriage_segment_placements
        self.assertEqual(first_segment.person_id, "I1")
        self.assertEqual(first_segment.x, float(date(1890, 1, 1).toordinal()))
        self.assertEqual(first_segment.y_start, 20.0)
        self.assertEqual(first_segment.y_end, 50.0)

        self.assertEqual(second_segment.person_id, "I1")
        self.assertEqual(second_segment.x, float(date(1910, 1, 1).toordinal()))
        self.assertEqual(second_segment.y_start, 20.0)
        self.assertEqual(second_segment.y_end, 65.0)

if __name__ == "__main__":
    unittest.main()