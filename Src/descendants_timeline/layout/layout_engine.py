"""Moteur de calcul du layout logique de la timeline."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from descendants_timeline.layout.marriage_node_placement import (
    MarriageNodePlacement,
)
from descendants_timeline.layout.remarriage_segment_placement import (
    RemarriageSegmentPlacement,
)
from descendants_timeline.layout.person_placement import PersonPlacement
from descendants_timeline.layout.position_kind import PositionKind
from descendants_timeline.layout.life_bar_kind import LifeBarKind
from descendants_timeline.layout.timeline_layout import TimelineLayout
from descendants_timeline.timeline.timeline_model import TimelineModel
from descendants_timeline.layout.timeline_scale import TimelineScale
from descendants_timeline.layout.temporal_display_value import (
    determine_display_value,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)

from descendants_timeline.traversal.descendance_traversal import (
    FamilyTraversalState,
    TraversalRole,
)

class LayoutEngine:
    """Transforme un TimelineModel en placements logiques."""

    DEFAULT_TOP_MARGIN = 20.0
    DEFAULT_ROW_HEIGHT = 30.0
    # Distance géométrique sur l'axe X, sans signification temporelle.
    LIFE_SPAN_OFFSET = 3650.0
    # Distance géométrique sur l'axe X, sans signification temporelle.
    VISUAL_OFFSET = 365.0
    # Origine géométrique sur l'axe X, sans signification temporelle.
    LOGICAL_X_ORIGIN = 0.0

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

        # Les sources restent les placements propres de la première passe.
        own_person_placements = person_placements
        resolved_person_placements = list(person_placements)
        for occurrence in model.traversal.family_occurrences:
            if (
                occurrence.spouse_person_id is None
                or occurrence.spouse_row_index is None
            ):
                continue

            descendant_index = occurrence.descendant_row_index
            spouse_index = occurrence.spouse_row_index
            spouse = resolved_person_placements[spouse_index]
            descendant_x_start = own_person_placements[descendant_index].x_start
            if spouse.x_start is None and descendant_x_start is not None:
                resolved_person_placements[spouse_index] = replace(
                    spouse,
                    x_start=descendant_x_start,
                    x_start_kind=PositionKind.VISUAL_FALLBACK,
                    x_end=(
                        spouse.x_end
                        if spouse.x_end is not None
                        else descendant_x_start + self.LIFE_SPAN_OFFSET
                    ),
                    x_end_kind=(
                        spouse.x_end_kind
                        if spouse.x_end is not None
                        else PositionKind.VISUAL_FALLBACK
                    ),
                )

            descendant = resolved_person_placements[descendant_index]
            spouse_x_start = own_person_placements[occurrence.spouse_row_index].x_start
            if descendant.x_start is not None or spouse_x_start is None:
                continue

            resolved_person_placements[descendant_index] = replace(
                descendant,
                x_start=spouse_x_start,
                x_start_kind=PositionKind.VISUAL_FALLBACK,
                x_end=(
                    descendant.x_end
                    if descendant.x_end is not None
                    else spouse_x_start + self.LIFE_SPAN_OFFSET
                ),
                x_end_kind=(
                    descendant.x_end_kind
                    if descendant.x_end is not None
                    else PositionKind.VISUAL_FALLBACK
                ),
            )

        for row_index, row in enumerate(model.traversal.rows):
            if row.role is not TraversalRole.ROOT:
                continue
            placement = resolved_person_placements[row_index]
            if placement.x_start is not None:
                continue
            resolved_person_placements[row_index] = replace(
                placement,
                x_start=self.LOGICAL_X_ORIGIN,
                x_start_kind=PositionKind.VISUAL_FALLBACK,
                x_end=(
                    placement.x_end
                    if placement.x_end is not None
                    else self.LOGICAL_X_ORIGIN + self.LIFE_SPAN_OFFSET
                ),
                x_end_kind=(
                    placement.x_end_kind
                    if placement.x_end is not None
                    else PositionKind.VISUAL_FALLBACK
                ),
            )

        # La fratrie propage les positions résolues dans l'ordre des child_refs.
        for family in model.data.families.values():
            previous_x_start = None
            for child_index, child_ref in enumerate(family.child_refs):
                for row_index, row in enumerate(model.traversal.rows):
                    if (
                        row.role is not TraversalRole.DESCENDANT
                        or row.family_id != family.family_id
                        or row.person_id != child_ref.person_id
                    ):
                        continue

                    child = resolved_person_placements[row_index]
                    if child.x_start is None and previous_x_start is None:
                        for next_child_ref in family.child_refs[child_index + 1:]:
                            for next_row_index, next_row in enumerate(model.traversal.rows):
                                if (
                                    next_row.role is not TraversalRole.DESCENDANT
                                    or next_row.family_id != family.family_id
                                    or next_row.person_id != next_child_ref.person_id
                                ):
                                    continue
                                next_x_start = resolved_person_placements[next_row_index].x_start
                                if next_x_start is not None:
                                    previous_x_start = next_x_start
                                    break
                            if previous_x_start is not None:
                                break

                    if child.x_start is not None:
                        previous_x_start = child.x_start
                    elif previous_x_start is not None:
                        resolved_person_placements[row_index] = replace(
                            child,
                            x_start=previous_x_start,
                            x_start_kind=PositionKind.VISUAL_FALLBACK,
                            x_end=(
                                child.x_end
                                if child.x_end is not None
                                else previous_x_start + self.LIFE_SPAN_OFFSET
                            ),
                            x_end_kind=(
                                child.x_end_kind
                                if child.x_end is not None
                                else PositionKind.VISUAL_FALLBACK
                            ),
                        )

        for row_index, row in enumerate(model.traversal.rows):
            if row.role is not TraversalRole.DESCENDANT:
                continue
            placement = resolved_person_placements[row_index]
            if placement.x_start is not None or row.family_id is None:
                continue

            marriage_target = TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id=row.family_id,
                semantic=TargetSemantic.MARRIAGE,
            )
            marriage_result = model.temporal_results.get(marriage_target)
            if marriage_result is None:
                continue
            display_value = determine_display_value(marriage_result)
            if display_value is None:
                continue

            marriage_x = scale.date_to_x(display_value)
            resolved_person_placements[row_index] = replace(
                placement,
                x_start=marriage_x,
                x_start_kind=PositionKind.VISUAL_FALLBACK,
                x_end=(
                    placement.x_end
                    if placement.x_end is not None
                    else marriage_x + self.LIFE_SPAN_OFFSET
                ),
                x_end_kind=(
                    placement.x_end_kind
                    if placement.x_end is not None
                    else PositionKind.VISUAL_FALLBACK
                ),
            )

        for row_index, row in enumerate(model.traversal.rows):
            if row.role is not TraversalRole.DESCENDANT:
                continue
            placement = resolved_person_placements[row_index]
            if placement.x_start is not None or row.family_id is None:
                continue

            parent_occurrence = next(
                (
                    occurrence
                    for occurrence in model.traversal.family_occurrences
                    if occurrence.family_id == row.family_id
                    and occurrence.state is FamilyTraversalState.EXPLORED
                ),
                None,
            )
            if parent_occurrence is None:
                continue
            parent_x_starts = [
                resolved_person_placements[
                    parent_occurrence.descendant_row_index
                ].x_start
            ]
            if parent_occurrence.spouse_row_index is not None:
                parent_x_starts.append(
                    resolved_person_placements[
                        parent_occurrence.spouse_row_index
                    ].x_start
                )
            parent_x_starts = [x for x in parent_x_starts if x is not None]
            if not parent_x_starts:
                continue

            parent_x_start = max(parent_x_starts)
            child_x_start = parent_x_start + self.VISUAL_OFFSET
            resolved_person_placements[row_index] = replace(
                placement,
                x_start=child_x_start,
                x_start_kind=PositionKind.VISUAL_FALLBACK,
                x_end=(
                    placement.x_end
                    if placement.x_end is not None
                    else child_x_start + self.LIFE_SPAN_OFFSET
                ),
                x_end_kind=(
                    placement.x_end_kind
                    if placement.x_end is not None
                    else PositionKind.VISUAL_FALLBACK
                ),
            )

        for row_index, placement in enumerate(resolved_person_placements):
            if (
                placement.x_start is not None
                and placement.x_end is not None
                and placement.x_start > placement.x_end
                and placement.x_start_kind is not PositionKind.VISUAL_FALLBACK
                and placement.x_end_kind is not PositionKind.VISUAL_FALLBACK
            ):
                resolved_person_placements[row_index] = replace(
                    placement,
                    life_bar_kind=LifeBarKind.REVERSED,
                    short_bar_length=self.LIFE_SPAN_OFFSET / 2,
                )
            elif (
                placement.x_start is not None
                and placement.x_end is not None
                and placement.x_start == placement.x_end
                and placement.x_start_kind is not PositionKind.VISUAL_FALLBACK
                and placement.x_end_kind is not PositionKind.VISUAL_FALLBACK
            ):
                resolved_person_placements[row_index] = replace(
                    placement,
                    life_bar_kind=LifeBarKind.ZERO_LENGTH,
                    short_bar_length=self.LIFE_SPAN_OFFSET / 2,
                )

        person_placements = tuple(resolved_person_placements)

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
            if marriage_result is None:
                continue
            display_value = determine_display_value(marriage_result)
            if display_value is None:
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
                        display_value
                    ),
                    y=(descendant_y + spouse_y) / 2.0,
                )
            )

        remarriage_segment_placements = []
        married_family_ids_by_person = {}
        for marriage in marriage_node_placements:
            person_id = marriage.descendant_person_id
            family_ids = married_family_ids_by_person.setdefault(person_id, set())
            if marriage.family_id in family_ids:
                continue
            if family_ids:
                person_y = person_placements[marriage.descendant_row_index].y
                remarriage_segment_placements.append(
                    RemarriageSegmentPlacement(
                        person_id=person_id,
                        x=marriage.x,
                        y_start=min(person_y, marriage.y),
                        y_end=max(person_y, marriage.y),
                    )
                )
            family_ids.add(marriage.family_id)

        return TimelineLayout(
            person_placements=person_placements,
            marriage_node_placements=tuple(marriage_node_placements),
            remarriage_segment_placements=tuple(remarriage_segment_placements),
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
        x_start_kind = PositionKind.REPRESENTATIVE

        if birth_result is not None:
            display_value = determine_display_value(birth_result)
            if display_value is not None:
                x_start = scale.date_to_x(display_value)
                if isinstance(birth_result.estimate.representative_value, date):
                    x_start_kind = PositionKind.REPRESENTATIVE
                else:
                    x_start_kind = PositionKind.DOMAIN_DISPLAY
        x_end = None
        x_end_kind = PositionKind.REPRESENTATIVE

        if death_result is not None:
            display_value = determine_display_value(death_result)
            if display_value is not None:
                x_end = scale.date_to_x(display_value)
                if isinstance(death_result.estimate.representative_value, date):
                    x_end_kind = PositionKind.REPRESENTATIVE
                else:
                    x_end_kind = PositionKind.DOMAIN_DISPLAY

        if x_end is None and x_start is not None:
            x_end = x_start + self.LIFE_SPAN_OFFSET
            x_end_kind = PositionKind.VISUAL_FALLBACK

        return PersonPlacement(
            person_id=row.person_id,
            row_index=row_index,
            generation=row.generation,
            role=row.role,
            family_id=row.family_id,
            spouse_of_person_id=row.spouse_of_person_id,
            x_start=x_start,
            x_start_kind=x_start_kind,
            x_end=x_end,
            x_end_kind=x_end_kind,
            y=(
                self.DEFAULT_TOP_MARGIN
                + row_index * self.DEFAULT_ROW_HEIGHT
            ),
        )
