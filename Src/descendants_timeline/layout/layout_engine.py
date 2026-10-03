"""Moteur de calcul du layout logique de la timeline."""

from __future__ import annotations

from descendants_timeline.layout.marriage_node_placement import (
    MarriageNodePlacement,
)
from descendants_timeline.layout.person_placement import PersonPlacement
from descendants_timeline.layout.timeline_layout import TimelineLayout
from descendants_timeline.timeline.timeline_model import TimelineModel
from descendants_timeline.layout.timeline_scale import TimelineScale
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)

class LayoutEngine:
    """Transforme un TimelineModel en placements logiques."""

    DEFAULT_TOP_MARGIN = 20.0
    DEFAULT_ROW_HEIGHT = 30.0

    def build(self, model: TimelineModel) -> TimelineLayout:
        scale = TimelineScale()

        person_placements = tuple(
            self._build_person_placement(
                model=model,
                scale=scale,
                row=row,
                row_index=row_index,
            )
            for row_index, row in enumerate(model.traversal.rows)
        )

        marriage_node_placements = []
        for occurrence in model.traversal.family_occurrences:
            if (
                occurrence.spouse_person_id is None
                or occurrence.spouse_row_index is None
            ):
                continue

            marriage_target = TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id=occurrence.family_id,
                semantic=TargetSemantic.MARRIAGE,
            )
            marriage_result = model.temporal_results.get(marriage_target)
            if (
                marriage_result is None
                or marriage_result.estimate.representative_value is None
            ):
                continue

            descendant_y = person_placements[occurrence.descendant_row_index].y
            spouse_y = person_placements[occurrence.spouse_row_index].y
            marriage_node_placements.append(
                MarriageNodePlacement(
                    family_id=occurrence.family_id,
                    descendant_person_id=occurrence.descendant_person_id,
                    spouse_person_id=occurrence.spouse_person_id,
                    descendant_row_index=occurrence.descendant_row_index,
                    spouse_row_index=occurrence.spouse_row_index,
                    x=scale.date_to_x(
                        marriage_result.estimate.representative_value
                    ),
                    y=(descendant_y + spouse_y) / 2.0,
                )
            )

        return TimelineLayout(
            person_placements=person_placements,
            marriage_node_placements=tuple(marriage_node_placements),
            remarriage_segment_placements=(),
        )

    def _build_person_placement(
        self,
        model: TimelineModel,
        scale: TimelineScale,
        row,
        row_index: int,
    ) -> PersonPlacement:
        birth_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id=row.person_id,
            semantic=TargetSemantic.BIRTH,
        )
        death_target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id=row.person_id,
            semantic=TargetSemantic.DEATH,
        )

        birth_result = model.temporal_results.get(birth_target)
        death_result = model.temporal_results.get(death_target)

        x_start = None

        if (
            birth_result is not None
            and birth_result.estimate.representative_value is not None
        ):
            x_start = scale.date_to_x(
                birth_result.estimate.representative_value
            )
        x_end = None

        if (
            death_result is not None
            and death_result.estimate.representative_value is not None
        ):
            x_end = scale.date_to_x(
                death_result.estimate.representative_value
            )

        return PersonPlacement(
            person_id=row.person_id,
            row_index=row_index,
            generation=row.generation,
            role=row.role,
            family_id=row.family_id,
            spouse_of_person_id=row.spouse_of_person_id,
            x_start=x_start,
            x_end=x_end,
            y=(
                self.DEFAULT_TOP_MARGIN
                + row_index * self.DEFAULT_ROW_HEIGHT
            ),
        )
