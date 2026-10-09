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
    def test_already_described_family_reserves_visual_rank_after_spouse(self) -> None:
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",) if person_id in ("I1", "I2") else (),
            )
            for person_id in ("I0", "I1", "I2", "I3")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={},
            root_person_id="I0",
        )
        traversal = TraversalResult(
            root_person_id="I0",
            rows=(
                TraversalRow("I0", 1, TraversalRole.ROOT, None, None),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 2, TraversalRole.DESCENDANT, None, None),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=1,
                    spouse_person_id="I2",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=3,
                    spouse_person_id="I2",
                    spouse_row_index=4,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(
            tuple(placement.row_index for placement in layout.person_placements),
            tuple(range(len(traversal.rows))),
        )
        for placement in layout.person_placements[:5]:
            self.assertEqual(placement.visual_rank, placement.row_index)
        first_person_after_spouse = layout.person_placements[5]
        self.assertEqual(
            first_person_after_spouse.visual_rank,
            first_person_after_spouse.row_index + 1,
        )

    def test_already_described_family_creates_branch_reference_placement(self) -> None:
        from descendants_timeline.layout.branch_reference_placement import (
            BranchReferencePlacement,
        )

        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",) if person_id in ("I1", "I2") else (),
            )
            for person_id in ("I0", "I1", "I2", "I3")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={},
            root_person_id="I0",
        )
        traversal = TraversalResult(
            root_person_id="I0",
            rows=(
                TraversalRow("I0", 1, TraversalRole.ROOT, None, None),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 2, TraversalRole.DESCENDANT, None, None),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=1,
                    spouse_person_id="I2",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=3,
                    spouse_person_id="I2",
                    spouse_row_index=4,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.branch_reference_placements), 1)
        reference = layout.branch_reference_placements[0]
        self.assertIsInstance(reference, BranchReferencePlacement)
        occurrence = traversal.family_occurrences[1]
        self.assertEqual(reference.family_id, occurrence.family_id)
        self.assertEqual(
            reference.descendant_row_index, occurrence.descendant_row_index
        )
        self.assertEqual(reference.spouse_row_index, occurrence.spouse_row_index)
        self.assertEqual(
            reference.referenced_row_index, occurrence.referenced_row_index
        )
        spouse_placement = layout.person_placements[occurrence.spouse_row_index]
        self.assertEqual(reference.visual_rank, spouse_placement.visual_rank + 1)
        self.assertEqual(
            reference.y,
            LayoutEngine.DEFAULT_TOP_MARGIN
            + reference.visual_rank * LayoutEngine.DEFAULT_ROW_HEIGHT,
        )

    def test_branch_reference_without_horizontal_bounds_keeps_x_none(self) -> None:
        from descendants_timeline.layout.branch_reference_placement import (
            BranchReferencePlacement,
        )

        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",) if person_id in ("I1", "I2") else (),
            )
            for person_id in ("I0", "I1", "I2", "I3")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={},
            root_person_id="I0",
        )
        traversal = TraversalResult(
            root_person_id="I0",
            rows=(
                TraversalRow("I0", 1, TraversalRole.ROOT, None, None),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 2, TraversalRole.DESCENDANT, None, None),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=1,
                    spouse_person_id="I2",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=3,
                    spouse_person_id="I2",
                    spouse_row_index=4,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.branch_reference_placements), 1)
        reference = layout.branch_reference_placements[0]
        self.assertIsInstance(reference, BranchReferencePlacement)
        occurrence = traversal.family_occurrences[1]
        self.assertEqual(reference.family_id, occurrence.family_id)
        self.assertEqual(
            reference.descendant_row_index, occurrence.descendant_row_index
        )
        self.assertEqual(reference.spouse_row_index, occurrence.spouse_row_index)
        self.assertEqual(
            reference.referenced_row_index, occurrence.referenced_row_index
        )
        spouse_placement = layout.person_placements[occurrence.spouse_row_index]
        self.assertEqual(reference.visual_rank, spouse_placement.visual_rank + 1)
        self.assertEqual(
            reference.y,
            LayoutEngine.DEFAULT_TOP_MARGIN
            + reference.visual_rank * LayoutEngine.DEFAULT_ROW_HEIGHT,
        )
        self.assertIsNone(reference.x)

    def test_branch_reference_is_horizontally_centered_under_couple(self) -> None:
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(
                        event_id="E" + person_id,
                        semantic_role=EventRoleSemantic.PRINCIPAL,
                        source_role="PRIMARY",
                    ),
                ) if person_id in ("I1", "I2") else (),
                parent_family_ids=(),
                family_ids=("F1",) if person_id in ("I1", "I2") else (),
            )
            for person_id in ("I0", "I1", "I2", "I3")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        events = {
            "E" + person_id: Event(
                event_id="E" + person_id,
                source_type="BIRTH",
                semantic=EventSemantic.BIRTH,
                date=TemporalValue(
                    source_value=str(birth_date),
                    source_calendar="GREGORIAN",
                    normalized_minimum=birth_date,
                    normalized_maximum=birth_date,
                    representative_value=birth_date,
                    value_origin=ValueOrigin.GRAMPS,
                    source_quality=SourceQuality.NORMAL,
                    evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                    certainty=CertaintyLevel.CERTAIN,
                ),
            )
            for person_id, birth_date in (
                ("I1", date(1840, 1, 1)),
                ("I2", date(1845, 1, 1)),
            )
        }
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I0",
        )
        traversal = TraversalResult(
            root_person_id="I0",
            rows=(
                TraversalRow("I0", 1, TraversalRole.ROOT, None, None),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 2, TraversalRole.DESCENDANT, None, None),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=1,
                    spouse_person_id="I2",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=3,
                    spouse_person_id="I2",
                    spouse_row_index=4,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
            ),
        )
        model = TimelineModelBuilder().build(
            data=data,
            traversal=traversal,
            temporal_results=TemporalInferenceEngine().run(data),
        )

        layout = LayoutEngine().build(model)

        occurrence = traversal.family_occurrences[1]
        reference = next(
            reference
            for reference in layout.branch_reference_placements
            if reference.descendant_row_index == occurrence.descendant_row_index
            and reference.spouse_row_index == occurrence.spouse_row_index
        )
        descendant = layout.person_placements[occurrence.descendant_row_index]
        spouse = layout.person_placements[occurrence.spouse_row_index]
        expected_x = (
            min(descendant.bar_x_start, spouse.bar_x_start)
            + max(descendant.bar_x_end, spouse.bar_x_end)
        ) / 2
        self.assertNotEqual(expected_x, 0.0)
        self.assertEqual(reference.x, expected_x)

    def test_multiple_already_described_families_create_distinct_branch_references(self) -> None:
        from descendants_timeline.layout.branch_reference_placement import (
            BranchReferencePlacement,
        )

        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",) if person_id in ("I1", "I2") else (),
            )
            for person_id in ("I0", "I1", "I2", "I3")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={},
            root_person_id="I0",
        )
        traversal = TraversalResult(
            root_person_id="I0",
            rows=(
                TraversalRow("I0", 1, TraversalRole.ROOT, None, None),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 2, TraversalRole.DESCENDANT, None, None),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=1,
                    spouse_person_id="I2",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=3,
                    spouse_person_id="I2",
                    spouse_row_index=4,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=5,
                    spouse_person_id="I2",
                    spouse_row_index=6,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.branch_reference_placements), 2)
        self.assertEqual(
            tuple(
                reference.spouse_row_index
                for reference in layout.branch_reference_placements
            ),
            (4, 6),
        )
        for reference, occurrence in zip(
            layout.branch_reference_placements, traversal.family_occurrences[1:]
        ):
            self.assertIsInstance(reference, BranchReferencePlacement)
            self.assertEqual(reference.family_id, occurrence.family_id)
            self.assertEqual(
                reference.descendant_row_index, occurrence.descendant_row_index
            )
            self.assertEqual(reference.spouse_row_index, occurrence.spouse_row_index)
            self.assertEqual(
                reference.referenced_row_index, occurrence.referenced_row_index
            )
            spouse = layout.person_placements[occurrence.spouse_row_index]
            self.assertEqual(reference.visual_rank, spouse.visual_rank + 1)
            self.assertEqual(
                reference.y,
                LayoutEngine.DEFAULT_TOP_MARGIN
                + reference.visual_rank * LayoutEngine.DEFAULT_ROW_HEIGHT,
            )
        person_after_references = layout.person_placements[7]
        self.assertEqual(person_after_references.person_id, "I3")
        self.assertEqual(person_after_references.row_index, 7)
        self.assertEqual(
            person_after_references.visual_rank, person_after_references.row_index + 2
        )

    def test_person_y_uses_visual_rank_after_already_described_family(self) -> None:
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",) if person_id in ("I1", "I2") else (),
            )
            for person_id in ("I0", "I1", "I2", "I3")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={},
            root_person_id="I0",
        )
        traversal = TraversalResult(
            root_person_id="I0",
            rows=(
                TraversalRow("I0", 1, TraversalRole.ROOT, None, None),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I1", 2, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 2, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 2, TraversalRole.DESCENDANT, None, None),
            ),
            family_occurrences=(
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=1,
                    spouse_person_id="I2",
                    spouse_row_index=2,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                ),
                TraversalFamilyOccurrence(
                    family_id="F1",
                    descendant_person_id="I1",
                    descendant_row_index=3,
                    spouse_person_id="I2",
                    spouse_row_index=4,
                    state=FamilyTraversalState.ALREADY_DESCRIBED,
                    referenced_row_index=1,
                ),
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[5]
        self.assertEqual(placement.visual_rank, placement.row_index + 1)
        self.assertEqual(
            placement.y,
            LayoutEngine.DEFAULT_TOP_MARGIN
            + placement.visual_rank * LayoutEngine.DEFAULT_ROW_HEIGHT,
        )
        self.assertEqual(
            placement.y
            - (
                LayoutEngine.DEFAULT_TOP_MARGIN
                + placement.row_index * LayoutEngine.DEFAULT_ROW_HEIGHT
            ),
            LayoutEngine.DEFAULT_ROW_HEIGHT,
        )

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
        self.assertEqual(
            placement.x_start,
            LayoutEngine.LOGICAL_X_ORIGIN,
        )
        self.assertEqual(
            placement.x_end,
            placement.x_start + LayoutEngine.LIFE_SPAN_OFFSET,
        )
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

    def test_birth_representative_value_sets_person_x_start_kind(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind

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

        self.assertIs(placement.x_start_kind, PositionKind.REPRESENTATIVE)

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
        from descendants_timeline.layout.timeline_scale import TimelineScale
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        death_result = model.temporal_results[death_target]
        self.assertIsNone(death_result.estimate.representative_value)
        self.assertIsNotNone(death_result.reconciled_domain.principal_minimum)
        self.assertEqual(
            placement.x_end,
            TimelineScale().date_to_x(
                death_result.reconciled_domain.principal_minimum.value
            ),
        )
    def test_birth_domain_display_sets_person_x_start_kind(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind

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

        self.assertIs(placement.x_start_kind, PositionKind.DOMAIN_DISPLAY)

    def test_death_representative_value_sets_person_x_end_kind(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind

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

        self.assertIs(placement.x_end_kind, PositionKind.REPRESENTATIVE)

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

        from descendants_timeline.layout.timeline_scale import TimelineScale
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = model.temporal_results[birth_target]
        self.assertIsNone(birth_result.estimate.representative_value)
        self.assertIsNotNone(birth_result.reconciled_domain.principal_maximum)
        self.assertEqual(
            placement.x_start,
            TimelineScale().date_to_x(
                birth_result.reconciled_domain.principal_maximum.value
            ),
        )

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

    def test_divorce_representative_value_creates_divorce_node(self) -> None:
        from descendants_timeline.layout.divorce_node_placement import (
            DivorceNodePlacement,
        )
        from descendants_timeline.layout.timeline_scale import TimelineScale
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        divorce = Event(
            event_id="E1",
            source_type="DIVORCE",
            semantic=EventSemantic.DIVORCE,
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
            events={"E1": divorce},
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

        divorce_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.DIVORCE,
        )
        self.assertEqual(
            model.temporal_results[divorce_target].estimate.representative_value,
            date(1870, 1, 1),
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.divorce_node_placements), 1)
        placement = layout.divorce_node_placements[0]
        self.assertIsInstance(placement, DivorceNodePlacement)
        self.assertEqual(placement.family_id, "F1")
        self.assertEqual(placement.descendant_person_id, "I1")
        self.assertEqual(placement.spouse_person_id, "I2")
        self.assertEqual(placement.descendant_row_index, 0)
        self.assertEqual(placement.spouse_row_index, 1)
        self.assertEqual(placement.x, TimelineScale().date_to_x(date(1870, 1, 1)))
        descendant_placement, spouse_placement = layout.person_placements
        self.assertEqual(
            placement.y,
            (descendant_placement.y + spouse_placement.y) / 2,
        )

    def test_divorce_without_display_value_creates_no_divorce_node(self) -> None:
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        divorce = Event(
            event_id="E1",
            source_type="DIVORCE",
            semantic=EventSemantic.DIVORCE,
            date=TemporalValue.unknown(),
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
            events={"E1": divorce},
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

        divorce_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.DIVORCE,
        )
        self.assertIn(divorce_target, model.temporal_results)
        divorce_result = model.temporal_results[divorce_target]
        self.assertIsNone(divorce_result.estimate.representative_value)
        self.assertIsNone(divorce_result.reconciled_domain.principal_minimum)
        self.assertIsNone(divorce_result.reconciled_domain.principal_maximum)
        self.assertIsNone(determine_display_value(divorce_result))

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.divorce_node_placements, ())

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

    def test_marriage_without_representative_value_uses_domain_midpoint(self) -> None:
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

        from descendants_timeline.layout.timeline_scale import TimelineScale

        self.assertIsNone(marriage_result.estimate.representative_value)
        self.assertEqual(len(layout.marriage_node_placements), 1)
        placement = layout.marriage_node_placements[0]
        minimum = marriage_result.reconciled_domain.principal_minimum.value
        maximum = marriage_result.reconciled_domain.principal_maximum.value
        midpoint = minimum + (maximum - minimum) // 2
        self.assertEqual(placement.x, TimelineScale().date_to_x(midpoint))

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

    def test_death_domain_display_sets_person_x_end_kind(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
            ReconciledTemporalDomain,
        )
        from descendants_timeline.inference.temporal_estimate import TemporalEstimate
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        target_entry = TemporalTargetEntry(
            target=death_target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )
        constraint_resolution = ConstraintResolution(
            target=death_target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )
        reconciled_domain = ReconciledTemporalDomain(
            target=death_target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=date(1900, 1, 1),
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        death_result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={death_target: death_result},
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIs(placement.x_end_kind, PositionKind.DOMAIN_DISPLAY)

    def test_death_without_representative_value_uses_domain_minimum_for_x_end(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBound,
            ReconciledBoundOrigin,
            ReconciledTemporalDomain,
        )
        from descendants_timeline.inference.temporal_estimate import TemporalEstimate
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.layout.timeline_scale import TimelineScale
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        target_entry = TemporalTargetEntry(
            target=death_target,
            gramps_value=TemporalValue.unknown(),
            anomalies=(),
        )
        constraint_resolution = ConstraintResolution(
            target=death_target,
            hard_minimum=None,
            hard_maximum=None,
            refined_minimum=None,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )
        reconciled_domain = ReconciledTemporalDomain(
            target=death_target,
            gramps_value=target_entry.gramps_value,
            constraint_resolution=constraint_resolution,
            principal_minimum=ReconciledBound(
                value=date(1900, 1, 1),
                origin=ReconciledBoundOrigin.GRAMPS,
            ),
            principal_maximum=None,
            conflict_type=None,
            conflicting_bounds=(),
        )
        death_result = TemporalInferenceResult(
            target_entry=target_entry,
            constraint_resolution=constraint_resolution,
            reconciled_domain=reconciled_domain,
            estimate=TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.UNDETERMINED,
            ),
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={death_target: death_result},
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]
        self.assertEqual(placement.person_id, "I1")
        self.assertIsNone(death_result.estimate.representative_value)
        self.assertEqual(
            placement.x_end,
            TimelineScale().date_to_x(
                death_result.reconciled_domain.principal_minimum.value
            ),
        )

    def test_reversed_life_bar_receives_short_visual_length(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledTemporalDomain,
        )
        from descendants_timeline.inference.temporal_estimate import TemporalEstimate
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.layout.life_bar_kind import LifeBarKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_date = date(1900, 1, 1)
        temporal_results = {}
        for semantic, representative_value, certainty in (
            (TargetSemantic.BIRTH, birth_date, CertaintyLevel.CERTAIN),
            (TargetSemantic.DEATH, date(1840, 1, 1), CertaintyLevel.CERTAIN),
        ):
            target = TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I1",
                semantic=semantic,
            )
            target_entry = TemporalTargetEntry(
                target=target,
                gramps_value=TemporalValue.unknown(),
                anomalies=(),
            )
            constraint_resolution = ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
            reconciled_domain = ReconciledTemporalDomain(
                target=target,
                gramps_value=target_entry.gramps_value,
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )
            temporal_results[target] = TemporalInferenceResult(
                target_entry=target_entry,
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=TemporalEstimate(
                    representative_value=representative_value,
                    certainty=certainty,
                ),
            )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIs(placement.x_start_kind, PositionKind.REPRESENTATIVE)
        self.assertIs(placement.x_end_kind, PositionKind.REPRESENTATIVE)
        self.assertGreater(placement.x_start, placement.x_end)
        self.assertIs(placement.life_bar_kind, LifeBarKind.REVERSED)
        self.assertEqual(
            placement.short_bar_length,
            LayoutEngine.LIFE_SPAN_OFFSET / 2,
        )

    def test_zero_length_life_bar_receives_short_visual_length(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledTemporalDomain,
        )
        from descendants_timeline.inference.temporal_estimate import TemporalEstimate
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.layout.life_bar_kind import LifeBarKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_date = date(1900, 1, 1)
        temporal_results = {}
        for semantic, representative_value, certainty in (
            (TargetSemantic.BIRTH, birth_date, CertaintyLevel.CERTAIN),
            (TargetSemantic.DEATH, birth_date, CertaintyLevel.CERTAIN),
        ):
            target = TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I1",
                semantic=semantic,
            )
            target_entry = TemporalTargetEntry(
                target=target,
                gramps_value=TemporalValue.unknown(),
                anomalies=(),
            )
            constraint_resolution = ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
            reconciled_domain = ReconciledTemporalDomain(
                target=target,
                gramps_value=target_entry.gramps_value,
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )
            temporal_results[target] = TemporalInferenceResult(
                target_entry=target_entry,
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=TemporalEstimate(
                    representative_value=representative_value,
                    certainty=certainty,
                ),
            )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIs(placement.x_start_kind, PositionKind.REPRESENTATIVE)
        self.assertIs(placement.x_end_kind, PositionKind.REPRESENTATIVE)
        self.assertEqual(placement.x_start, placement.x_end)
        self.assertIs(placement.life_bar_kind, LifeBarKind.ZERO_LENGTH)
        self.assertEqual(
            placement.short_bar_length,
            LayoutEngine.LIFE_SPAN_OFFSET / 2,
        )

    def test_life_span_offset_sets_person_x_end_kind_to_visual_fallback(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledTemporalDomain,
        )
        from descendants_timeline.inference.temporal_estimate import TemporalEstimate
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_date = date(1840, 1, 1)
        temporal_results = {}
        for semantic, representative_value, certainty in (
            (TargetSemantic.BIRTH, birth_date, CertaintyLevel.CERTAIN),
            (TargetSemantic.DEATH, None, CertaintyLevel.UNDETERMINED),
        ):
            target = TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I1",
                semantic=semantic,
            )
            target_entry = TemporalTargetEntry(
                target=target,
                gramps_value=TemporalValue.unknown(),
                anomalies=(),
            )
            constraint_resolution = ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
            reconciled_domain = ReconciledTemporalDomain(
                target=target,
                gramps_value=target_entry.gramps_value,
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )
            temporal_results[target] = TemporalInferenceResult(
                target_entry=target_entry,
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=TemporalEstimate(
                    representative_value=representative_value,
                    certainty=certainty,
                ),
            )
        death_result = temporal_results[target]
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIs(placement.x_end_kind, PositionKind.VISUAL_FALLBACK)

    def test_death_without_display_value_uses_life_span_offset_from_x_start(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledTemporalDomain,
        )
        from descendants_timeline.inference.temporal_estimate import TemporalEstimate
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.layout.temporal_display_value import (
            determine_display_value,
        )
        from descendants_timeline.layout.timeline_scale import TimelineScale
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_date = date(1840, 1, 1)
        temporal_results = {}
        for semantic, representative_value, certainty in (
            (TargetSemantic.BIRTH, birth_date, CertaintyLevel.CERTAIN),
            (TargetSemantic.DEATH, None, CertaintyLevel.UNDETERMINED),
        ):
            target = TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I1",
                semantic=semantic,
            )
            target_entry = TemporalTargetEntry(
                target=target,
                gramps_value=TemporalValue.unknown(),
                anomalies=(),
            )
            constraint_resolution = ConstraintResolution(
                target=target,
                hard_minimum=None,
                hard_maximum=None,
                refined_minimum=None,
                refined_maximum=None,
                conflict_type=None,
                conflicting_constraints=(),
            )
            reconciled_domain = ReconciledTemporalDomain(
                target=target,
                gramps_value=target_entry.gramps_value,
                constraint_resolution=constraint_resolution,
                principal_minimum=None,
                principal_maximum=None,
                conflict_type=None,
                conflicting_bounds=(),
            )
            temporal_results[target] = TemporalInferenceResult(
                target_entry=target_entry,
                constraint_resolution=constraint_resolution,
                reconciled_domain=reconciled_domain,
                estimate=TemporalEstimate(
                    representative_value=representative_value,
                    certainty=certainty,
                ),
            )
        death_result = temporal_results[target]
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]
        self.assertEqual(placement.person_id, "I1")
        self.assertEqual(placement.x_start, TimelineScale().date_to_x(birth_date))
        self.assertIsNone(death_result.estimate.representative_value)
        self.assertIsNone(death_result.reconciled_domain.principal_minimum)
        self.assertIsNone(death_result.reconciled_domain.principal_maximum)
        self.assertIsNone(determine_display_value(death_result))
        self.assertEqual(
            placement.x_end,
            placement.x_start + LayoutEngine.LIFE_SPAN_OFFSET,
        )

    def test_spouse_fallback_sets_person_x_start_kind_to_visual_fallback(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
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
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
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
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow("I1", 1, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 1, TraversalRole.SPOUSE, "F1", "I1"),
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
        spouse_birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I2",
            semantic=TargetSemantic.BIRTH,
        )
        spouse_birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == spouse_birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={spouse_birth_target: spouse_birth_result},
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIs(placement.x_start_kind, PositionKind.VISUAL_FALLBACK)

    def test_birth_without_display_value_uses_later_spouse_own_x_start(self) -> None:
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
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
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
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
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow("I1", 1, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 1, TraversalRole.SPOUSE, "F1", "I1"),
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
        spouse_birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I2",
            semantic=TargetSemantic.BIRTH,
        )
        spouse_birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == spouse_birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={spouse_birth_target: spouse_birth_result},
        )

        layout = LayoutEngine().build(model)

        placement_I1, placement_I2 = layout.person_placements
        self.assertEqual(placement_I1.person_id, "I1")
        self.assertEqual(placement_I1.row_index, 0)
        self.assertEqual(placement_I2.person_id, "I2")
        self.assertEqual(placement_I2.row_index, 1)
        self.assertEqual(spouse_birth_result.estimate.representative_value, birth_date)
        self.assertEqual(placement_I2.x_start, float(birth_date.toordinal()))
        self.assertEqual(placement_I1.x_start, placement_I2.x_start)

    def test_spouse_without_display_value_uses_earlier_descendant_own_x_start(self) -> None:
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
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
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
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
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow("I1", 1, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 1, TraversalRole.SPOUSE, "F1", "I1"),
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
        descendant_birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        descendant_birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == descendant_birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={descendant_birth_target: descendant_birth_result},
        )

        # Le fallback doit être résolu en seconde passe, même avec un ancrage antérieur.
        layout = LayoutEngine().build(model)

        placement_I1, placement_I2 = layout.person_placements
        self.assertEqual(placement_I1.person_id, "I1")
        self.assertEqual(placement_I1.row_index, 0)
        self.assertEqual(placement_I2.person_id, "I2")
        self.assertEqual(placement_I2.row_index, 1)
        self.assertEqual(descendant_birth_result.estimate.representative_value, birth_date)
        self.assertEqual(placement_I1.x_start, float(birth_date.toordinal()))
        self.assertEqual(placement_I2.x_start, placement_I1.x_start)

    def test_birth_fallback_uses_first_usable_spouse_in_gramps_family_order(self) -> None:
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
        )

        first_birth_date = date(1850, 1, 1)
        second_birth_date = date(1840, 1, 1)
        descendant = Person(
            person_id="I1",
            display_name="Descendant",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1", "F2"),
        )
        persons = {"I1": descendant}
        families = {}
        events = {}
        for family_id, spouse_id, event_id, birth_date in (
            ("F1", "I2", "E1", first_birth_date),
            ("F2", "I3", "E2", second_birth_date),
        ):
            persons[spouse_id] = Person(
                person_id=spouse_id,
                display_name=spouse_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(
                        event_id=event_id,
                        semantic_role=EventRoleSemantic.PRINCIPAL,
                        source_role="PRIMARY",
                    ),
                ),
                parent_family_ids=(),
                family_ids=(family_id,),
            )
            families[family_id] = Family(
                family_id=family_id,
                parent1_id="I1",
                parent2_id=spouse_id,
                event_refs=(),
                child_refs=(),
            )
            events[event_id] = Event(
                event_id=event_id,
                source_type="BIRTH",
                semantic=EventSemantic.BIRTH,
                date=TemporalValue(
                    source_value=birth_date.isoformat(),
                    source_calendar="GREGORIAN",
                    normalized_minimum=birth_date,
                    normalized_maximum=birth_date,
                    representative_value=birth_date,
                    value_origin=ValueOrigin.GRAMPS,
                    source_quality=SourceQuality.NORMAL,
                    evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                    certainty=CertaintyLevel.CERTAIN,
                ),
            )
        data = RawGenealogyData(
            persons=persons,
            families=families,
            events=events,
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow("I1", 1, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 1, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 1, TraversalRole.SPOUSE, "F2", "I1"),
            ),
            family_occurrences=tuple(
                TraversalFamilyOccurrence(
                    family_id=family_id,
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id=spouse_id,
                    spouse_row_index=row_index,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                )
                for family_id, spouse_id, row_index in (
                    ("F1", "I2", 1),
                    ("F2", "I3", 2),
                )
            ),
        )
        temporal_results = {
            result.target_entry.target: result
            for result in TemporalInferenceEngine().run(data)
            if (
                result.target_entry.target.owner_type is TemporalOwnerType.PERSON
                and result.target_entry.target.owner_id in ("I2", "I3")
                and result.target_entry.target.semantic is TargetSemantic.BIRTH
            )
        }
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        layout = LayoutEngine().build(model)

        placement_I1, placement_I2, placement_I3 = layout.person_placements
        self.assertEqual(descendant.family_ids, ("F1", "F2"))
        self.assertEqual(
            tuple(occurrence.family_id for occurrence in traversal.family_occurrences),
            ("F1", "F2"),
        )
        self.assertEqual(placement_I2.x_start, float(first_birth_date.toordinal()))
        self.assertEqual(placement_I3.x_start, float(second_birth_date.toordinal()))
        self.assertLess(placement_I3.x_start, placement_I2.x_start)
        self.assertEqual(placement_I1.x_start, placement_I2.x_start)
        self.assertNotEqual(placement_I1.x_start, placement_I3.x_start)

    def test_birth_fallback_skips_unusable_spouse_in_gramps_family_order(self) -> None:
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        persons = {}
        for person_id, family_ids, event_refs in (
            ("I1", ("F1", "F2"), ()),
            ("I2", ("F1",), ()),
            (
                "I3",
                ("F2",),
                (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            ),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=event_refs,
                parent_family_ids=(),
                family_ids=family_ids,
            )
        families = {
            family_id: Family(
                family_id=family_id,
                parent1_id="I1",
                parent2_id=spouse_id,
                event_refs=(),
                child_refs=(),
            )
            for family_id, spouse_id in (("F1", "I2"), ("F2", "I3"))
        }
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families=families,
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = TraversalResult(
            root_person_id="I1",
            rows=(
                TraversalRow("I1", 1, TraversalRole.DESCENDANT, None, None),
                TraversalRow("I2", 1, TraversalRole.SPOUSE, "F1", "I1"),
                TraversalRow("I3", 1, TraversalRole.SPOUSE, "F2", "I1"),
            ),
            family_occurrences=tuple(
                TraversalFamilyOccurrence(
                    family_id=family_id,
                    descendant_person_id="I1",
                    descendant_row_index=0,
                    spouse_person_id=spouse_id,
                    spouse_row_index=row_index,
                    state=FamilyTraversalState.EXPLORED,
                    referenced_row_index=None,
                )
                for family_id, spouse_id, row_index in (
                    ("F1", "I2", 1),
                    ("F2", "I3", 2),
                )
            ),
        )
        usable_birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I3",
            semantic=TargetSemantic.BIRTH,
        )
        usable_birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == usable_birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={usable_birth_target: usable_birth_result},
        )

        for person_id in ("I1", "I2"):
            self.assertEqual(data.persons[person_id].event_refs, ())
            self.assertNotIn(
                TemporalTarget(
                    owner_type=TemporalOwnerType.PERSON,
                    owner_id=person_id,
                    semantic=TargetSemantic.BIRTH,
                ),
                model.temporal_results,
            )
        self.assertEqual(data.persons["I1"].family_ids, ("F1", "F2"))
        self.assertEqual(
            tuple(occurrence.family_id for occurrence in traversal.family_occurrences),
            ("F1", "F2"),
        )
        self.assertEqual(usable_birth_result.estimate.representative_value, birth_date)

        layout = LayoutEngine().build(model)

        placement_I1, _, placement_I3 = layout.person_placements
        self.assertEqual(placement_I3.x_start, float(birth_date.toordinal()))
        self.assertEqual(placement_I1.x_start, placement_I3.x_start)

    def test_sibling_fallback_sets_person_x_start_kind_to_visual_fallback(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        persons = {}
        for person_id, parent_family_ids, family_ids, event_refs in (
            ("I1", (), ("F1",), ()),
            (
                "I2",
                ("F1",),
                (),
                (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            ),
            ("I3", ("F1",), (), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=event_refs,
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id=None,
            event_refs=(),
            child_refs=(
                ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.NONE),
            ),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I2",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={birth_target: birth_result},
        )

        layout = LayoutEngine().build(model)

        placements = {placement.person_id: placement for placement in layout.person_placements}
        placement = placements["I3"]

        self.assertIs(placement.x_start_kind, PositionKind.VISUAL_FALLBACK)

    def test_birth_fallback_uses_previous_sibling_in_gramps_child_order(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        persons = {}
        for person_id, parent_family_ids, family_ids, event_refs in (
            ("I1", (), ("F1",), ()),
            (
                "I2",
                ("F1",),
                (),
                (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            ),
            ("I3", ("F1",), (), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=event_refs,
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id=None,
            event_refs=(),
            child_refs=(
                ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.NONE),
            ),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I2",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={birth_target: birth_result},
        )

        self.assertEqual(
            tuple(child_ref.person_id for child_ref in family.child_refs),
            ("I2", "I3"),
        )
        self.assertEqual(
            tuple(
                (row.person_id, row.family_id)
                for row in traversal.rows
                if row.role is TraversalRole.DESCENDANT
            ),
            (("I2", "F1"), ("I3", "F1")),
        )
        self.assertEqual(persons["I2"].family_ids, ())
        self.assertEqual(persons["I3"].family_ids, ())
        self.assertEqual(persons["I3"].event_refs, ())
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I3",
                semantic=TargetSemantic.BIRTH,
            ),
            model.temporal_results,
        )
        self.assertEqual(birth_result.estimate.representative_value, birth_date)

        layout = LayoutEngine().build(model)

        placements = {placement.person_id: placement for placement in layout.person_placements}
        placement_I2 = placements["I2"]
        placement_I3 = placements["I3"]
        self.assertEqual(placement_I2.x_start, float(birth_date.toordinal()))
        self.assertEqual(placement_I3.x_start, placement_I2.x_start)

    def test_birth_sibling_fallback_propagates_in_gramps_child_order(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        persons = {}
        for person_id, parent_family_ids, family_ids, event_refs in (
            ("I1", (), ("F1",), ()),
            (
                "I2",
                ("F1",),
                (),
                (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            ),
            ("I3", ("F1",), (), ()),
            ("I4", ("F1",), (), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=event_refs,
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id=None,
            event_refs=(),
            child_refs=(
                ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.NONE),
                ChildRef("I4", ChildRelation.BIRTH, ChildRelation.NONE),
            ),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I2",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={birth_target: birth_result},
        )

        self.assertEqual(
            tuple(child_ref.person_id for child_ref in family.child_refs),
            ("I2", "I3", "I4"),
        )
        self.assertEqual(
            tuple(
                (row.person_id, row.family_id)
                for row in traversal.rows
                if row.role is TraversalRole.DESCENDANT
            ),
            (("I2", "F1"), ("I3", "F1"), ("I4", "F1")),
        )
        self.assertEqual(tuple(model.temporal_results), (birth_target,))
        for person_id in ("I2", "I3", "I4"):
            self.assertEqual(persons[person_id].family_ids, ())
        for person_id in ("I3", "I4"):
            self.assertEqual(persons[person_id].event_refs, ())
            self.assertNotIn(
                TemporalTarget(
                    owner_type=TemporalOwnerType.PERSON,
                    owner_id=person_id,
                    semantic=TargetSemantic.BIRTH,
                ),
                model.temporal_results,
            )
        self.assertEqual(birth_result.estimate.representative_value, birth_date)

        layout = LayoutEngine().build(model)

        placements = {placement.person_id: placement for placement in layout.person_placements}
        placement_I2 = placements["I2"]
        placement_I3 = placements["I3"]
        placement_I4 = placements["I4"]
        self.assertEqual(placement_I2.x_start, float(birth_date.toordinal()))
        self.assertEqual(placement_I3.x_start, placement_I2.x_start)
        self.assertEqual(placement_I4.x_start, placement_I3.x_start)

    def test_birth_fallback_uses_next_sibling_when_no_previous_sibling_is_usable(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        birth_date = date(1840, 1, 1)
        persons = {}
        for person_id, parent_family_ids, family_ids, event_refs in (
            ("I1", (), ("F1",), ()),
            (
                "I3",
                ("F1",),
                (),
                (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            ),
            ("I2", ("F1",), (), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=event_refs,
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id=None,
            event_refs=(),
            child_refs=(
                ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.NONE),
            ),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I3",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={birth_target: birth_result},
        )

        self.assertEqual(
            tuple(child_ref.person_id for child_ref in family.child_refs),
            ("I2", "I3"),
        )
        self.assertEqual(
            tuple(
                (row.person_id, row.family_id)
                for row in traversal.rows
                if row.role is TraversalRole.DESCENDANT
            ),
            (("I2", "F1"), ("I3", "F1")),
        )
        self.assertEqual(tuple(model.temporal_results), (birth_target,))
        self.assertEqual(persons["I3"].family_ids, ())
        self.assertEqual(persons["I2"].family_ids, ())
        self.assertEqual(persons["I2"].event_refs, ())
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I2",
                semantic=TargetSemantic.BIRTH,
            ),
            model.temporal_results,
        )
        self.assertEqual(birth_result.estimate.representative_value, birth_date)

        layout = LayoutEngine().build(model)

        placements = {placement.person_id: placement for placement in layout.person_placements}
        placement_I2 = placements["I2"]
        placement_I3 = placements["I3"]
        self.assertEqual(placement_I3.x_start, float(birth_date.toordinal()))
        self.assertEqual(placement_I2.x_start, placement_I3.x_start)

    def test_parent_family_marriage_fallback_sets_person_x_start_kind_to_visual_fallback(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        marriage_date = date(1830, 1, 1)
        persons = {}
        for person_id, parent_family_ids, family_ids in (
            ("I1", (), ("F1",)),
            ("I2", (), ("F1",)),
            ("I3", ("F1",), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue(
                source_value="01/01/1830",
                source_calendar="GREGORIAN",
                normalized_minimum=marriage_date,
                normalized_maximum=marriage_date,
                representative_value=marriage_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
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
            child_refs=(
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.BIRTH),
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": marriage},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        marriage_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        marriage_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == marriage_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={marriage_target: marriage_result},
        )

        layout = LayoutEngine().build(model)

        placement = next(
            placement
            for placement in layout.person_placements
            if placement.person_id == "I3"
        )

        self.assertIs(placement.x_start_kind, PositionKind.VISUAL_FALLBACK)

    def test_birth_fallback_uses_parent_family_marriage_when_siblings_are_unusable(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        marriage_date = date(1830, 1, 1)
        persons = {}
        for person_id, parent_family_ids, family_ids in (
            ("I1", (), ("F1",)),
            ("I2", (), ("F1",)),
            ("I3", ("F1",), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue(
                source_value="01/01/1830",
                source_calendar="GREGORIAN",
                normalized_minimum=marriage_date,
                normalized_maximum=marriage_date,
                representative_value=marriage_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
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
            child_refs=(
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.BIRTH),
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": marriage},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        marriage_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        marriage_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == marriage_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={marriage_target: marriage_result},
        )

        child_row = next(row for row in traversal.rows if row.person_id == "I3")
        self.assertIs(child_row.role, TraversalRole.DESCENDANT)
        self.assertEqual(child_row.family_id, "F1")
        self.assertEqual(persons["I3"].event_refs, ())
        self.assertEqual(persons["I3"].family_ids, ())
        self.assertEqual(
            tuple(child_ref.person_id for child_ref in family.child_refs),
            ("I3",),
        )
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I3",
                semantic=TargetSemantic.BIRTH,
            ),
            model.temporal_results,
        )
        self.assertIn(marriage_target, model.temporal_results)
        self.assertEqual(
            model.temporal_results[marriage_target].estimate.representative_value,
            marriage_date,
        )

        layout = LayoutEngine().build(model)

        placement_I3 = next(
            placement
            for placement in layout.person_placements
            if placement.person_id == "I3"
        )
        self.assertEqual(placement_I3.x_start, float(marriage_date.toordinal()))

    def test_parent_coordinate_fallback_sets_person_x_start_kind_to_visual_fallback(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        parent_birth_date = date(1800, 1, 1)
        parent = Person(
            person_id="I1",
            display_name="Parent",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        child = Person(
            person_id="I2",
            display_name="Child",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=("F1",),
            family_ids=(),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1800",
                source_calendar="GREGORIAN",
                normalized_minimum=parent_birth_date,
                normalized_maximum=parent_birth_date,
                representative_value=parent_birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id=None,
            event_refs=(),
            child_refs=(
                ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
            ),
        )
        data = RawGenealogyData(
            persons={"I1": parent, "I2": child},
            families={"F1": family},
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        parent_birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        parent_birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == parent_birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={parent_birth_target: parent_birth_result},
        )

        layout = LayoutEngine().build(model)

        placement = next(
            placement
            for placement in layout.person_placements
            if placement.person_id == "I2"
        )

        self.assertIs(placement.x_start_kind, PositionKind.VISUAL_FALLBACK)

    def test_birth_fallback_uses_single_parent_x_start_with_visual_offset(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        parent_birth_date = date(1800, 1, 1)
        visual_offset = 365.0
        parent = Person(
            person_id="I1",
            display_name="Parent",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef(
                    event_id="E1",
                    semantic_role=EventRoleSemantic.PRINCIPAL,
                    source_role="PRIMARY",
                ),
            ),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        child = Person(
            person_id="I2",
            display_name="Child",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=("F1",),
            family_ids=(),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1800",
                source_calendar="GREGORIAN",
                normalized_minimum=parent_birth_date,
                normalized_maximum=parent_birth_date,
                representative_value=parent_birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id=None,
            event_refs=(),
            child_refs=(
                ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
            ),
        )
        data = RawGenealogyData(
            persons={"I1": parent, "I2": child},
            families={"F1": family},
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        parent_birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        parent_birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == parent_birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={parent_birth_target: parent_birth_result},
        )

        child_row = next(row for row in traversal.rows if row.person_id == "I2")
        self.assertIs(child_row.role, TraversalRole.DESCENDANT)
        self.assertEqual(child_row.family_id, "F1")
        self.assertEqual(family.parent1_id, "I1")
        self.assertIsNone(family.parent2_id)
        self.assertEqual(child.event_refs, ())
        self.assertEqual(child.family_ids, ())
        self.assertEqual(
            tuple(child_ref.person_id for child_ref in family.child_refs),
            ("I2",),
        )
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I2",
                semantic=TargetSemantic.BIRTH,
            ),
            model.temporal_results,
        )
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id="F1",
                semantic=TargetSemantic.MARRIAGE,
            ),
            model.temporal_results,
        )
        self.assertEqual(
            parent_birth_result.estimate.representative_value,
            parent_birth_date,
        )

        layout = LayoutEngine().build(model)

        placement_I1, placement_I2 = layout.person_placements
        self.assertEqual(placement_I1.person_id, "I1")
        self.assertEqual(placement_I2.person_id, "I2")
        self.assertEqual(placement_I1.x_start, float(parent_birth_date.toordinal()))
        self.assertEqual(placement_I2.x_start, placement_I1.x_start + visual_offset)

    def test_birth_fallback_uses_rightmost_parent_x_start_with_visual_offset(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        visual_offset = 365.0
        parent_birth_dates = {"I1": date(1800, 1, 1), "I2": date(1810, 1, 1)}
        persons = {}
        events = {}
        for person_id, event_id in (("I1", "E1"), ("I2", "E2")):
            birth_date = parent_birth_dates[person_id]
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(
                        event_id=event_id,
                        semantic_role=EventRoleSemantic.PRINCIPAL,
                        source_role="PRIMARY",
                    ),
                ),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            events[event_id] = Event(
                event_id=event_id,
                source_type="BIRTH",
                semantic=EventSemantic.BIRTH,
                date=TemporalValue(
                    source_value=birth_date.strftime("%d/%m/%Y"),
                    source_calendar="GREGORIAN",
                    normalized_minimum=birth_date,
                    normalized_maximum=birth_date,
                    representative_value=birth_date,
                    value_origin=ValueOrigin.GRAMPS,
                    source_quality=SourceQuality.NORMAL,
                    evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                    certainty=CertaintyLevel.CERTAIN,
                ),
            )
        persons["I3"] = Person(
            person_id="I3",
            display_name="Child",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=("F1",),
            family_ids=(),
        )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(),
            child_refs=(
                ChildRef("I3", ChildRelation.BIRTH, ChildRelation.BIRTH),
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        parent_birth_targets = {
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id=person_id,
                semantic=TargetSemantic.BIRTH,
            )
            for person_id in ("I1", "I2")
        }
        temporal_results = {
            result.target_entry.target: result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target in parent_birth_targets
        }
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=temporal_results,
        )

        child_row = next(row for row in traversal.rows if row.person_id == "I3")
        self.assertIs(child_row.role, TraversalRole.DESCENDANT)
        self.assertEqual(child_row.family_id, "F1")
        self.assertEqual(family.parent1_id, "I1")
        self.assertEqual(family.parent2_id, "I2")
        occurrence = next(
            occurrence
            for occurrence in traversal.family_occurrences
            if occurrence.family_id == "F1"
            and occurrence.state is FamilyTraversalState.EXPLORED
        )
        self.assertEqual(occurrence.descendant_person_id, "I1")
        self.assertEqual(occurrence.spouse_person_id, "I2")
        self.assertEqual(
            traversal.rows[occurrence.descendant_row_index].person_id, "I1"
        )
        self.assertIsNotNone(occurrence.spouse_row_index)
        self.assertEqual(
            traversal.rows[occurrence.spouse_row_index].person_id, "I2"
        )
        self.assertIs(
            traversal.rows[occurrence.spouse_row_index].role, TraversalRole.SPOUSE
        )
        self.assertEqual(persons["I3"].event_refs, ())
        self.assertEqual(persons["I3"].family_ids, ())
        self.assertEqual(
            tuple(child_ref.person_id for child_ref in family.child_refs),
            ("I3",),
        )
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id="I3",
                semantic=TargetSemantic.BIRTH,
            ),
            model.temporal_results,
        )
        self.assertNotIn(
            TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id="F1",
                semantic=TargetSemantic.MARRIAGE,
            ),
            model.temporal_results,
        )
        self.assertEqual(set(model.temporal_results), parent_birth_targets)
        for target in parent_birth_targets:
            self.assertEqual(
                model.temporal_results[target].estimate.representative_value,
                parent_birth_dates[target.owner_id],
            )

        layout = LayoutEngine().build(model)

        placement_I1 = layout.person_placements[occurrence.descendant_row_index]
        placement_I2 = layout.person_placements[occurrence.spouse_row_index]
        placement_I3 = next(
            placement
            for placement in layout.person_placements
            if placement.person_id == "I3"
        )
        self.assertEqual(
            placement_I1.x_start, float(parent_birth_dates["I1"].toordinal())
        )
        self.assertEqual(
            placement_I2.x_start, float(parent_birth_dates["I2"].toordinal())
        )
        self.assertGreater(placement_I2.x_start, placement_I1.x_start)
        self.assertEqual(
            placement_I3.x_start,
            max(placement_I1.x_start, placement_I2.x_start) + visual_offset,
        )
        self.assertEqual(placement_I3.x_start, placement_I2.x_start + visual_offset)

    def test_birth_parent_fallback_propagates_across_generations(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )

        root_birth_date = date(1800, 1, 1)
        visual_offset = 365.0
        persons = {}
        for person_id, parent_family_ids, family_ids, event_refs in (
            (
                "I1",
                (),
                ("F1",),
                (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            ),
            ("I2", ("F1",), ("F2",), ()),
            ("I3", ("F2",), (), ()),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=event_refs,
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
        families = {
            family_id: Family(
                family_id=family_id,
                parent1_id=parent_id,
                parent2_id=None,
                event_refs=(),
                child_refs=(
                    ChildRef(child_id, ChildRelation.BIRTH, ChildRelation.NONE),
                ),
            )
            for family_id, parent_id, child_id in (
                ("F1", "I1", "I2"),
                ("F2", "I2", "I3"),
            )
        }
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1800",
                source_calendar="GREGORIAN",
                normalized_minimum=root_birth_date,
                normalized_maximum=root_birth_date,
                representative_value=root_birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families=families,
            events={"E1": birth},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={birth_target: birth_result},
        )

        self.assertEqual(
            tuple(
                (row.person_id, row.role, row.family_id, row.generation)
                for row in traversal.rows
            ),
            (
                ("I1", TraversalRole.ROOT, None, 1),
                ("I2", TraversalRole.DESCENDANT, "F1", 2),
                ("I3", TraversalRole.DESCENDANT, "F2", 3),
            ),
        )
        self.assertEqual(tuple(model.temporal_results), (birth_target,))
        self.assertEqual(birth_result.estimate.representative_value, root_birth_date)
        for person_id in ("I2", "I3"):
            self.assertEqual(persons[person_id].event_refs, ())
        for family_id, parent_id, child_id in (
            ("F1", "I1", "I2"),
            ("F2", "I2", "I3"),
        ):
            family = families[family_id]
            self.assertEqual(family.parent1_id, parent_id)
            self.assertIsNone(family.parent2_id)
            self.assertEqual(family.event_refs, ())
            self.assertEqual(
                tuple(child_ref.person_id for child_ref in family.child_refs),
                (child_id,),
            )

        layout = LayoutEngine().build(model)

        placement_I1, placement_I2, placement_I3 = layout.person_placements
        self.assertEqual(
            tuple(
                (placement.person_id, placement.role, placement.family_id)
                for placement in layout.person_placements
            ),
            (
                ("I1", TraversalRole.ROOT, None),
                ("I2", TraversalRole.DESCENDANT, "F1"),
                ("I3", TraversalRole.DESCENDANT, "F2"),
            ),
        )
        self.assertEqual(placement_I1.x_start, float(root_birth_date.toordinal()))
        self.assertEqual(placement_I2.x_start, placement_I1.x_start + visual_offset)
        self.assertEqual(placement_I3.x_start, placement_I2.x_start + visual_offset)
        self.assertEqual(
            placement_I3.x_start, placement_I1.x_start + 2 * visual_offset
        )

    def test_logical_x_origin_sets_root_x_start_kind_to_visual_fallback(self) -> None:
        from descendants_timeline.layout.position_kind import PositionKind

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
        traversal = DescendanceTraversal().traverse(data, "I1")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        layout = LayoutEngine().build(model)

        placement = layout.person_placements[0]

        self.assertIs(placement.x_start_kind, PositionKind.VISUAL_FALLBACK)

    def test_root_without_birth_uses_logical_x_origin(self) -> None:
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
        traversal = DescendanceTraversal().traverse(data, "I1")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )
        self.assertEqual(dict(model.temporal_results), {})

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.person_placements), 1)
        placement = layout.person_placements[0]
        self.assertEqual(placement.person_id, "I1")
        self.assertIs(placement.role, TraversalRole.ROOT)
        self.assertEqual(placement.x_start, 0.0)
        self.assertEqual(
            placement.x_end, placement.x_start + LayoutEngine.LIFE_SPAN_OFFSET
        )
        self.assertEqual(placement.x_end, 3650.0)

    def test_logical_x_origin_propagates_across_generations(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation

        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
            for person_id, parent_family_ids, family_ids in (
                ("I1", (), ("F1",)),
                ("I2", ("F1",), ("F2",)),
                ("I3", ("F2",), ()),
            )
        }
        families = {
            family_id: Family(
                family_id=family_id,
                parent1_id=parent_id,
                parent2_id=None,
                event_refs=(),
                child_refs=(
                    ChildRef(child_id, ChildRelation.BIRTH, ChildRelation.NONE),
                ),
            )
            for family_id, parent_id, child_id in (
                ("F1", "I1", "I2"),
                ("F2", "I2", "I3"),
            )
        }
        data = RawGenealogyData(
            persons=persons,
            families=families,
            events={},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(data, "I1")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={},
        )

        self.assertEqual(dict(data.events), {})
        self.assertEqual(dict(model.temporal_results), {})
        self.assertEqual(
            tuple(
                (row.person_id, row.role, row.family_id, row.generation)
                for row in traversal.rows
            ),
            (
                ("I1", TraversalRole.ROOT, None, 1),
                ("I2", TraversalRole.DESCENDANT, "F1", 2),
                ("I3", TraversalRole.DESCENDANT, "F2", 3),
            ),
        )
        for person in persons.values():
            self.assertEqual(person.event_refs, ())
        for family_id, parent_id, child_id in (
            ("F1", "I1", "I2"),
            ("F2", "I2", "I3"),
        ):
            family = families[family_id]
            self.assertEqual(family.parent1_id, parent_id)
            self.assertIsNone(family.parent2_id)
            self.assertEqual(family.event_refs, ())
            self.assertEqual(
                tuple(child_ref.person_id for child_ref in family.child_refs),
                (child_id,),
            )

        layout = LayoutEngine().build(model)

        placement_I1, placement_I2, placement_I3 = layout.person_placements
        self.assertEqual(
            tuple(
                (placement.person_id, placement.role, placement.family_id)
                for placement in layout.person_placements
            ),
            (
                ("I1", TraversalRole.ROOT, None),
                ("I2", TraversalRole.DESCENDANT, "F1"),
                ("I3", TraversalRole.DESCENDANT, "F2"),
            ),
        )
        self.assertEqual(placement_I1.x_start, LayoutEngine.LOGICAL_X_ORIGIN)
        self.assertEqual(
            placement_I2.x_start, placement_I1.x_start + LayoutEngine.VISUAL_OFFSET
        )
        self.assertEqual(
            placement_I3.x_start, placement_I2.x_start + LayoutEngine.VISUAL_OFFSET
        )
        self.assertEqual(placement_I1.x_start, 0.0)
        self.assertEqual(placement_I2.x_start, 365.0)
        self.assertEqual(placement_I3.x_start, 730.0)
        for placement in (placement_I1, placement_I2, placement_I3):
            self.assertEqual(
                placement.x_end,
                placement.x_start + LayoutEngine.LIFE_SPAN_OFFSET,
            )

    def test_repeated_same_marriage_does_not_create_remarriage_segment(self) -> None:
        from descendants_timeline.model.child_ref import ChildRef, ChildRelation
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.traversal.descendance_traversal import (
            DescendanceMode,
            TraversalOptions,
        )

        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=parent_family_ids,
                family_ids=family_ids,
            )
            for person_id, parent_family_ids, family_ids in (
                ("I1", (), ("F1",)),
                ("I2", ("F1",), ("F2",)),
                ("I3", ("F1",), ("F3",)),
                ("I4", ("F2", "F3"), ("F4",)),
                ("I5", (), ("F4",)),
            )
        }
        # I4 est enfant biologique de I2 et enfant adopté de I3.
        families = {
            "F1": Family(
                family_id="F1",
                parent1_id="I1",
                parent2_id=None,
                event_refs=(),
                child_refs=(
                    ChildRef("I2", ChildRelation.BIRTH, ChildRelation.NONE),
                    ChildRef("I3", ChildRelation.BIRTH, ChildRelation.NONE),
                ),
            ),
            "F2": Family(
                family_id="F2",
                parent1_id="I2",
                parent2_id=None,
                event_refs=(),
                child_refs=(
                    ChildRef("I4", ChildRelation.BIRTH, ChildRelation.NONE),
                ),
            ),
            "F3": Family(
                family_id="F3",
                parent1_id="I3",
                parent2_id=None,
                event_refs=(),
                child_refs=(
                    ChildRef("I4", ChildRelation.ADOPTED, ChildRelation.NONE),
                ),
            ),
            "F4": Family(
                family_id="F4",
                parent1_id="I4",
                parent2_id="I5",
                event_refs=(
                    FamilyEventRef("E1", FamilyRoleSemantic.FAMILY, "FAMILY"),
                ),
                child_refs=(),
            ),
        }
        marriage_date = date(1850, 1, 1)
        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=TemporalValue(
                source_value="01/01/1850",
                source_calendar="GREGORIAN",
                normalized_minimum=marriage_date,
                normalized_maximum=marriage_date,
                representative_value=marriage_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        data = RawGenealogyData(
            persons=persons,
            families=families,
            events={"E1": marriage},
            root_person_id="I1",
        )
        traversal = DescendanceTraversal().traverse(
            data, "I1", TraversalOptions(mode=DescendanceMode.EXTENDED)
        )
        marriage_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F4",
            semantic=TargetSemantic.MARRIAGE,
        )
        marriage_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == marriage_target
        )
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results={marriage_target: marriage_result},
        )

        occurrences = tuple(
            occurrence
            for occurrence in traversal.family_occurrences
            if occurrence.family_id == "F4"
        )
        self.assertEqual(len(occurrences), 2)
        self.assertEqual(
            tuple(occurrence.state for occurrence in occurrences),
            (
                FamilyTraversalState.EXPLORED,
                FamilyTraversalState.ALREADY_DESCRIBED,
            ),
        )
        for occurrence in occurrences:
            self.assertEqual(occurrence.descendant_person_id, "I4")
            self.assertEqual(occurrence.spouse_person_id, "I5")
        self.assertNotEqual(
            occurrences[0].descendant_row_index,
            occurrences[1].descendant_row_index,
        )
        self.assertEqual(marriage_result.estimate.representative_value, marriage_date)

        layout = LayoutEngine().build(model)

        marriages = tuple(
            placement
            for placement in layout.marriage_node_placements
            if placement.family_id == "F4"
        )
        self.assertEqual(len(marriages), 2)
        self.assertEqual(len(layout.marriage_node_placements), 2)
        for placement, occurrence in zip(marriages, occurrences):
            self.assertEqual(
                placement.descendant_row_index, occurrence.descendant_row_index
            )
            self.assertEqual(placement.spouse_row_index, occurrence.spouse_row_index)
            self.assertEqual(placement.x, float(marriage_date.toordinal()))
        self.assertEqual(layout.remarriage_segment_placements, ())

    def test_birth_hard_soft_conflict_creates_diagnostic_at_bar_start(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintConflictType,
            ConstraintResolution,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        birth_date = date(1840, 1, 1)
        birth_value = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=birth_date,
            normalized_maximum=birth_date,
            representative_value=birth_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            parent_family_ids=(),
            family_ids=(),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=birth_value,
        )
        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={"E1": birth},
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I1",
            event_id="E1",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_value,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I1",
        )
        hard_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=birth_date,
            rule_id="test_hard_birth_minimum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        soft_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            bound=date(1839, 1, 1),
            rule_id="test_soft_birth_maximum",
            strength=ConstraintStrength.SOFT,
            evidences=(evidence,),
        )
        hard_minimum = ResolvedBound(
            target=target,
            value=birth_date,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=(hard_constraint, soft_constraint),
        )
        domain = TemporalReconciler().reconcile(target, birth_value, resolution)
        birth_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=target,
                gramps_value=birth_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint, soft_constraint),
        )
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results={target: birth_result},
        )

        layout = LayoutEngine().build(model)

        person_placement = layout.person_placements[0]
        self.assertEqual(person_placement.x_start, float(birth_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, person_placement.x_start)
        self.assertEqual(diagnostic.y, person_placement.y)

    def test_birth_gramps_inference_conflict_creates_diagnostic(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciliationConflictType,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        birth_date = date(1840, 1, 1)
        birth_value = TemporalValue(
            source_value="avant le 01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=birth_date,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.UNDETERMINED,
        )
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),),
            parent_family_ids=(),
            family_ids=(),
        )
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=birth_value,
        )
        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events={"E1": birth},
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I1",
            event_id="E1",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=birth_value,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I1",
        )
        hard_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1841, 1, 1),
            rule_id="test_hard_birth_minimum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        hard_minimum = ResolvedBound(
            target=target,
            value=date(1841, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )
        domain = TemporalReconciler().reconcile(target, birth_value, resolution)
        birth_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=target,
                gramps_value=birth_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint,),
        )
        self.assertIsNone(birth_result.constraint_resolution.conflict_type)
        self.assertIs(
            birth_result.reconciled_domain.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertIs(domain.constraint_resolution, resolution)
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results={target: birth_result},
        )

        layout = LayoutEngine().build(model)

        person_placement = layout.person_placements[0]
        self.assertEqual(person_placement.x_start, float(birth_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, person_placement.x_start)
        self.assertEqual(diagnostic.y, person_placement.y)

    def test_birth_multiple_principal_events_creates_diagnostic(self) -> None:
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        unknown_birth = TemporalValue.unknown()
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                PersonEventRef("E2", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
            ),
            parent_family_ids=(),
            family_ids=(),
        )
        events = {
            event_id: Event(
                event_id=event_id,
                source_type="BIRTH",
                semantic=EventSemantic.BIRTH,
                date=unknown_birth,
            )
            for event_id in ("E1", "E2")
        }
        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events=events,
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == target
        )
        self.assertEqual(len(birth_result.target_entry.anomalies), 1)
        anomaly = birth_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E1", "E2"))
        self.assertIsNone(birth_result.constraint_resolution.conflict_type)
        self.assertIsNone(birth_result.reconciled_domain.conflict_type)
        self.assertIsNone(birth_result.estimate.representative_value)
        self.assertIsNone(birth_result.reconciled_domain.principal_minimum)
        self.assertIsNone(birth_result.reconciled_domain.principal_maximum)
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results={target: birth_result},
        )

        layout = LayoutEngine().build(model)

        person_placement = layout.person_placements[0]
        self.assertIsNotNone(person_placement.x_start)
        self.assertEqual(person_placement.x_start, LayoutEngine.LOGICAL_X_ORIGIN)
        self.assertIs(person_placement.x_start_kind, PositionKind.VISUAL_FALLBACK)
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, person_placement.x_start)
        self.assertEqual(diagnostic.y, person_placement.y)

    def test_death_conflict_creates_diagnostic_at_bar_end(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintConflictType,
            ConstraintResolution,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.life_bar_kind import LifeBarKind
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        birth_date = date(1840, 1, 1)
        death_date = date(1900, 1, 1)
        events = {}
        for event_id, semantic, event_date in (
            ("E1", EventSemantic.BIRTH, birth_date),
            ("E2", EventSemantic.DEATH, death_date),
        ):
            events[event_id] = Event(
                event_id=event_id,
                source_type=semantic.value,
                semantic=semantic,
                date=TemporalValue(
                    source_value=event_date.isoformat(),
                    source_calendar="GREGORIAN",
                    normalized_minimum=event_date,
                    normalized_maximum=event_date,
                    representative_value=event_date,
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
                PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                PersonEventRef("E2", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
            ),
            parent_family_ids=(),
            family_ids=(),
        )
        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events=events,
            root_person_id="I1",
        )
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        death_value = events["E2"].date
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I1",
            event_id="E2",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=death_value,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I1",
        )
        hard_constraint = TemporalConstraint(
            target=death_target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=death_date,
            rule_id="test_hard_death_minimum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        soft_constraint = TemporalConstraint(
            target=death_target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            bound=date(1899, 1, 1),
            rule_id="test_soft_death_maximum",
            strength=ConstraintStrength.SOFT,
            evidences=(evidence,),
        )
        hard_minimum = ResolvedBound(
            target=death_target,
            value=death_date,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=death_target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=(hard_constraint, soft_constraint),
        )
        domain = TemporalReconciler().reconcile(death_target, death_value, resolution)
        death_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=death_target,
                gramps_value=death_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint, soft_constraint),
        )
        self.assertIs(
            death_result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertIs(domain.constraint_resolution, resolution)
        self.assertIsNone(death_result.reconciled_domain.conflict_type)
        self.assertEqual(death_result.target_entry.anomalies, ())
        self.assertIsNone(birth_result.constraint_resolution.conflict_type)
        self.assertIsNone(birth_result.reconciled_domain.conflict_type)
        self.assertEqual(birth_result.target_entry.anomalies, ())
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results={birth_target: birth_result, death_target: death_result},
        )

        layout = LayoutEngine().build(model)

        person_placement = layout.person_placements[0]
        self.assertIs(person_placement.life_bar_kind, LifeBarKind.NORMAL)
        self.assertEqual(person_placement.x_start, float(birth_date.toordinal()))
        self.assertIsNotNone(person_placement.bar_x_end)
        self.assertEqual(person_placement.bar_x_end, float(death_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, death_target)
        self.assertEqual(diagnostic.x, person_placement.bar_x_end)
        self.assertEqual(diagnostic.y, person_placement.y)

    def test_death_gramps_inference_conflict_creates_diagnostic(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciliationConflictType,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.life_bar_kind import LifeBarKind
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        birth_date = date(1840, 1, 1)
        death_date = date(1900, 1, 1)
        events = {}
        for event_id, semantic, event_date in (
            ("E1", EventSemantic.BIRTH, birth_date),
            ("E2", EventSemantic.DEATH, death_date),
        ):
            events[event_id] = Event(
                event_id=event_id,
                source_type=semantic.value,
                semantic=semantic,
                date=TemporalValue(
                    source_value=("après le " if semantic is EventSemantic.DEATH else "") + event_date.isoformat(),
                    source_calendar="GREGORIAN",
                    normalized_minimum=event_date,
                    normalized_maximum=None if semantic is EventSemantic.DEATH else event_date,
                    representative_value=None if semantic is EventSemantic.DEATH else event_date,
                    value_origin=ValueOrigin.GRAMPS,
                    source_quality=SourceQuality.NORMAL,
                    evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                    certainty=CertaintyLevel.UNDETERMINED if semantic is EventSemantic.DEATH else CertaintyLevel.CERTAIN,
                ),
            )
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                PersonEventRef("E2", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
            ),
            parent_family_ids=(),
            family_ids=(),
        )
        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events=events,
            root_person_id="I1",
        )
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )
        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        birth_result = next(
            result
            for result in TemporalInferenceEngine().run(data)
            if result.target_entry.target == birth_target
        )
        death_value = events["E2"].date
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I1",
            event_id="E2",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=death_value,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I1",
        )
        hard_constraint = TemporalConstraint(
            target=death_target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            bound=date(1899, 1, 1),
            rule_id="test_hard_death_maximum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        hard_maximum = ResolvedBound(
            target=death_target,
            value=date(1899, 1, 1),
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=death_target,
            hard_minimum=None,
            hard_maximum=hard_maximum,
            refined_minimum=None,
            refined_maximum=hard_maximum,
            conflict_type=None,
            conflicting_constraints=(),
        )
        domain = TemporalReconciler().reconcile(death_target, death_value, resolution)
        death_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=death_target,
                gramps_value=death_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint,),
        )
        self.assertIsNone(death_result.constraint_resolution.conflict_type)
        self.assertIs(domain.constraint_resolution, resolution)
        self.assertIs(
            death_result.reconciled_domain.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertEqual(death_result.target_entry.anomalies, ())
        self.assertIsNone(birth_result.constraint_resolution.conflict_type)
        self.assertIsNone(birth_result.reconciled_domain.conflict_type)
        self.assertEqual(birth_result.target_entry.anomalies, ())
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results={birth_target: birth_result, death_target: death_result},
        )

        layout = LayoutEngine().build(model)

        person_placement = layout.person_placements[0]
        self.assertIs(person_placement.life_bar_kind, LifeBarKind.NORMAL)
        self.assertEqual(person_placement.x_start, float(birth_date.toordinal()))
        self.assertIsNotNone(person_placement.bar_x_end)
        self.assertEqual(person_placement.bar_x_end, float(death_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, death_target)
        self.assertEqual(diagnostic.x, person_placement.bar_x_end)
        self.assertEqual(diagnostic.y, person_placement.y)

    def test_death_multiple_principal_events_creates_diagnostic(self) -> None:
        from descendants_timeline.inference.rule_engine import RuleEngine
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        birth_date = date(1840, 1, 1)
        birth_value = TemporalValue(
            source_value="01/01/1840",
            source_calendar="GREGORIAN",
            normalized_minimum=birth_date,
            normalized_maximum=birth_date,
            representative_value=birth_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )
        root = Person(
            person_id="I1",
            display_name="Root",
            gender=PersonGender.UNKNOWN,
            event_refs=(
                PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                PersonEventRef("E2", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                PersonEventRef("E3", EventRoleSemantic.PRINCIPAL, "PRIMARY"),
            ),
            parent_family_ids=(),
            family_ids=(),
        )
        events = {
            "E1": Event(
                event_id="E1",
                source_type="BIRTH",
                semantic=EventSemantic.BIRTH,
                date=birth_value,
            ),
        }
        for event_id in ("E2", "E3"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="DEATH",
                semantic=EventSemantic.DEATH,
                date=TemporalValue.unknown(),
            )
        data = RawGenealogyData(
            persons={"I1": root},
            families={},
            events=events,
            root_person_id="I1",
        )
        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.DEATH,
        )
        # Aucune règle ne fournit de date inférée : on isole le fallback du layout.
        results = TemporalInferenceEngine(rule_engine=RuleEngine(rules=())).run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        death_result = results_by_target[death_target]
        self.assertEqual(len(death_result.target_entry.anomalies), 1)
        anomaly = death_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E2", "E3"))
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not death_result:
                self.assertEqual(result.target_entry.anomalies, ())
        self.assertIs(
            death_result.reconciled_domain.constraint_resolution,
            death_result.constraint_resolution,
        )
        self.assertIsNone(death_result.estimate.representative_value)
        self.assertIsNone(death_result.reconciled_domain.principal_minimum)
        self.assertIsNone(death_result.reconciled_domain.principal_maximum)
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        person_placement = layout.person_placements[0]
        self.assertEqual(person_placement.x_start, float(birth_date.toordinal()))
        self.assertIsNotNone(person_placement.bar_x_end)
        self.assertEqual(
            person_placement.bar_x_end,
            person_placement.x_start + LayoutEngine.LIFE_SPAN_OFFSET,
        )
        self.assertIs(person_placement.x_end_kind, PositionKind.VISUAL_FALLBACK)
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, death_target)
        self.assertEqual(diagnostic.x, person_placement.bar_x_end)
        self.assertEqual(diagnostic.y, person_placement.y)

    def test_marriage_conflict_creates_diagnostic_at_marriage_node(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintConflictType,
            ConstraintResolution,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        marriage_date = date(1870, 1, 1)
        marriage_value = TemporalValue(
            source_value="01/01/1870",
            source_calendar="GREGORIAN",
            normalized_minimum=marriage_date,
            normalized_maximum=marriage_date,
            representative_value=marriage_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for person_id in ("I1", "I2")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(FamilyEventRef("E1", FamilyRoleSemantic.FAMILY, "FAMILY"),),
            child_refs=(),
        )
        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_value,
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": marriage},
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F1",
            event_id="E1",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=marriage_value,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F1",
        )
        hard_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=marriage_date,
            rule_id="test_hard_marriage_minimum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        soft_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            bound=date(1869, 1, 1),
            rule_id="test_soft_marriage_maximum",
            strength=ConstraintStrength.SOFT,
            evidences=(evidence,),
        )
        hard_minimum = ResolvedBound(
            target=target,
            value=marriage_date,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=(hard_constraint, soft_constraint),
        )
        domain = TemporalReconciler().reconcile(target, marriage_value, resolution)
        marriage_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=target,
                gramps_value=marriage_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint, soft_constraint),
        )
        results_by_target = {
            result.target_entry.target: result
            for result in TemporalInferenceEngine().run(data)
        }
        results_by_target[target] = marriage_result
        self.assertIs(
            marriage_result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertIs(domain.constraint_resolution, resolution)
        self.assertIsNone(marriage_result.reconciled_domain.conflict_type)
        self.assertEqual(marriage_result.target_entry.anomalies, ())
        self.assertEqual(determine_display_value(marriage_result), marriage_date)
        for result_target, result in results_by_target.items():
            if result_target != target:
                self.assertIsNone(result.constraint_resolution.conflict_type)
                self.assertIsNone(result.reconciled_domain.conflict_type)
                self.assertEqual(result.target_entry.anomalies, ())
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.marriage_node_placements), 1)
        marriage_node = layout.marriage_node_placements[0]
        self.assertEqual(marriage_node.family_id, "F1")
        self.assertEqual(marriage_node.x, float(marriage_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, marriage_node.x)
        self.assertEqual(diagnostic.y, marriage_node.y)

    def test_divorce_conflict_creates_diagnostic_at_divorce_node(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintConflictType,
            ConstraintResolution,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.divorce_node_placement import (
            DivorceNodePlacement,
        )
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        divorce_date = date(1870, 1, 1)
        divorce_value = TemporalValue(
            source_value="01/01/1870",
            source_calendar="GREGORIAN",
            normalized_minimum=divorce_date,
            normalized_maximum=divorce_date,
            representative_value=divorce_date,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for person_id in ("I1", "I2")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(FamilyEventRef("E1", FamilyRoleSemantic.FAMILY, "FAMILY"),),
            child_refs=(),
        )
        divorce = Event(
            event_id="E1",
            source_type="DIVORCE",
            semantic=EventSemantic.DIVORCE,
            date=divorce_value,
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": divorce},
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.DIVORCE,
        )
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F1",
            event_id="E1",
            semantic=EventSemantic.DIVORCE,
            role=FamilyRoleSemantic.FAMILY,
            date=divorce_value,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F1",
        )
        hard_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=divorce_date,
            rule_id="test_hard_divorce_minimum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        soft_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.BEFORE_OR_EQUAL,
            bound=date(1869, 1, 1),
            rule_id="test_soft_divorce_maximum",
            strength=ConstraintStrength.SOFT,
            evidences=(evidence,),
        )
        hard_minimum = ResolvedBound(
            target=target,
            value=divorce_date,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=ConstraintConflictType.HARD_SOFT,
            conflicting_constraints=(hard_constraint, soft_constraint),
        )
        domain = TemporalReconciler().reconcile(target, divorce_value, resolution)
        divorce_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=target,
                gramps_value=divorce_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint, soft_constraint),
        )
        results_by_target = {
            result.target_entry.target: result
            for result in TemporalInferenceEngine().run(data)
        }
        results_by_target[target] = divorce_result
        self.assertIs(
            divorce_result.constraint_resolution.conflict_type,
            ConstraintConflictType.HARD_SOFT,
        )
        self.assertIs(domain.constraint_resolution, resolution)
        self.assertIsNone(divorce_result.reconciled_domain.conflict_type)
        self.assertEqual(divorce_result.target_entry.anomalies, ())
        self.assertEqual(divorce_result.estimate.representative_value, divorce_date)
        self.assertEqual(determine_display_value(divorce_result), divorce_date)
        for result_target, result in results_by_target.items():
            if result_target != target:
                self.assertIsNone(result.constraint_resolution.conflict_type)
                self.assertIsNone(result.reconciled_domain.conflict_type)
                self.assertEqual(result.target_entry.anomalies, ())
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.divorce_node_placements), 1)
        divorce_node = layout.divorce_node_placements[0]
        self.assertIsInstance(divorce_node, DivorceNodePlacement)
        self.assertEqual(divorce_node.family_id, "F1")
        self.assertEqual(divorce_node.x, float(divorce_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, divorce_node.x)
        self.assertEqual(diagnostic.y, divorce_node.y)

    def test_marriage_gramps_inference_conflict_creates_diagnostic(self) -> None:
        from descendants_timeline.inference.constraint_resolution import (
            ConstraintResolution,
        )
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciliationConflictType,
        )
        from descendants_timeline.inference.resolved_bound import ResolvedBound
        from descendants_timeline.inference.temporal_estimator import TemporalEstimator
        from descendants_timeline.inference.temporal_inference_result import (
            TemporalInferenceResult,
        )
        from descendants_timeline.inference.temporal_reconciler import TemporalReconciler
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_constraint import (
            ConstraintOperator,
            ConstraintStrength,
            TemporalConstraint,
        )
        from descendants_timeline.model.temporal_evidence import (
            EvidenceOwnerType,
            TemporalEvidence,
        )
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry

        marriage_date = date(1870, 1, 1)
        marriage_value = TemporalValue(
            source_value="avant le 01/01/1870",
            source_calendar="GREGORIAN",
            normalized_minimum=None,
            normalized_maximum=marriage_date,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.UNDETERMINED,
        )
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for person_id in ("I1", "I2")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(FamilyEventRef("E1", FamilyRoleSemantic.FAMILY, "FAMILY"),),
            child_refs=(),
        )
        marriage = Event(
            event_id="E1",
            source_type="MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            date=marriage_value,
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events={"E1": marriage},
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F1",
            event_id="E1",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=marriage_value,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F1",
        )
        hard_constraint = TemporalConstraint(
            target=target,
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            bound=date(1871, 1, 1),
            rule_id="test_hard_marriage_minimum",
            strength=ConstraintStrength.HARD,
            evidences=(evidence,),
        )
        hard_minimum = ResolvedBound(
            target=target,
            value=date(1871, 1, 1),
            operator=ConstraintOperator.AFTER_OR_EQUAL,
            strength=ConstraintStrength.HARD,
            constraints=(hard_constraint,),
        )
        resolution = ConstraintResolution(
            target=target,
            hard_minimum=hard_minimum,
            hard_maximum=None,
            refined_minimum=hard_minimum,
            refined_maximum=None,
            conflict_type=None,
            conflicting_constraints=(),
        )
        domain = TemporalReconciler().reconcile(target, marriage_value, resolution)
        marriage_result = TemporalInferenceResult(
            target_entry=TemporalTargetEntry(
                target=target,
                gramps_value=marriage_value,
                anomalies=(),
            ),
            constraint_resolution=resolution,
            reconciled_domain=domain,
            estimate=TemporalEstimator().estimate(domain),
            constraints=(hard_constraint,),
        )
        results_by_target = {
            result.target_entry.target: result
            for result in TemporalInferenceEngine().run(data)
        }
        results_by_target[target] = marriage_result
        self.assertIsNone(marriage_result.constraint_resolution.conflict_type)
        self.assertIs(domain.constraint_resolution, resolution)
        self.assertIs(
            marriage_result.reconciled_domain.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )
        self.assertEqual(marriage_result.target_entry.anomalies, ())
        self.assertEqual(determine_display_value(marriage_result), marriage_date)
        for result_target, result in results_by_target.items():
            if result_target != target:
                self.assertIsNone(result.constraint_resolution.conflict_type)
                self.assertIsNone(result.reconciled_domain.conflict_type)
                self.assertEqual(result.target_entry.anomalies, ())
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.marriage_node_placements), 1)
        marriage_node = layout.marriage_node_placements[0]
        self.assertEqual(marriage_node.family_id, "F1")
        self.assertEqual(marriage_node.x, float(marriage_date.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, marriage_node.x)
        self.assertEqual(diagnostic.y, marriage_node.y)

    def test_marriage_multiple_principal_events_creates_diagnostic(self) -> None:
        from descendants_timeline.inference.reconciled_temporal_domain import (
            ReconciledBoundOrigin,
        )
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        birth_date = date(1840, 1, 1)
        birth = Event(
            event_id="E1",
            source_type="BIRTH",
            semantic=EventSemantic.BIRTH,
            date=TemporalValue(
                source_value="01/01/1840",
                source_calendar="GREGORIAN",
                normalized_minimum=birth_date,
                normalized_maximum=birth_date,
                representative_value=birth_date,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=SourceQuality.NORMAL,
                evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                certainty=CertaintyLevel.CERTAIN,
            ),
        )
        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    (PersonEventRef("E1", EventRoleSemantic.PRINCIPAL, "PRIMARY"),)
                    if person_id == "I1" else ()
                ),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for person_id in ("I1", "I2")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef("E2", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E3", FamilyRoleSemantic.FAMILY, "FAMILY"),
            ),
            child_refs=(),
        )
        events = {"E1": birth}
        for event_id in ("E2", "E3"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue.unknown(),
            )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        results = TemporalInferenceEngine().run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        marriage_result = results_by_target[target]
        self.assertEqual(len(marriage_result.target_entry.anomalies), 1)
        anomaly = marriage_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E2", "E3"))
        self.assertIs(
            marriage_result.target_entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not marriage_result:
                self.assertEqual(result.target_entry.anomalies, ())
        self.assertIs(
            marriage_result.reconciled_domain.constraint_resolution,
            marriage_result.constraint_resolution,
        )
        minimum = marriage_result.reconciled_domain.principal_minimum
        self.assertIsNotNone(minimum)
        self.assertIs(minimum.origin, ReconciledBoundOrigin.INFERENCE)
        display_value = determine_display_value(marriage_result)
        self.assertIsNotNone(display_value)
        model = TimelineModel(
            data=data,
            traversal=DescendanceTraversal().traverse(data, "I1"),
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(len(layout.marriage_node_placements), 1)
        marriage_node = layout.marriage_node_placements[0]
        self.assertEqual(marriage_node.family_id, "F1")
        self.assertEqual(marriage_node.x, float(display_value.toordinal()))
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, marriage_node.x)
        self.assertEqual(diagnostic.y, marriage_node.y)

    def test_marriage_anomaly_without_node_uses_shared_life_bar_interval(self) -> None:
        from descendants_timeline.inference.rule_engine import RuleEngine
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        events = {}
        persons = {}
        for person_id, birth_id, death_id, birth_date, death_date in (
            ("I1", "E1", "E2", date(1840, 1, 1), date(1900, 1, 1)),
            ("I2", "E3", "E4", date(1850, 1, 1), date(1910, 1, 1)),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(birth_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                    PersonEventRef(death_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                ),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for event_id, semantic, event_date in (
                (birth_id, EventSemantic.BIRTH, birth_date),
                (death_id, EventSemantic.DEATH, death_date),
            ):
                events[event_id] = Event(
                    event_id=event_id,
                    source_type=semantic.value,
                    semantic=semantic,
                    date=TemporalValue(
                        source_value=event_date.isoformat(),
                        source_calendar="GREGORIAN",
                        normalized_minimum=event_date,
                        normalized_maximum=event_date,
                        representative_value=event_date,
                        value_origin=ValueOrigin.GRAMPS,
                        source_quality=SourceQuality.NORMAL,
                        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                        certainty=CertaintyLevel.CERTAIN,
                    ),
                )
        for event_id in ("E5", "E6"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue.unknown(),
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef("E5", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E6", FamilyRoleSemantic.FAMILY, "FAMILY"),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        # Isoler le placement graphique sans inférer de borne de mariage.
        results = TemporalInferenceEngine(rule_engine=RuleEngine(rules=())).run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        marriage_result = results_by_target[target]
        self.assertEqual(len(marriage_result.target_entry.anomalies), 1)
        anomaly = marriage_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E5", "E6"))
        self.assertIs(
            marriage_result.target_entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )
        self.assertIsNone(marriage_result.estimate.representative_value)
        self.assertIsNone(determine_display_value(marriage_result))
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not marriage_result:
                self.assertEqual(result.target_entry.anomalies, ())
        traversal = DescendanceTraversal().traverse(data, "I1")
        self.assertEqual(persons["I1"].family_ids, ("F1",))
        self.assertEqual(len(traversal.family_occurrences), 1)
        occurrence = traversal.family_occurrences[0]
        self.assertEqual(occurrence.family_id, "F1")
        self.assertEqual(occurrence.descendant_person_id, "I1")
        self.assertEqual(occurrence.spouse_person_id, "I2")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())
        descendant = layout.person_placements[occurrence.descendant_row_index]
        spouse = layout.person_placements[occurrence.spouse_row_index]
        for placement in (descendant, spouse):
            self.assertIsNotNone(placement.bar_x_start)
            self.assertIsNotNone(placement.bar_x_end)
        shared_start = max(descendant.bar_x_start, spouse.bar_x_start)
        shared_end = min(descendant.bar_x_end, spouse.bar_x_end)
        self.assertLess(shared_start, shared_end)
        expected_x = (shared_start + shared_end) / 2
        expected_y = (descendant.y + spouse.y) / 2
        self.assertEqual(len(layout.diagnostic_placements), 1)
        diagnostic = layout.diagnostic_placements[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, expected_x)
        self.assertEqual(diagnostic.y, expected_y)
        self.assertIsNone(determine_display_value(marriage_result))
        self.assertIsNone(marriage_result.estimate.representative_value)

    def test_marriage_and_divorce_anomalies_without_nodes_have_offset_diagnostics(self) -> None:
        from descendants_timeline.inference.rule_engine import RuleEngine
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        events = {}
        persons = {}
        for person_id, birth_id, death_id, birth_date, death_date in (
            ("I1", "E1", "E2", date(1840, 1, 1), date(1900, 1, 1)),
            ("I2", "E3", "E4", date(1850, 1, 1), date(1910, 1, 1)),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(birth_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                    PersonEventRef(death_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                ),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for event_id, semantic, event_date in (
                (birth_id, EventSemantic.BIRTH, birth_date),
                (death_id, EventSemantic.DEATH, death_date),
            ):
                events[event_id] = Event(
                    event_id=event_id,
                    source_type=semantic.value,
                    semantic=semantic,
                    date=TemporalValue(
                        source_value=event_date.isoformat(),
                        source_calendar="GREGORIAN",
                        normalized_minimum=event_date,
                        normalized_maximum=event_date,
                        representative_value=event_date,
                        value_origin=ValueOrigin.GRAMPS,
                        source_quality=SourceQuality.NORMAL,
                        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                        certainty=CertaintyLevel.CERTAIN,
                    ),
                )
        for event_id in ("E5", "E6"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue.unknown(),
            )
        for event_id in ("E7", "E8"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="DIVORCE",
                semantic=EventSemantic.DIVORCE,
                date=TemporalValue.unknown(),
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef("E5", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E6", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E7", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E8", FamilyRoleSemantic.FAMILY, "FAMILY"),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        # Isoler le placement graphique sans inférer de borne de mariage.
        results = TemporalInferenceEngine(rule_engine=RuleEngine(rules=())).run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        marriage_result = results_by_target[target]
        self.assertEqual(len(marriage_result.target_entry.anomalies), 1)
        anomaly = marriage_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E5", "E6"))
        self.assertIs(
            marriage_result.target_entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )
        self.assertIsNone(marriage_result.estimate.representative_value)
        self.assertIsNone(determine_display_value(marriage_result))
        divorce_target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.DIVORCE,
        )
        divorce_result = results_by_target[divorce_target]
        self.assertEqual(len(divorce_result.target_entry.anomalies), 1)
        self.assertIs(
            divorce_result.target_entry.anomalies[0].anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(divorce_result.target_entry.anomalies[0].event_ids, ("E7", "E8"))
        for result in (marriage_result, divorce_result):
            self.assertIsNone(result.estimate.representative_value)
            self.assertIsNone(result.reconciled_domain.principal_minimum)
            self.assertIsNone(result.reconciled_domain.principal_maximum)
            self.assertIsNone(determine_display_value(result))
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not marriage_result and result is not divorce_result:
                self.assertEqual(result.target_entry.anomalies, ())
        traversal = DescendanceTraversal().traverse(data, "I1")
        self.assertEqual(persons["I1"].family_ids, ("F1",))
        self.assertEqual(len(traversal.family_occurrences), 1)
        occurrence = traversal.family_occurrences[0]
        self.assertEqual(occurrence.family_id, "F1")
        self.assertEqual(occurrence.descendant_person_id, "I1")
        self.assertEqual(occurrence.spouse_person_id, "I2")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())
        self.assertEqual(layout.divorce_node_placements, ())
        descendant = layout.person_placements[occurrence.descendant_row_index]
        spouse = layout.person_placements[occurrence.spouse_row_index]
        for placement in (descendant, spouse):
            self.assertIsNotNone(placement.bar_x_start)
            self.assertIsNotNone(placement.bar_x_end)
        shared_start = max(descendant.bar_x_start, spouse.bar_x_start)
        shared_end = min(descendant.bar_x_end, spouse.bar_x_end)
        self.assertLess(shared_start, shared_end)
        expected_x = (shared_start + shared_end) / 2
        expected_y = (descendant.y + spouse.y) / 2
        marriage_diagnostics = tuple(
            diagnostic for diagnostic in layout.diagnostic_placements
            if diagnostic.target == target
        )
        self.assertEqual(len(marriage_diagnostics), 1)
        marriage_diagnostic = marriage_diagnostics[0]
        self.assertIsInstance(marriage_diagnostic, DiagnosticPlacement)
        self.assertEqual(marriage_diagnostic.x, expected_x)
        self.assertEqual(marriage_diagnostic.y, expected_y)
        divorce_diagnostics = tuple(
            diagnostic for diagnostic in layout.diagnostic_placements
            if diagnostic.target == divorce_target
        )
        self.assertEqual(len(divorce_diagnostics), 1)
        self.assertEqual(len(layout.diagnostic_placements), 2)
        divorce_diagnostic = divorce_diagnostics[0]
        self.assertIsInstance(divorce_diagnostic, DiagnosticPlacement)
        self.assertEqual(divorce_diagnostic.y, marriage_diagnostic.y)
        self.assertGreater(divorce_diagnostic.x, marriage_diagnostic.x)
        self.assertEqual(
            divorce_diagnostic.x - marriage_diagnostic.x,
            LayoutEngine.DIVORCE_DIAGNOSTIC_OFFSET,
        )

    def test_remarriage_anomaly_without_node_uses_descendant_bar_bottom(self) -> None:
        from descendants_timeline.inference.rule_engine import RuleEngine
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        events = {}
        persons = {}
        for person_id, birth_id, death_id, birth_date, death_date in (
            ("P1", "E1", "E2", date(1840, 1, 1), date(1900, 1, 1)),
            ("P3", "E3", "E4", date(1850, 1, 1), date(1910, 1, 1)),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(birth_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                    PersonEventRef(death_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                ),
                parent_family_ids=(),
                family_ids=("F1", "F2") if person_id == "P1" else ("F2",),
            )
            for event_id, semantic, event_date in (
                (birth_id, EventSemantic.BIRTH, birth_date),
                (death_id, EventSemantic.DEATH, death_date),
            ):
                events[event_id] = Event(
                    event_id=event_id,
                    source_type=semantic.value,
                    semantic=semantic,
                    date=TemporalValue(
                        source_value=event_date.isoformat(),
                        source_calendar="GREGORIAN",
                        normalized_minimum=event_date,
                        normalized_maximum=event_date,
                        representative_value=event_date,
                        value_origin=ValueOrigin.GRAMPS,
                        source_quality=SourceQuality.NORMAL,
                        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                        certainty=CertaintyLevel.CERTAIN,
                    ),
                )
        for event_id in ("E5", "E6"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue.unknown(),
            )
        persons["P2"] = Person(
            person_id="P2",
            display_name="First spouse",
            gender=PersonGender.UNKNOWN,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F1",),
        )
        first_family = Family(
            family_id="F1",
            parent1_id="P1",
            parent2_id="P2",
            event_refs=(),
            child_refs=(),
        )
        family = Family(
            family_id="F2",
            parent1_id="P1",
            parent2_id="P3",
            event_refs=(
                FamilyEventRef("E5", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E6", FamilyRoleSemantic.FAMILY, "FAMILY"),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": first_family, "F2": family},
            events=events,
            root_person_id="P1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F2",
            semantic=TargetSemantic.MARRIAGE,
        )
        # Isoler le placement graphique sans inférer de borne de mariage.
        results = TemporalInferenceEngine(rule_engine=RuleEngine(rules=())).run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        marriage_result = results_by_target[target]
        self.assertEqual(len(marriage_result.target_entry.anomalies), 1)
        anomaly = marriage_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E5", "E6"))
        self.assertIs(
            marriage_result.target_entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )
        self.assertIsNone(marriage_result.estimate.representative_value)
        self.assertIsNone(determine_display_value(marriage_result))
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not marriage_result:
                self.assertEqual(result.target_entry.anomalies, ())
        traversal = DescendanceTraversal().traverse(data, "P1")
        self.assertEqual(persons["P1"].family_ids, ("F1", "F2"))
        self.assertEqual(
            tuple(item.family_id for item in traversal.family_occurrences),
            ("F1", "F2"),
        )
        occurrence = traversal.family_occurrences[1]
        self.assertEqual(occurrence.family_id, "F2")
        self.assertEqual(occurrence.descendant_person_id, "P1")
        self.assertEqual(occurrence.spouse_person_id, "P3")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())
        descendant = layout.person_placements[occurrence.descendant_row_index]
        spouse = layout.person_placements[occurrence.spouse_row_index]
        for placement in (descendant, spouse):
            self.assertIsNotNone(placement.bar_x_start)
            self.assertIsNotNone(placement.bar_x_end)
        shared_start = max(descendant.bar_x_start, spouse.bar_x_start)
        shared_end = min(descendant.bar_x_end, spouse.bar_x_end)
        self.assertLess(shared_start, shared_end)
        expected_x = (shared_start + shared_end) / 2
        expected_y = descendant.y
        diagnostics = tuple(
            diagnostic for diagnostic in layout.diagnostic_placements
            if diagnostic.target == target
        )
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, expected_x)
        self.assertEqual(diagnostic.y, expected_y)
        self.assertIsNone(determine_display_value(marriage_result))
        self.assertIsNone(marriage_result.estimate.representative_value)

    def test_marriage_anomaly_without_node_disjoint_bars_uses_descendant_midpoint(self) -> None:
        from descendants_timeline.inference.rule_engine import RuleEngine
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        events = {}
        persons = {}
        for person_id, birth_id, death_id, birth_date, death_date in (
            ("I1", "E1", "E2", date(1840, 1, 1), date(1900, 1, 1)),
            ("I2", "E3", "E4", date(1910, 1, 1), date(1970, 1, 1)),
        ):
            persons[person_id] = Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(
                    PersonEventRef(birth_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                    PersonEventRef(death_id, EventRoleSemantic.PRINCIPAL, "PRIMARY"),
                ),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for event_id, semantic, event_date in (
                (birth_id, EventSemantic.BIRTH, birth_date),
                (death_id, EventSemantic.DEATH, death_date),
            ):
                events[event_id] = Event(
                    event_id=event_id,
                    source_type=semantic.value,
                    semantic=semantic,
                    date=TemporalValue(
                        source_value=event_date.isoformat(),
                        source_calendar="GREGORIAN",
                        normalized_minimum=event_date,
                        normalized_maximum=event_date,
                        representative_value=event_date,
                        value_origin=ValueOrigin.GRAMPS,
                        source_quality=SourceQuality.NORMAL,
                        evidence_status=EvidenceStatus.EVIDENCE_USABLE,
                        certainty=CertaintyLevel.CERTAIN,
                    ),
                )
        for event_id in ("E5", "E6"):
            events[event_id] = Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue.unknown(),
            )
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef("E5", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E6", FamilyRoleSemantic.FAMILY, "FAMILY"),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        # Isoler le placement graphique sans inférer de borne de mariage.
        results = TemporalInferenceEngine(rule_engine=RuleEngine(rules=())).run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        marriage_result = results_by_target[target]
        self.assertEqual(len(marriage_result.target_entry.anomalies), 1)
        anomaly = marriage_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E5", "E6"))
        self.assertIs(
            marriage_result.target_entry.gramps_value.value_origin,
            ValueOrigin.UNKNOWN,
        )
        self.assertIsNone(marriage_result.estimate.representative_value)
        self.assertIsNone(determine_display_value(marriage_result))
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not marriage_result:
                self.assertEqual(result.target_entry.anomalies, ())
        traversal = DescendanceTraversal().traverse(data, "I1")
        self.assertEqual(persons["I1"].family_ids, ("F1",))
        self.assertEqual(len(traversal.family_occurrences), 1)
        occurrence = traversal.family_occurrences[0]
        self.assertEqual(occurrence.family_id, "F1")
        self.assertEqual(occurrence.descendant_person_id, "I1")
        self.assertEqual(occurrence.spouse_person_id, "I2")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())
        descendant = layout.person_placements[occurrence.descendant_row_index]
        spouse = layout.person_placements[occurrence.spouse_row_index]
        for placement in (descendant, spouse):
            self.assertIsNotNone(placement.bar_x_start)
            self.assertIsNotNone(placement.bar_x_end)
        shared_start = max(descendant.bar_x_start, spouse.bar_x_start)
        shared_end = min(descendant.bar_x_end, spouse.bar_x_end)
        self.assertGreater(shared_start, shared_end)
        expected_x = (descendant.bar_x_start + descendant.bar_x_end) / 2
        expected_y = (descendant.y + spouse.y) / 2
        diagnostics = tuple(
            diagnostic for diagnostic in layout.diagnostic_placements
            if diagnostic.target == target
        )
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, expected_x)
        self.assertEqual(diagnostic.y, expected_y)
        self.assertIsNone(determine_display_value(marriage_result))
        self.assertIsNone(marriage_result.estimate.representative_value)

    def test_marriage_anomaly_without_node_uses_only_available_descendant_bar(self) -> None:
        from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
        from descendants_timeline.layout.position_kind import PositionKind
        from descendants_timeline.layout.temporal_display_value import determine_display_value
        from descendants_timeline.model.temporal_target import (
            TargetSemantic,
            TemporalOwnerType,
            TemporalTarget,
        )
        from descendants_timeline.model.temporal_target_anomaly import (
            TemporalTargetAnomalyType,
        )

        persons = {
            person_id: Person(
                person_id=person_id,
                display_name=person_id,
                gender=PersonGender.UNKNOWN,
                event_refs=(),
                parent_family_ids=(),
                family_ids=("F1",),
            )
            for person_id in ("I1", "I2")
        }
        events = {
            event_id: Event(
                event_id=event_id,
                source_type="MARRIAGE",
                semantic=EventSemantic.MARRIAGE,
                date=TemporalValue.unknown(),
            )
            for event_id in ("E1", "E2")
        }
        family = Family(
            family_id="F1",
            parent1_id="I1",
            parent2_id="I2",
            event_refs=(
                FamilyEventRef("E1", FamilyRoleSemantic.FAMILY, "FAMILY"),
                FamilyEventRef("E2", FamilyRoleSemantic.FAMILY, "FAMILY"),
            ),
            child_refs=(),
        )
        data = RawGenealogyData(
            persons=persons,
            families={"F1": family},
            events=events,
            root_person_id="I1",
        )
        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F1",
            semantic=TargetSemantic.MARRIAGE,
        )
        results = TemporalInferenceEngine().run(data)
        results_by_target = {result.target_entry.target: result for result in results}
        marriage_result = results_by_target[target]
        self.assertEqual(len(marriage_result.target_entry.anomalies), 1)
        anomaly = marriage_result.target_entry.anomalies[0]
        self.assertIs(
            anomaly.anomaly_type,
            TemporalTargetAnomalyType.MULTIPLE_PRINCIPAL_EVENTS,
        )
        self.assertEqual(anomaly.event_ids, ("E1", "E2"))
        self.assertIsNone(determine_display_value(marriage_result))
        for result in results:
            self.assertIsNone(result.constraint_resolution.conflict_type)
            self.assertIsNone(result.reconciled_domain.conflict_type)
            if result is not marriage_result:
                self.assertEqual(result.target_entry.anomalies, ())
                self.assertIsNone(determine_display_value(result))
        traversal = DescendanceTraversal().traverse(data, "I1")
        self.assertEqual(persons["I1"].family_ids, ("F1",))
        self.assertEqual(len(traversal.family_occurrences), 1)
        occurrence = traversal.family_occurrences[0]
        self.assertEqual(occurrence.family_id, "F1")
        self.assertEqual(occurrence.descendant_person_id, "I1")
        self.assertEqual(occurrence.spouse_person_id, "I2")
        model = TimelineModel(
            data=data,
            traversal=traversal,
            temporal_results=results_by_target,
        )

        layout = LayoutEngine().build(model)

        self.assertEqual(layout.marriage_node_placements, ())
        descendant = layout.person_placements[occurrence.descendant_row_index]
        spouse = layout.person_placements[occurrence.spouse_row_index]
        self.assertEqual(descendant.person_id, "I1")
        self.assertIsNotNone(descendant.bar_x_start)
        self.assertIsNotNone(descendant.bar_x_end)
        self.assertEqual(descendant.bar_x_start, LayoutEngine.LOGICAL_X_ORIGIN)
        self.assertEqual(
            descendant.bar_x_end,
            descendant.bar_x_start + LayoutEngine.LIFE_SPAN_OFFSET,
        )
        self.assertIs(descendant.x_start_kind, PositionKind.VISUAL_FALLBACK)
        self.assertIs(descendant.x_end_kind, PositionKind.VISUAL_FALLBACK)
        self.assertEqual(spouse.person_id, "I2")
        self.assertIsNone(spouse.bar_x_start)
        self.assertIsNone(spouse.bar_x_end)
        expected_x = (descendant.bar_x_start + descendant.bar_x_end) / 2
        expected_y = (descendant.y + spouse.y) / 2
        diagnostics = tuple(
            diagnostic for diagnostic in layout.diagnostic_placements
            if diagnostic.target == target
        )
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertIsInstance(diagnostic, DiagnosticPlacement)
        self.assertEqual(diagnostic.target, target)
        self.assertEqual(diagnostic.x, expected_x)
        self.assertEqual(diagnostic.y, expected_y)

if __name__ == "__main__":
    unittest.main()