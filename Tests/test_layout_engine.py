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

if __name__ == "__main__":
    unittest.main()