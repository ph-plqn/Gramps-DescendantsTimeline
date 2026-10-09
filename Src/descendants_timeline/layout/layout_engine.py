"""Moteur de calcul du layout logique de la timeline."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from descendants_timeline.layout.branch_reference_placement import (
    BranchReferencePlacement,
)
from descendants_timeline.layout.diagnostic_placement import DiagnosticPlacement
from descendants_timeline.layout.divorce_node_placement import (
    DivorceNodePlacement,
)
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
    # Décalage graphique provisoire en coordonnées logiques, sans sens temporel.
    DIVORCE_DIAGNOSTIC_OFFSET = 30.0
    # Origine géométrique sur l'axe X, sans signification temporelle.
    LOGICAL_X_ORIGIN = 0.0

    def build(self, model: TimelineModel) -> TimelineLayout:
        scale = TimelineScale()
        reference_spouse_row_indices = tuple(
            occurrence.spouse_row_index
            for occurrence in model.traversal.family_occurrences
            if occurrence.state is FamilyTraversalState.ALREADY_DESCRIBED
            and occurrence.spouse_row_index is not None
        )

        person_placements = tuple(
            self._build_person_placement(
                model=model,
                scale=scale,
                row=row,
                row_index=row_index,
                visual_rank=row_index + sum(
                    spouse_row_index < row_index
                    for spouse_row_index in reference_spouse_row_indices
                ),
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

        divorce_node_placements = []
        for occurrence in model.traversal.family_occurrences:
            if (
                occurrence.descendant_person_id is None
                or occurrence.descendant_row_index is None
                or occurrence.spouse_person_id is None
                or occurrence.spouse_row_index is None
            ):
                continue

            divorce_target = TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id=occurrence.family_id,
                semantic=TargetSemantic.DIVORCE,
            )
            divorce_result = model.temporal_results.get(divorce_target)
            if divorce_result is None:
                continue
            display_value = determine_display_value(divorce_result)
            if display_value is None:
                continue

            descendant_y = person_placements[occurrence.descendant_row_index].y
            spouse_y = person_placements[occurrence.spouse_row_index].y
            divorce_node_placements.append(
                DivorceNodePlacement(
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

        diagnostic_placements = []
        for placement in person_placements:
            if placement.x_start is None:
                continue
            birth_target = TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id=placement.person_id,
                semantic=TargetSemantic.BIRTH,
            )
            birth_result = model.temporal_results.get(birth_target)
            if (
                birth_result is not None
                and (
                    birth_result.constraint_resolution.conflict_type is not None
                    or birth_result.reconciled_domain.conflict_type is not None
                    or bool(birth_result.target_entry.anomalies)
                )
            ):
                diagnostic_placements.append(
                    DiagnosticPlacement(
                        target=birth_target,
                        x=placement.x_start,
                        y=placement.y,
                    )
                )

        for placement in person_placements:
            if placement.bar_x_end is None:
                continue
            death_target = TemporalTarget(
                owner_type=TemporalOwnerType.PERSON,
                owner_id=placement.person_id,
                semantic=TargetSemantic.DEATH,
            )
            death_result = model.temporal_results.get(death_target)
            if (
                death_result is not None
                and (
                    death_result.constraint_resolution.conflict_type is not None
                    or death_result.reconciled_domain.conflict_type is not None
                    or bool(death_result.target_entry.anomalies)
                )
            ):
                diagnostic_placements.append(
                    DiagnosticPlacement(
                        target=death_target,
                        x=placement.bar_x_end,
                        y=placement.y,
                    )
                )

        for marriage_node in marriage_node_placements:
            marriage_target = TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id=marriage_node.family_id,
                semantic=TargetSemantic.MARRIAGE,
            )
            marriage_result = model.temporal_results.get(marriage_target)
            if (
                marriage_result is not None
                and (
                    marriage_result.constraint_resolution.conflict_type is not None
                    or marriage_result.reconciled_domain.conflict_type is not None
                    or bool(marriage_result.target_entry.anomalies)
                )
            ):
                diagnostic_placements.append(
                    DiagnosticPlacement(
                        target=marriage_target,
                        x=marriage_node.x,
                        y=marriage_node.y,
                    )
                )

        for divorce_node in divorce_node_placements:
            divorce_target = TemporalTarget(
                owner_type=TemporalOwnerType.FAMILY,
                owner_id=divorce_node.family_id,
                semantic=TargetSemantic.DIVORCE,
            )
            divorce_result = model.temporal_results.get(divorce_target)
            if (
                divorce_result is not None
                and (
                    divorce_result.constraint_resolution.conflict_type is not None
                    or divorce_result.reconciled_domain.conflict_type is not None
                    or bool(divorce_result.target_entry.anomalies)
                )
            ):
                diagnostic_placements.append(
                    DiagnosticPlacement(
                        target=divorce_target,
                        x=divorce_node.x,
                        y=divorce_node.y,
                    )
                )

        marriage_node_occurrences = {
            (node.family_id, node.descendant_row_index, node.spouse_row_index)
            for node in marriage_node_placements
        }
        divorce_node_occurrences = {
            (node.family_id, node.descendant_row_index, node.spouse_row_index)
            for node in divorce_node_placements
        }
        for occurrence in model.traversal.family_occurrences:
            if (
                occurrence.descendant_person_id is None
                or occurrence.descendant_row_index is None
                or occurrence.spouse_person_id is None
                or occurrence.spouse_row_index is None
            ):
                continue
            occurrence_key = (
                occurrence.family_id,
                occurrence.descendant_row_index,
                occurrence.spouse_row_index,
            )
            diagnostic_targets = []
            for semantic, node_occurrences, offset in (
                (TargetSemantic.MARRIAGE, marriage_node_occurrences, 0.0),
                (
                    TargetSemantic.DIVORCE,
                    divorce_node_occurrences,
                    self.DIVORCE_DIAGNOSTIC_OFFSET,
                ),
            ):
                if occurrence_key in node_occurrences:
                    continue
                target = TemporalTarget(
                    owner_type=TemporalOwnerType.FAMILY,
                    owner_id=occurrence.family_id,
                    semantic=semantic,
                )
                result = model.temporal_results.get(target)
                if result is not None and (
                    result.constraint_resolution.conflict_type is not None
                    or result.reconciled_domain.conflict_type is not None
                    or bool(result.target_entry.anomalies)
                ):
                    diagnostic_targets.append((target, offset))
            if not diagnostic_targets:
                continue
            descendant = person_placements[occurrence.descendant_row_index]
            spouse = person_placements[occurrence.spouse_row_index]
            descendant_complete = (
                descendant.bar_x_start is not None
                and descendant.bar_x_end is not None
            )
            spouse_complete = (
                spouse.bar_x_start is not None
                and spouse.bar_x_end is not None
            )
            if descendant_complete and spouse_complete:
                shared_start = max(descendant.bar_x_start, spouse.bar_x_start)
                shared_end = min(descendant.bar_x_end, spouse.bar_x_end)
                diagnostic_x = (
                    (shared_start + shared_end) / 2
                    if shared_start <= shared_end
                    else (descendant.bar_x_start + descendant.bar_x_end) / 2
                )
            elif descendant_complete:
                diagnostic_x = (descendant.bar_x_start + descendant.bar_x_end) / 2
            elif spouse_complete:
                diagnostic_x = (spouse.bar_x_start + spouse.bar_x_end) / 2
            else:
                continue
            family_ids = model.data.persons[occurrence.descendant_person_id].family_ids
            diagnostic_y = (
                (descendant.y + spouse.y) / 2
                if occurrence.family_id == family_ids[0]
                else descendant.y
            )
            for target, offset in diagnostic_targets:
                diagnostic_placements.append(
                    DiagnosticPlacement(
                        target=target,
                        x=diagnostic_x + offset,
                        y=diagnostic_y,
                    )
                )

        branch_reference_placements = []
        for occurrence in model.traversal.family_occurrences:
            if (
                occurrence.state is not FamilyTraversalState.ALREADY_DESCRIBED
                or occurrence.spouse_row_index is None
            ):
                continue
            descendant_placement = person_placements[occurrence.descendant_row_index]
            spouse_placement = person_placements[occurrence.spouse_row_index]
            descendant_start = descendant_placement.bar_x_start
            descendant_end = descendant_placement.bar_x_end
            spouse_start = spouse_placement.bar_x_start
            spouse_end = spouse_placement.bar_x_end
            x = None
            if (
                descendant_start is not None
                and descendant_end is not None
                and spouse_start is not None
                and spouse_end is not None
            ):
                x = (
                    min(descendant_start, spouse_start)
                    + max(descendant_end, spouse_end)
                ) / 2
            visual_rank = spouse_placement.visual_rank + 1
            branch_reference_placements.append(
                BranchReferencePlacement(
                    family_id=occurrence.family_id,
                    descendant_row_index=occurrence.descendant_row_index,
                    spouse_row_index=occurrence.spouse_row_index,
                    referenced_row_index=occurrence.referenced_row_index,
                    visual_rank=visual_rank,
                    y=self.DEFAULT_TOP_MARGIN + visual_rank * self.DEFAULT_ROW_HEIGHT,
                    x=x,
                )
            )

        return TimelineLayout(
            person_placements=person_placements,
            marriage_node_placements=tuple(marriage_node_placements),
            remarriage_segment_placements=tuple(remarriage_segment_placements),
            diagnostic_placements=tuple(diagnostic_placements),
            divorce_node_placements=tuple(divorce_node_placements),
            branch_reference_placements=tuple(branch_reference_placements),
        )

    def _build_person_placement(
        self,
        model: TimelineModel,
        scale: TimelineScale,
        row,
        row_index: int,
        visual_rank: int,
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
            visual_rank=visual_rank,
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
                + visual_rank * self.DEFAULT_ROW_HEIGHT
            ),
        )
