"""Placement logique d'une personne dans la timeline."""

from __future__ import annotations

from dataclasses import dataclass

from descendants_timeline.layout.life_bar_kind import LifeBarKind
from descendants_timeline.layout.position_kind import PositionKind
from descendants_timeline.traversal.descendance_traversal import (
    TraversalRole,
)


@dataclass(frozen=True, slots=True)
class PersonPlacement:
    """Position logique d'une occurrence de personne dans la timeline."""

    person_id: str
    row_index: int
    generation: int
    role: TraversalRole
    family_id: str | None
    spouse_of_person_id: str | None
    x_start: float | None
    x_end: float | None
    y: float
    visual_rank: int | None = None
    x_start_kind: PositionKind = PositionKind.REPRESENTATIVE
    x_end_kind: PositionKind = PositionKind.REPRESENTATIVE
    life_bar_kind: LifeBarKind = LifeBarKind.NORMAL
    short_bar_length: float | None = None

    @property
    def bar_x_start(self) -> float | None:
        return self.x_start

    @property
    def bar_x_end(self) -> float | None:
        if (
            self.life_bar_kind in (
                LifeBarKind.REVERSED,
                LifeBarKind.ZERO_LENGTH,
            )
            and self.x_start is not None
            and self.short_bar_length is not None
        ):
            return self.x_start + self.short_bar_length
        return self.x_end

    def __post_init__(self) -> None:
        if self.visual_rank is None:
            object.__setattr__(self, "visual_rank", self.row_index)

        if not isinstance(self.person_id, str) or not self.person_id:
            raise ValueError(
                "person_id must be a non-empty string"
            )

        if not isinstance(self.row_index, int) or self.row_index < 0:
            raise ValueError(
                "row_index must be a non-negative integer"
            )

        if not isinstance(self.generation, int) or self.generation < 1:
            raise ValueError(
                "generation must be a positive integer"
            )

        if not isinstance(self.role, TraversalRole):
            raise TypeError(
                "role must be a TraversalRole"
            )

        if self.family_id is not None and (
            not isinstance(self.family_id, str) or not self.family_id
        ):
            raise ValueError(
                "family_id must be None or a non-empty string"
            )

        if self.spouse_of_person_id is not None and (
            not isinstance(self.spouse_of_person_id, str)
            or not self.spouse_of_person_id
        ):
            raise ValueError(
                "spouse_of_person_id must be None or a non-empty string"
            )

        if self.x_start is not None and not isinstance(
            self.x_start, (int, float)
        ):
            raise TypeError(
                "x_start must be None or a number"
            )

        if not isinstance(self.x_start_kind, PositionKind):
            raise TypeError(
                "x_start_kind must be a PositionKind"
            )

        if self.x_end is not None and not isinstance(
            self.x_end, (int, float)
        ):
            raise TypeError(
                "x_end must be None or a number"
            )

        if not isinstance(self.x_end_kind, PositionKind):
            raise TypeError(
                "x_end_kind must be a PositionKind"
            )

        if not isinstance(self.y, (int, float)):
            raise TypeError(
                "y must be a number"
            )
        if not isinstance(self.life_bar_kind, LifeBarKind):
            raise TypeError(
                "life_bar_kind must be a LifeBarKind"
            )
