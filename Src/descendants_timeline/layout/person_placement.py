"""Placement logique d'une personne dans la timeline."""

from __future__ import annotations

from dataclasses import dataclass

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

    def __post_init__(self) -> None:
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

        if self.x_end is not None and not isinstance(
            self.x_end, (int, float)
        ):
            raise TypeError(
                "x_end must be None or a number"
            )

        if not isinstance(self.y, (int, float)):
            raise TypeError(
                "y must be a number"
            )